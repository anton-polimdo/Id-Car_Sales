# Analisis Pasar Otomotif Indonesia: Tren Wholesales GAIKINDO (2023 - 2026)
## Deskripsi Proyek
Proyek ini melakukan analisis mendalam terhadap pergerakan pasar otomotif roda empat di Indonesia berdasarkan data resmi distribusi pabrikan ke dealer (*wholesales*) dari **GAIKINDO** periode tahun 2023 hingga data berjalan 2026. Proyek ini berfokus pada pelacakan tren transisi energi dari kendaraan konvensional (ICE) menuju era elektrifikasi (Hybrid & BEV), serta dinamika kompetisi antar-pabrikan global di pasar domestik.
## 🛠️ Tech Stack & Alat yang Digunakan
- **Bahasa Pemrograman:** Python 3.11
- **Pustaka Data:** `pandas`, `numpy`, `pdfplumber` (Data Scraping & Cleaning)
- **Visualisasi & Dashboard:** Tableau Desktop / Power BI (Bisa disesuaikan)
- **Dokumentasi:** Markdown
## 📁 Struktur Repositori
```text
├── data/
│   ├── raw/                # Berkas PDF asli tahunan dari GAIKINDO
│   └── processed/          # Berkas CSV bersih hasil pembersihan awal
├── scripts/
│   ├── extract_2023.py     # Skrip ekstraksi PDF ke DataFrame
│   ├── clean_data.py       # Skrip pembersihan karakter eror dan standardisasi
│   └── consolidate.py      # Skrip penggabungan data multi-tahun (Master)
├── dashboard/
│   └── gaikindo_dashboard.twbx # Berkas hasil rancangan dashboard interaktif
└── README.md               # Dokumentasi utama proyek
```

## 📊 Rancangan Arsitektur Tabel (Data Schema)
Data akhir dikonsolidasikan ke dalam format *Tidy Data* (Long Format) dengan struktur berikut:
- `year` (int): Tahun distribusi (2023 - 2026)
- `month` (str): Bulan distribusi format 3 huruf (`jan`, `feb`, dst)
- `category` (str): Segmen kendaraan (`SEDAN`, `4X2`, `4X4`, `BUS`, `PICK UP/TRUCK`)
- `brand` (str): Pabrikan otomotif skala besar (`TOYOTA`, `BYD`, `WULING`, dst)
- `model` (str): Nama lengkap varian komersial mobil
- `cc` (int): Kapasitas kubikasi mesin (0 untuk tipe full elektrik/BEV)
- `fuel` (str): Sumber energi (`G` = Bensin, `D` = Diesel, `HYBRID`, `BEV`, `PHEV`)
- `assembly` (str): Status manufaktur lokasi rakit (`CKD INA`, `CBU Japan`, dst)
- `sales_volume` (int): Total volume unit terdistribusi bulanan (Mendukung angka negatif untuk retur pembatalan order)

## 💡 Temuan Utama (Key Insights)
*(Bagian ini akan diperbarui secara otomatis setelah kalkulasi statistik deskriptif dijalankan di langkah berikutnya)*
