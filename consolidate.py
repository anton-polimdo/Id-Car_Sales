"""
consolidate.py
----------------
Menggabungkan seluruh berkas CSV bersih (*_clean.csv, multi-tahun) menjadi
satu berkas master siap pakai untuk dashboard.

Input  : data/processed/*_clean.csv
Output : data/processed/gaikindo_master.csv
"""

import glob
import os
import pandas as pd

CLEAN_FILES_PATTERN = "data/processed/*_clean.csv"
OUTPUT_MASTER_PATH = "data/processed/gaikindo_master.csv"


def consolidate_all_years(pattern: str) -> pd.DataFrame:
    files = sorted(glob.glob(pattern))
    if not files:
        raise FileNotFoundError(f"Tidak ditemukan berkas yang cocok dengan pola: {pattern}")

    dataframes = [pd.read_csv(f) for f in files]
    master_df = pd.concat(dataframes, ignore_index=True)
    sort_cols = [c for c in ["year", "category", "brand"] if c in master_df.columns]
    if sort_cols:
        master_df = master_df.sort_values(by=sort_cols).reset_index(drop=True)
    return master_df


def main():
    master_df = consolidate_all_years(CLEAN_FILES_PATTERN)
    master_df.to_csv(OUTPUT_MASTER_PATH, index=False)
    print(f"Berhasil menggabungkan {len(master_df)} baris data ke: {OUTPUT_MASTER_PATH}")


if __name__ == "__main__":
    main()
