import sqlite3
import pandas as pd
from pathlib import Path
import os

DB_PATH = os.getenv("SQLITE_DB_PATH", "/workspace/data/analytics.db")
CSV_PATH = Path(os.getenv("CSV_PATH", "/workspace/raw/pdv_actual_28-08-2019.csv"))

def load():
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"CSV not found at {CSV_PATH}. Check Docker COPY or Volume Mount.")
    
    print(f"Loading {CSV_PATH}...")
    df = pd.read_csv(CSV_PATH, sep=";", encoding="utf-8", on_bad_lines="skip", dtype=str)
    
    # Видалено зайві мапінги, залишено тільки необхідне
    df = df.rename(columns={
        "Назва юридичної особи": "name", 
        "ЄДРПОУ/РНОКПП": "code",
        "Дата реєстрації": "dat_reestr", 
        "Дата завершення": "dat_term"
    })
    
    cols = ["name", "code", "dat_reestr", "dat_term"]
    df = df[cols].copy()
    
    df["dat_reestr"] = pd.to_datetime(df["dat_reestr"], format="%d.%m.%Y", errors="coerce")
    df["dat_term"] = pd.to_datetime(df["dat_term"], format="%d.%m.%Y", errors="coerce")

    with sqlite3.connect(DB_PATH) as conn:
        df.to_sql("vat_registry", conn, if_exists="replace", index=False)
    print("Database loaded successfully.")
