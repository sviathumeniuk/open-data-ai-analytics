import sqlite3
import pandas as pd
from pathlib import Path
import os
import re

DB_PATH = os.getenv("SQLITE_DB_PATH", "/workspace/data/analytics.db")
CSV_PATH = Path(os.getenv("CSV_PATH", "/workspace/raw/pdv_actual_28-08-2019.csv"))


def _norm_col(col: str) -> str:
    # Normalize for robust matching across different dataset versions.
    # Examples: "ЄДРПОУ/РНОКПП", "kod_pdv", "Код ПДВ".
    col = str(col).replace("\u00a0", " ")
    col = col.strip().strip('"').strip("'")
    col = re.sub(r"\s+", " ", col)
    return col.casefold()


def _build_rename_map(existing_columns: list[str]) -> dict[str, str]:
    by_norm = {_norm_col(c): c for c in existing_columns}

    def pick(*candidates: str) -> str | None:
        for cand in candidates:
            key = _norm_col(cand)
            if key in by_norm:
                return by_norm[key]
        return None

    # Canonical column names expected downstream
    sources: dict[str, tuple[str, ...]] = {
        "name": (
            "name",
            "Назва юридичної особи",
            "Найменування",
        ),
        "code": (
            "code",
            "kod_pdv",
            "код пдв",
            "ЄДРПОУ/РНОКПП",
            "ЄДРПОУ / РНОКПП",
            "ЄДРПОУ",
            "РНОКПП",
        ),
        "dat_reestr": (
            "dat_reestr",
            "Дата реєстрації",
            "Дата реєстрації платником ПДВ",
        ),
        "dat_term": (
            "dat_term",
            "Дата завершення",
            "Дата анулювання реєстрації",
        ),
    }

    rename: dict[str, str] = {}
    for canonical, candidates in sources.items():
        src = pick(*candidates)
        if src and src != canonical:
            rename[src] = canonical
    return rename

def load():
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"CSV not found at {CSV_PATH}. Check Docker COPY or Volume Mount.")
    
    print(f"Loading {CSV_PATH}...")
    df = pd.read_csv(CSV_PATH, sep=";", encoding="utf-8", on_bad_lines="skip", dtype=str)

    df = df.rename(columns=_build_rename_map(list(df.columns)))

    required = ["name", "code", "dat_reestr", "dat_term"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        available = ", ".join(map(str, df.columns))
        raise KeyError(
            f"Missing required columns: {missing}. "
            f"Available columns: [{available}]. "
            "If the dataset schema changed, update the mapping in pipeline/loader.py."
        )

    df = df[required].copy()

    # Normalize common null markers before parsing dates
    for c in ("dat_reestr", "dat_term"):
        df[c] = df[c].replace({"null": pd.NA, "NULL": pd.NA, "": pd.NA, " ": pd.NA})
    
    df["dat_reestr"] = pd.to_datetime(df["dat_reestr"], format="%d.%m.%Y", errors="coerce")
    df["dat_term"] = pd.to_datetime(df["dat_term"], format="%d.%m.%Y", errors="coerce")

    with sqlite3.connect(DB_PATH) as conn:
        df.to_sql("vat_registry", conn, if_exists="replace", index=False)
    print("Database loaded successfully.")
