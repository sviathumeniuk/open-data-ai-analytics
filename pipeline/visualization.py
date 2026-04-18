import os
import sqlite3
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd

SQLITE_DB_PATH = os.environ.get("SQLITE_DB_PATH", "/workspace/data/analytics.db")
TABLE_NAME = os.environ.get("TABLE_NAME", "vat_registry")
FIG_ROOT = Path(os.environ.get("FIGURES_ROOT", "/workspace/reports/figures"))

def visualize():
    print("Generating visualizations...")
    with sqlite3.connect(SQLITE_DB_PATH) as conn:
        df = pd.read_sql_query(f"SELECT dat_reestr FROM {TABLE_NAME}", conn)
    
    df["dat_reestr"] = pd.to_datetime(df["dat_reestr"], errors="coerce")
    df = df.dropna(subset=["dat_reestr"])
    
    plt.figure(figsize=(10, 4))
    df.groupby(df["dat_reestr"].dt.year).size().plot(kind="bar")
    plt.title("Registrations by Year")
    
    FIG_ROOT.mkdir(parents=True, exist_ok=True)
    plt.savefig(FIG_ROOT / "registrations_by_year.png")
    plt.close()
    print(f"Figures saved to {FIG_ROOT}")
