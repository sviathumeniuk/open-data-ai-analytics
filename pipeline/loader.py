import os
import sqlite3
import pandas as pd
from pathlib import Path

SQLITE_DB_PATH = os.environ.get("SQLITE_DB_PATH", "/workspace/data/analytics.db")
TABLE_NAME = os.environ.get("TABLE_NAME", "vat_registry")
CSV_PATH = Path(os.environ.get("CSV_PATH", "/workspace/raw/pdv_actual_28-08-2019.csv"))

COLUMN_MAP = {
    "Назва юридичної особи": "name", "ЄДРПОУ/РНОКПП": "code", "kod_pdv": "code",
    "code": "code", "Дата реєстрації": "dat_reestr", "name": "name",
    "dat_reestr": "dat_reestr", "dat_term": "dat_term", "Дата завершення": "dat_term",
}

def load():
    print(f"Loading data from {CSV_PATH} to SQLite...")
    if not CSV_PATH.exists(): raise FileNotFoundError(f"CSV not found: {CSV_PATH}")

    df = pd.read_csv(CSV_PATH, sep=";", encoding="utf-8", on_bad_lines="skip", dtype=str)
    df = df.rename(columns=COLUMN_MAP)
    required = ["name", "code", "dat_reestr", "dat_term"]
    df = df[required].copy()
    
    df["dat_reestr"] = pd.to_datetime(df["dat_reestr"], format="%d.%m.%Y", errors="coerce")
    df["dat_term"] = pd.to_datetime(df["dat_term"], format="%d.%m.%Y", errors="coerce")

    with sqlite3.connect(SQLITE_DB_PATH) as conn:
        df.to_sql(TABLE_NAME, conn, if_exists="replace", index=False)
    print(f"Loaded {len(df)} records into {TABLE_NAME}")
