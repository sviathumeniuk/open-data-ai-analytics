import os
import time
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import psycopg2


DB_HOST = os.environ["DB_HOST"]
DB_PORT = int(os.environ["DB_PORT"])
DB_NAME = os.environ["DB_NAME"]
DB_USER = os.environ["DB_USER"]
DB_PASSWORD = os.environ["DB_PASSWORD"]
TABLE_NAME = os.environ["TABLE_NAME"]
FIGURES_ROOT = Path(os.environ["FIGURES_ROOT"])
ECONOMIC_EVENT_YEAR = int(os.environ["ECONOMIC_EVENT_YEAR"])
Y_LABEL = "Кількість"


def wait_for_db(retries: int = 30, delay_seconds: int = 2) -> None:
    for attempt in range(1, retries + 1):
        try:
            with psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
            ):
                return
        except psycopg2.OperationalError:
            print(f"Waiting for database ({attempt}/{retries})...")
            time.sleep(delay_seconds)
    raise RuntimeError("Database is not available after retries")


def fetch_dataframe() -> pd.DataFrame:
    with psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    ) as conn:
        df = pd.read_sql_query(
            f"SELECT name, dat_reestr, dat_term FROM {TABLE_NAME}",
            conn,
        )

    df["dat_reestr"] = pd.to_datetime(df["dat_reestr"], errors="coerce")
    return df.dropna(subset=["dat_reestr"]).copy()


def save_plot(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path, dpi=200)
    plt.close()


def plot_registrations_by_year(df: pd.DataFrame) -> None:
    registrations = df.groupby(df["dat_reestr"].dt.year).size()
    plt.figure(figsize=(10, 4))
    registrations.plot(kind="bar", color="steelblue")
    plt.title("Кількість реєстрацій за роками")
    plt.xlabel("Рік")
    plt.ylabel(Y_LABEL)
    save_plot(FIGURES_ROOT / "eda" / "registrations_by_year.png")


def plot_seasonality(df: pd.DataFrame) -> None:
    monthly = df.groupby(df["dat_reestr"].dt.month).size().reindex(range(1, 13), fill_value=0)
    plt.figure(figsize=(10, 4))
    monthly.plot(kind="bar", color="coral")
    plt.title("Сезонність реєстрацій за місяцями")
    plt.xlabel("Місяць")
    plt.ylabel(Y_LABEL)
    save_plot(FIGURES_ROOT / "hypothesis_1" / "hypothesis_1_seasonality.png")


def plot_economic_periods(df: pd.DataFrame) -> None:
    yearly = df.groupby(df["dat_reestr"].dt.year).size()
    colors = ["steelblue" if year < ECONOMIC_EVENT_YEAR else "orange" for year in yearly.index]
    plt.figure(figsize=(10, 4))
    yearly.plot(kind="bar", color=colors)
    plt.title("Періоди до/після економічних подій")
    plt.xlabel("Рік")
    plt.ylabel(Y_LABEL)
    save_plot(FIGURES_ROOT / "hypothesis_3" / "hypothesis_3_economic_impact.png")


def main() -> None:
    wait_for_db()
    dataframe = fetch_dataframe()
    plot_registrations_by_year(dataframe)
    plot_seasonality(dataframe)
    plot_economic_periods(dataframe)
    print(f"Saved figures to {FIGURES_ROOT}")


if __name__ == "__main__":
    main()
