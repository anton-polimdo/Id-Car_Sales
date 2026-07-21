# Id-Car_Sales — GAIKINDO Data Pipeline & Dashboard

Proyek ini mengekstraksi, membersihkan, dan menggabungkan data penjualan
wholesales kendaraan bermotor Indonesia dari laporan resmi **GAIKINDO**
(Gabungan Industri Kendaraan Bermotor Indonesia), lalu menyiapkannya untuk
divisualisasikan dalam bentuk dashboard interaktif.

## Struktur Proyek

```
├── data/
│   ├── raw/                # Berkas PDF asli tahunan dari GAIKINDO
│   └── processed/          # Hasil ekstraksi & pembersihan (CSV)
├── scripts/
│   ├── extract_2023.py     # Ekstraksi semua PDF di data/raw/ → CSV mentah
│   ├── clean_data.py       # Pembersihan & standardisasi tipe data
│   └── consolidate.py      # Penggabungan seluruh tahun → satu master file
├── dashboard/
│   └── gaikindo_dashboard.twbx   # Dashboard interaktif (Tableau)
└── README.md
```

## Sumber Data

Berkas PDF "GAIKINDO Wholesales Data" — laporan tahunan hasil export
Excel-ke-PDF yang berisi 7 kategori kendaraan:

| Kategori | Isi |
|---|---|
| `SEDAN` | Mobil sedan |
| `4X2` | Mobil penumpang 4x2 |
| `4X4` | Mobil penumpang 4x4 |
| `BUS` | Bus |
| `PICKUP_TRUCK` | Pick up & truk |
| `DOUBLE_CABIN` | Double cabin |
| `AFFORDABLE_ENERGY` | Mobil hemat energi & terjangkau (LCGC) |

> **Catatan:** Format laporan GAIKINDO berubah sedikit tiap tahun (mis. format
> persentase, brand baru yang muncul di pasar). Jika file tahun berikutnya
> gagal diproses, cek pesan error dari `extract_2023.py` — biasanya perlu
> penyesuaian kecil pada pola regex atau daftar `KNOWN_BRANDS`.

## Alur Kerja (Pipeline)

```
data/raw/*.pdf
      │
      ▼  extract_2023.py  (pdftotext -layout + regex parser)
data/processed/gaikindo_<tahun>_raw.csv
      │
      ▼  clean_data.py  (standardisasi tipe data, buang baris invalid)
data/processed/gaikindo_<tahun>_clean.csv
      │
      ▼  consolidate.py  (gabungkan semua tahun)
data/processed/gaikindo_master.csv
      │
      ▼
dashboard/  (Tableau / alat visualisasi lain)
```

### 1. Ekstraksi (`extract_2023.py`)
Membaca semua PDF di `data/raw/` menggunakan `pdftotext -layout` (dari Poppler)
untuk mempertahankan posisi kolom, lalu memisahkan tiap baris data kendaraan
menjadi kolom-kolom terstruktur menggunakan regex — termasuk memisahkan
BRAND dari MODEL menggunakan daftar brand yang dikenal (`KNOWN_BRANDS`).

### 2. Pembersihan (`clean_data.py`)
Mengonversi tipe data (angka, teks), membersihkan format CC (engine size),
dan membuang baris yang tidak valid (tanpa brand & model).

### 3. Konsolidasi (`consolidate.py`)
Menggabungkan seluruh `*_clean.csv` menjadi satu `gaikindo_master.csv`.

## Skema Data (`gaikindo_master.csv`)

| Kolom | Tipe | Keterangan |
|---|---|---|
| `year` | int | Tahun data |
| `category` | str | Salah satu dari 7 kategori di atas |
| `brand` | str | Merek kendaraan (mis. TOYOTA, HONDA) |
| `model` | str | Nama model/tipe |
| `cc` | float | Kapasitas mesin (cc) |
| `fuel` | str | Jenis bahan bakar (G, D, BEV, HYBRID, PHEV, dst) |
| `cbu_ckd` | str | Status impor (CBU) atau rakitan lokal (CKD) |
| `country` | str | Negara asal |
| `jan` ... `dec` | int | Unit terjual per bulan |
| `sales_volume` | int | Total unit terjual dalam setahun |

## Cara Menjalankan

```bash
# 1. (Opsional) buat virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 2. Install dependensi
pip install pandas pdfplumber

# 3. Pastikan Poppler (pdftotext) terinstall — dibutuhkan oleh extract_2023.py
pdftotext -v   # jika error "command not found", install Poppler dulu

# 4. Letakkan PDF GAIKINDO di data/raw/, lalu jalankan pipeline
python scripts/extract_2023.py
python scripts/clean_data.py
python scripts/consolidate.py
```

Hasil akhir ada di `data/processed/gaikindo_master.csv`.

## Status Proyek

- [x] Ekstraksi PDF multi-tahun (2023–2025)
- [x] Pembersihan & standardisasi data
- [x] Konsolidasi multi-tahun
- [ ] Dashboard interaktif (`dashboard/gaikindo_dashboard.twbx`)
- [ ] Ekstraksi data 2026 (menyusul saat PDF tersedia)

## Lisensi

Tentukan lisensi proyek Anda di sini (mis. MIT License).
