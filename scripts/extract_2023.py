"""
extract_2023.py
----------------
Mengekstraksi SEMUA berkas PDF "GAIKINDO Wholesales Data" di data/raw/
menjadi CSV mentah (satu baris = satu model kendaraan per bulan-tahun tsb).

Format sumber: laporan Excel-to-PDF GAIKINDO yang terdiri dari 7 section
(SEDAN, 4X2, 4X4, BUS, PICK UP/TRUCK, DOUBLE CABIN, AFFORDABLE ENERGY
SAVING CARS), tiap section berisi banyak model dengan kolom spesifikasi
teknis + 12 kolom penjualan bulanan (Jan-Des) + total tahunan.

Karena PDF ini bukan tabel berbingkai biasa (hasil export Excel dengan
banyak cell wrapping/merge), ekstraksi dilakukan dengan:
  1. `pdftotext -layout` untuk mempertahankan posisi kolom sebagai teks
  2. Regex untuk mengenali pola baris data: ... 12 angka bulanan
     + 2 persentase + 1 total (di akhir baris)
  3. Regex untuk mengenali CC + Transmisi + Bahan Bakar (penanda posisi
     tengah baris)
  4. Daftar brand dikenal (KNOWN_BRANDS) untuk memisahkan BRAND dari
     MODEL secara akurat, karena nama trim mobil (mis. "AMG CLA 45 S")
     sering ditulis huruf besar semua sehingga heuristik generik gagal.

Catatan: karena kompleksitas layout asli, brand/model punya akurasi
~97-98% dari uji terhadap data 2023 (sebagian kecil baris kontinuasi
tanpa brand akan mewarisi brand baris sebelumnya). Angka penjualan
bulanan & total diekstraksi dengan keandalan tinggi karena polanya
sangat konsisten di akhir tiap baris.

Input  : data/raw/*.pdf
Output : data/processed/gaikindo_<tahun>_raw.csv
"""

import glob
import os
import re
import subprocess

RAW_DIR = "data/raw"
OUTPUT_DIR = "data/processed"

NUM = r'(?:-|\(\d+\)|\d{1,3}(?:\.\d{3})*)'
# PCT: menerima "8,7%" (format 2023) maupun "10%" / "0%" (format 2024-2025, tanpa koma desimal)
PCT = r'(?:#DIV/0!|\d+(?:,\d)?%)'

TAIL_RE = re.compile(
    r'^(?P<prefix>.*?)\s+(?P<months>(?:' + NUM + r'\s+){11}' + NUM + r')\s+'
    r'(?P<share_brand>' + PCT + r')\s+(?P<share_market>' + PCT + r')\s+(?P<total>' + NUM + r')\s*$'
)
SPEC_RE = re.compile(
    r'(?P<cc>-|\d{1,2}\.\d{3}|\d{3,5})\s+(?P<trans>MT|AT|CVT|M/T|A/T|-)\s+(?P<fuel>G|D|BEV|HYBRID|PHEV|CNG|HEV|-)\s'
)

SECTION_MAP = [
    ("SEDAN TYPE SALES", "SEDAN"),
    ("4 X 2 TYPE SALES", "4X2"),
    ("4X2 TYPE SALES", "4X2"),
    ("4X4 TYPE SALES", "4X4"),
    ("BUS SALES", "BUS"),
    ("PICK UP/TRUCK SALES", "PICKUP_TRUCK"),
    ("DOUBLE CABIN SALES", "DOUBLE_CABIN"),
    ("AFFORDABLE ENERGY SAVING CARS", "AFFORDABLE_ENERGY"),
]

NOISE_WORDS = {
    "CBU", "CKD", "TYPE", "SEDAN", "BUS", "TRUCK", "PICKUP", "PICK", "UP", "GVW",
    "TANK", "CAPT", "DIMENSION", "ORIGIN", "COUNTRY", "MARKET", "SHARE", "TOTAL",
    "AFFORDABLE", "ENERGY", "SAVING", "CARS", "DOUBLE", "CABIN", "FOR", "ALL", "4X2", "4X4",
}

# Daftar brand yang dikenal beroperasi di pasar mobil Indonesia (GAIKINDO members).
# Urutan terpanjang lebih dulu agar brand 2-3 kata (mis. "MERCEDES BENZ PC")
# tercocokkan sebelum brand 1 kata.
KNOWN_BRANDS = sorted([
    "MITSUBISHI MOTORS", "MITSUBISHI FUSO", "MERCEDES BENZ PC", "MERCEDES-BENZ PC",
    "MERCEDES BENZ CV", "MERCEDES-BENZ CV", "MERCEDES BENZ", "MERCEDES-BENZ",
    "HYUNDAI - HMID", "HYUNDAI HMID", "HYUNDAI - HIM", "HYUNDAI HIM", "HYUNDAI",
    "MORRIS GARAGE", "TATA MOTORS", "UD TRUCKS",
    "TOYOTA", "HONDA", "DAIHATSU", "SUZUKI", "NISSAN", "MAZDA", "ISUZU", "HINO", "WULING",
    "KIA", "BMW", "MINI", "AUDI", "VOLKSWAGEN", "LEXUS", "SUBARU", "DFSK", "CHERY",
    "PEUGEOT", "JEEP", "TATA", "SCANIA", "FAW", "NETA", "SERES", "MG",
    # Brand tambahan yang muncul di data 2024-2025 (EV & merek baru)
    "VOLVO CARS", "BYD", "AION", "GWM", "GEELY", "JETOUR", "HAVAL", "CITROEN",
    "FORD", "DENZA", "BAIC", "MAXUS", "POLYTRON", "VINFAST", "XPENG", "JAECOO",
], key=len, reverse=True)

MONTH_COLS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]


def detect_section(upper_line: str):
    for key, val in SECTION_MAP:
        if key.upper() in upper_line:
            return val
    return None


def is_noise(token: str) -> bool:
    core = token.strip().rstrip(".,")
    return core.upper() in NOISE_WORDS or bool(
        re.match(r"^CC\b|^\[G/D\]|^/\s*[\d.]+|^GVW\b", core)
    )


def match_brand(text: str):
    """Cocokkan awal `text` dengan salah satu KNOWN_BRANDS. Return substring brand atau None."""
    up = text.upper()
    for b in KNOWN_BRANDS:
        if up == b or up.startswith(b + " "):
            return text[: len(b)]
    return None


def clean_num(tok: str) -> int:
    tok = tok.strip()
    if tok in ("", "-"):
        return 0
    neg = tok.startswith("(") and tok.endswith(")")
    if neg:
        tok = tok[1:-1]
    tok = tok.replace(".", "")
    try:
        val = int(tok)
    except ValueError:
        return 0
    return -val if neg else val


def extract_year_from_filename(filename: str) -> str:
    match = re.search(r"(20\d{2})", filename)
    return match.group(1) if match else "unknown"


def pdf_to_layout_text(pdf_path: str) -> str:
    """Gunakan pdftotext -layout (poppler-utils) agar posisi kolom terjaga.

    Output ditangkap sebagai bytes lalu didekode manual dengan errors="replace",
    karena sebagian PDF GAIKINDO mengandung byte yang bukan UTF-8 murni
    (biasanya simbol/karakter sisa dari export Excel) yang bisa membuat
    subprocess gagal decode di beberapa environment (khususnya Windows).
    """
    result = subprocess.run(
        ["pdftotext", "-layout", "-enc", "UTF-8", pdf_path, "-"],
        capture_output=True, check=True,
    )
    return result.stdout.decode("utf-8", errors="replace")


def parse_gaikindo_text(text: str, year: str):
    rows = []
    current_section = None
    last_brand = None

    for raw_line in text.splitlines():
        line = raw_line.rstrip("\n")
        stripped = line.strip()
        if not stripped:
            continue
        upper = stripped.upper()

        sec = detect_section(upper)
        if sec:
            current_section = sec
            last_brand = None
            continue

        m = TAIL_RE.match(line)
        if not m:
            continue  # baris header/judul/kosong, bukan baris data

        prefix = m.group("prefix")
        months_raw = m.group("months").split()
        if len(months_raw) != 12:
            continue
        total = clean_num(m.group("total"))

        spec_m = SPEC_RE.search(prefix)
        if not spec_m:
            continue  # tidak ditemukan penanda CC/TRANS/FUEL -> bukan baris model

        before_spec = prefix[: spec_m.start()].strip()
        cc = spec_m.group("cc")
        fuel = spec_m.group("fuel")
        after_spec = prefix[spec_m.end():].strip()

        cbu_ckd_m = re.search(r"\b(CBU|CKD)\b\s+([A-Za-z][A-Za-z .]*)$", after_spec)
        country = cbu_ckd_m.group(2).strip() if cbu_ckd_m else None
        cbu_ckd = cbu_ckd_m.group(1) if cbu_ckd_m else None

        parts = [p for p in re.split(r"\s{2,}", before_spec) if p.strip()]
        while parts and is_noise(parts[0]):
            parts.pop(0)

        brand, model = None, None
        if parts:
            b = match_brand(parts[0])
            if b:
                brand = b
                rest_of_first = parts[0][len(b):].strip()
                model_parts = ([rest_of_first] if rest_of_first else []) + parts[1:]
                model = " ".join(model_parts) if model_parts else None
                last_brand = brand
            else:
                model = " ".join(parts)
                brand = last_brand
        else:
            brand = last_brand

        row = {
            "year": year,
            "category": current_section,
            "brand": brand,
            "model": model,
            "cc": cc,
            "fuel": fuel,
            "cbu_ckd": cbu_ckd,
            "country": country,
        }
        for col, val in zip(MONTH_COLS, months_raw):
            row[col] = clean_num(val)
        row["sales_volume"] = total
        rows.append(row)

    return rows


def main():
    pdf_files = sorted(glob.glob(os.path.join(RAW_DIR, "*.pdf")))
    if not pdf_files:
        raise FileNotFoundError(f"Tidak ditemukan berkas PDF di: {RAW_DIR}")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    import csv

    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        year = extract_year_from_filename(filename)
        output_path = os.path.join(OUTPUT_DIR, f"gaikindo_{year}_raw.csv")

        print(f"Memproses: {filename} (tahun terdeteksi: {year}) ...")
        try:
            text = pdf_to_layout_text(pdf_path)
            rows = parse_gaikindo_text(text, year)
            if not rows:
                print(f"  -> PERINGATAN: tidak ada baris data yang berhasil diparse dari {filename}")
                continue

            fieldnames = ["year", "category", "brand", "model", "cc", "fuel",
                          "cbu_ckd", "country"] + MONTH_COLS + ["sales_volume"]
            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)

            no_brand = sum(1 for r in rows if not r["brand"])
            print(f"  -> Berhasil: {len(rows)} baris disimpan ke {output_path} "
                  f"({no_brand} baris tanpa brand terdeteksi)")
        except subprocess.CalledProcessError as e:
            print(f"  -> GAGAL menjalankan pdftotext untuk {filename}: {e}")
        except Exception as e:
            print(f"  -> GAGAL memproses {filename}: {e}")


if __name__ == "__main__":
    main()
