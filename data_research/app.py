import json
import os
import re
import time
from pathlib import Path

import pandas as pd
import psycopg2
from psycopg2.extras import Json, execute_values


DB_HOST = os.environ["DB_HOST"]
DB_PORT = int(os.environ["DB_PORT"])
DB_NAME = os.environ["DB_NAME"]
DB_USER = os.environ["DB_USER"]
DB_PASSWORD = os.environ["DB_PASSWORD"]
TABLE_NAME = os.environ["TABLE_NAME"]
REPORT_PATH = Path(os.environ["RESEARCH_REPORT_PATH"])
ECONOMIC_EVENT_YEAR = int(os.environ["ECONOMIC_EVENT_YEAR"])


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
            f"SELECT name, code, dat_reestr, dat_term FROM {TABLE_NAME}",
            conn,
        )

    df["dat_reestr"] = pd.to_datetime(df["dat_reestr"], errors="coerce")
    df["dat_term"] = pd.to_datetime(df["dat_term"], errors="coerce")
    return df


def extract_legal_form(name: str) -> str:
    name_upper = str(name or "").upper().replace("I", "І")
    if re.search(r"\bТОВ\b", name_upper) or re.search(r"ТОВАРИСТВО.*ОБМЕЖЕН", name_upper):
        return "ТОВ"
    if re.search(r"\bПП\b", name_upper) or re.search(r"ПРИВАТНЕ.*ПІДПРИЄМСТВО", name_upper):
        return "ПП"
    if re.search(r"\bЗАТ\b", name_upper):
        return "ЗАТ"
    if re.search(r"\bАТ\b", name_upper) or re.search(r"АКЦІОНЕРНЕ", name_upper):
        return "АТ"
    if "ООО" in name_upper:
        return "ООО"
    return "Інше"


def build_summary(df: pd.DataFrame) -> dict:
    clean = df.dropna(subset=["dat_reestr"]).copy()
    clean["year"] = clean["dat_reestr"].dt.year
    clean["month"] = clean["dat_reestr"].dt.month

    registrations_by_year = clean.groupby("year").size().to_dict()
    registrations_by_month = clean.groupby("month").size().to_dict()

    clean["legal_form"] = clean["name"].apply(extract_legal_form)
    forms_by_year = (
        clean.groupby(["year", "legal_form"]).size().unstack(fill_value=0).astype(int)
    )

    before = clean[clean["year"] < ECONOMIC_EVENT_YEAR]
    after = clean[clean["year"] >= ECONOMIC_EVENT_YEAR]

    summary = {
        "registrations_by_year": registrations_by_year,
        "registrations_by_month": registrations_by_month,
        "legal_forms_by_year": {
            str(year): {form: int(value) for form, value in row.items()}
            for year, row in forms_by_year.iterrows()
        },
        "economic_impact": {
            "event_year": ECONOMIC_EVENT_YEAR,
            "before_count": int(len(before)),
            "after_count": int(len(after)),
            "after_vs_before_pct": (
                round(((len(after) - len(before)) / len(before) * 100), 2)
                if len(before) > 0
                else None
            ),
        },
    }

    return summary


def persist_results(summary: dict) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

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
                CREATE TABLE IF NOT EXISTS research_results (
                    id BIGSERIAL PRIMARY KEY,
                    result_key TEXT NOT NULL,
                    result_value JSONB NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
                """
            )
            cursor.execute("TRUNCATE TABLE research_results;")

            rows = [(key, Json(value)) for key, value in summary.items()]
            execute_values(
                cursor,
                "INSERT INTO research_results (result_key, result_value) VALUES %s",
                rows,
            )
        conn.commit()


def main() -> None:
    wait_for_db()
    dataframe = fetch_dataframe()
    summary = build_summary(dataframe)
    persist_results(summary)
    print(f"Saved research results to DB and {REPORT_PATH}")


if __name__ == "__main__":
    main()
