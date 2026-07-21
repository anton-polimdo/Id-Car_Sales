"""
clean_data.py
--------------
Membersihkan SEMUA berkas CSV mentah (*_raw.csv) hasil extract_2023.py
dan menstandardisasi kolom:
    year (int), category (str), brand (str), model (str), cc (str/float),
    fuel (str), cbu_ckd (str), country (str),
    jan..dec (int, unit terjual per bulan), sales_volume (int, total tahunan)

Input  : data/processed/*_raw.csv
Output : data/processed/*_clean.csv  (satu per file _raw.csv)
"""

import glob
import os
import pandas as pd

PROCESSED_DIR = "data/processed"
MONTH_COLS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]


def clean_text_fields(df: pd.DataFrame) -> pd.DataFrame:
    text_cols = ["category", "brand", "model", "fuel", "cbu_ckd", "country"]
    for col in text_cols:
        if col in df.columns:
            df[col] = (
                df[col]
                .astype(str)
                .str.replace(r"\s+", " ", regex=True)
                .str.strip()
            )
            df.loc[df[col].isin(["nan", "None", ""]), col] = pd.NA
    return df


def clean_cc_field(df: pd.DataFrame) -> pd.DataFrame:
    if "cc" in df.columns:
        # cc format asli pakai titik sebagai pemisah ribuan, mis. "1.500" = 1500 cc
        df["cc"] = (
            df["cc"]
            .astype(str)
            .str.replace(".", "", regex=False)
            .replace({"-": None, "nan": None})
        )
        df["cc"] = pd.to_numeric(df["cc"], errors="coerce")
    return df


def clean_numeric_fields(df: pd.DataFrame) -> pd.DataFrame:
    numeric_cols = MONTH_COLS + ["sales_volume", "year"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    return df


def drop_invalid_rows(df: pd.DataFrame) -> pd.DataFrame:
    # Buang baris tanpa brand DAN tanpa model (kemungkinan besar noise parsing)
    df = df.dropna(subset=["brand", "model"], how="all")
    df = df.drop_duplicates()
    return df


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = clean_text_fields(df)
    df = clean_cc_field(df)
    df = clean_numeric_fields(df)
    df = drop_invalid_rows(df)
    return df.reset_index(drop=True)


def main():
    raw_files = sorted(glob.glob(os.path.join(PROCESSED_DIR, "*_raw.csv")))
    if not raw_files:
        raise FileNotFoundError(f"Tidak ditemukan berkas *_raw.csv di: {PROCESSED_DIR}")

    for raw_path in raw_files:
        filename = os.path.basename(raw_path)
        output_path = raw_path.replace("_raw.csv", "_clean.csv")

        print(f"Membersihkan: {filename} ...")
        df = pd.read_csv(raw_path)
        df_clean = clean_dataframe(df)
        df_clean.to_csv(output_path, index=False)
        print(f"  -> Berhasil: {len(df_clean)} baris disimpan ke {output_path}")


if __name__ == "__main__":
    main()
