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
CSV_PATH = Path(os.environ["CSV_PATH"])

CSV_SEP = ";"
CSV_ENCODING = "utf-8"

COLUMN_MAP = {
    "Назва юридичної особи": "name",
    "ЄДРПОУ/РНОКПП": "code",
    "kod_pdv": "code",
    "code": "code",
    "Дата реєстрації": "dat_reestr",
    "name": "name",
    "dat_reestr": "dat_reestr",
    "dat_term": "dat_term",
    "Дата завершення": "dat_term",
}


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
                print("Database is available")
                return
        except psycopg2.OperationalError:
            print(f"Waiting for database ({attempt}/{retries})...")
            time.sleep(delay_seconds)
    raise RuntimeError("Database is not available after retries")


def read_csv() -> pd.DataFrame:
    if not CSV_PATH.exists():
        raise FileNotFoundError(f"CSV file not found: {CSV_PATH}")

    df = pd.read_csv(
        CSV_PATH,
        sep=CSV_SEP,
        encoding=CSV_ENCODING,
        on_bad_lines="skip",
        dtype=str,
    )

    df = df.rename(columns=COLUMN_MAP)
    required_columns = ["name", "code", "dat_reestr", "dat_term"]
    missing = [column for column in required_columns if column not in df.columns]
    if missing:
        raise ValueError(f"CSV is missing required columns: {missing}")

    df = df[required_columns].copy()
    df["dat_term"] = df["dat_term"].replace({"null": None, "": None})
    df["dat_reestr"] = pd.to_datetime(df["dat_reestr"], format="%d.%m.%Y", errors="coerce")
    df["dat_term"] = pd.to_datetime(df["dat_term"], format="%d.%m.%Y", errors="coerce")

    return df


def load_to_db(df: pd.DataFrame) -> None:
    with psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    ) as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
                    id BIGSERIAL PRIMARY KEY,
                    name TEXT,
                    code TEXT,
                    dat_reestr DATE,
                    dat_term DATE
                );
                """
            )
            cursor.execute(f"TRUNCATE TABLE {TABLE_NAME};")

            rows = [
                (
                    row["name"],
                    row["code"],
                    row["dat_reestr"].date() if pd.notna(row["dat_reestr"]) else None,
                    row["dat_term"].date() if pd.notna(row["dat_term"]) else None,
                )
                for _, row in df.iterrows()
            ]

            execute_values(
                cursor,
                f"""
                INSERT INTO {TABLE_NAME} (name, code, dat_reestr, dat_term)
                VALUES %s
                """,
                rows,
                page_size=5000,
            )

        conn.commit()


def main() -> None:
    wait_for_db()
    dataframe = read_csv()
    load_to_db(dataframe)
    print(f"Loaded {len(dataframe)} records into {TABLE_NAME}")


if __name__ == "__main__":
    main()
