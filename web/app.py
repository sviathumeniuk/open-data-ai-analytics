import os
from pathlib import Path

import psycopg2
from flask import Flask, render_template, send_from_directory


DB_HOST = os.environ["DB_HOST"]
DB_PORT = int(os.environ["DB_PORT"])
DB_NAME = os.environ["DB_NAME"]
DB_USER = os.environ["DB_USER"]
DB_PASSWORD = os.environ["DB_PASSWORD"]
FIGURES_ROOT = Path(os.environ["FIGURES_ROOT"])

app = Flask(__name__)


def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )


def load_quality_metrics() -> list[dict]:
    query = """
        SELECT metric, value
        FROM data_quality_metrics
        ORDER BY metric
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                return [{"metric": row[0], "value": row[1]} for row in rows]
    except Exception:
        return []


def load_research_results() -> list[dict]:
    query = """
        SELECT result_key, result_value::text
        FROM research_results
        ORDER BY result_key
    """
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()
                return [{"key": row[0], "value": row[1]} for row in rows]
    except Exception:
        return []


def list_figures() -> list[str]:
    if not FIGURES_ROOT.exists():
        return []
    images = [
        str(path.relative_to(FIGURES_ROOT)).replace("\\", "/")
        for path in FIGURES_ROOT.rglob("*")
        if path.is_file() and path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"}
    ]
    return sorted(images)


@app.route("/", methods=["GET"])
def index():
    return render_template(
        "index.html",
        quality_metrics=load_quality_metrics(),
        research_results=load_research_results(),
        figures=list_figures(),
    )


@app.route("/figures/<path:filename>", methods=["GET"])
def figures(filename: str):
    return send_from_directory(FIGURES_ROOT, filename)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
