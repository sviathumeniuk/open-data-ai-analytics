import json
import os
import time
from pathlib import Path

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values


DB_HOST = os.environ["DB_HOST"]
DB_PORT = int(os.environ["DB_PORT"])
DB_NAME = os.environ["DB_NAME"]
DB_USER = os.environ["DB_USER"]
DB_PASSWORD = os.environ["DB_PASSWORD"]
TABLE_NAME = os.environ["TABLE_NAME"]
REPORT_PATH = Path(os.environ["QUALITY_REPORT_PATH"])


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
        return pd.read_sql_query(
            f"SELECT id, name, code, dat_reestr, dat_term FROM {TABLE_NAME}",
            conn,
        )


def calculate_metrics(df: pd.DataFrame) -> dict:
    code_series = df["code"].fillna("").astype(str).str.strip()
    duplicate_rows = int(code_series[code_series != ""].duplicated(keep=False).sum())

    return {
        "total_rows": int(len(df)),
        "missing_name": int(df["name"].isna().sum()),
        "missing_code": int(df["code"].isna().sum()),
        "missing_registration_date": int(df["dat_reestr"].isna().sum()),
        "missing_termination_date": int(df["dat_term"].isna().sum()),
        "duplicate_code_rows": duplicate_rows,
        "active_records": int(df["dat_term"].isna().sum()),
    }


def persist_results(metrics: dict) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")

    with psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    ) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS data_quality_metrics (
                    id BIGSERIAL PRIMARY KEY,
                    metric TEXT NOT NULL,
                    value DOUBLE PRECISION,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
                """
            )
            cursor.execute("TRUNCATE TABLE data_quality_metrics;")

            rows = [(key, float(value)) for key, value in metrics.items()]
            execute_values(
                cursor,
                "INSERT INTO data_quality_metrics (metric, value) VALUES %s",
                rows,
            )

        conn.commit()


def main() -> None:
    wait_for_db()
    dataframe = fetch_dataframe()
    metrics = calculate_metrics(dataframe)
    persist_results(metrics)
    print(f"Saved data quality metrics to DB and {REPORT_PATH}")


if __name__ == "__main__":
    main()
