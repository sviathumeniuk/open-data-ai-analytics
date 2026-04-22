import os
import sqlite3
import json
import pandas as pd
from pathlib import Path

SQLITE_DB_PATH = os.environ.get("SQLITE_DB_PATH", "/workspace/data/analytics.db")
TABLE_NAME = os.environ.get("TABLE_NAME", "vat_registry")
REPORT_PATH = Path(os.environ.get("RESEARCH_REPORT_PATH", "/workspace/reports/data_research/summary.json"))
EVENT_YEAR = int(os.environ.get("ECONOMIC_EVENT_YEAR", 2014))

def run_research():
    print("Running research...")
    with sqlite3.connect(SQLITE_DB_PATH) as conn:
        df = pd.read_sql_query(f"SELECT * FROM {TABLE_NAME}", conn)
    
    df["dat_reestr"] = pd.to_datetime(df["dat_reestr"], errors="coerce")
    clean = df.dropna(subset=["dat_reestr"]).copy()
    clean["year"] = clean["dat_reestr"].dt.year

    before = len(clean[clean["year"] < EVENT_YEAR])
    after = len(clean[clean["year"] >= EVENT_YEAR])

    summary = {
        "economic_impact": {
            "before_count": before, "after_count": after,
            "diff_pct": round(((after-before)/before*100), 2) if before > 0 else 0
        }
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    with sqlite3.connect(SQLITE_DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS research_results")
        cursor.execute("CREATE TABLE research_results (result_key TEXT, result_value TEXT)")
        for k, v in summary.items():
            cursor.execute("INSERT INTO research_results VALUES (?, ?)", (k, json.dumps(v)))
    print(f"Research results saved to {REPORT_PATH}")
