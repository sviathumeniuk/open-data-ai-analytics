import os
import sqlite3
import json
import pandas as pd
from pathlib import Path

SQLITE_DB_PATH = os.environ.get("SQLITE_DB_PATH", "/workspace/data/analytics.db")
TABLE_NAME = os.environ.get("TABLE_NAME", "vat_registry")
REPORT_PATH = Path(os.environ.get("QUALITY_REPORT_PATH", "/workspace/reports/data_quality/latest.json"))

def analyze_quality():
    print("Analyzing data quality...")
    with sqlite3.connect(SQLITE_DB_PATH) as conn:
        df = pd.read_sql_query(f"SELECT * FROM {TABLE_NAME}", conn)

    metrics = {
        "total_rows": int(len(df)),
        "missing_name": int(df["name"].isna().sum()),
        "missing_code": int(df["code"].isna().sum()),
        "duplicate_code_rows": int(df["code"].fillna("").duplicated(keep=False).sum()),
        "active_records": int(df["dat_term"].isna().sum()),
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

    with sqlite3.connect(SQLITE_DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS data_quality_metrics")
        cursor.execute("CREATE TABLE data_quality_metrics (metric TEXT, value REAL)")
        for k, v in metrics.items():
            cursor.execute("INSERT INTO data_quality_metrics VALUES (?, ?)", (k, float(v)))
    print(f"Quality report saved to {REPORT_PATH}")
