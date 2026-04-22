import os
import sqlite3
from flask import Flask, render_template

SQLITE_DB_PATH = os.environ.get("SQLITE_DB_PATH", "data/analytics.db")
TABLE_NAME = os.environ.get("TABLE_NAME", "vat_registry")

app = Flask(__name__)


def get_db():
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def get_dashboard_stats():
    stats = {}
    with get_db() as conn:
        stats['total'] = conn.execute(f"SELECT count(*) FROM {TABLE_NAME}").fetchone()[0]
        
        stats['active'] = conn.execute(f"SELECT count(*) FROM {TABLE_NAME} WHERE dat_term IS NULL").fetchone()[0]
        
        stats['term_rate'] = round(((stats['total'] - stats['active']) / stats['total'] * 100), 1) if stats['total'] > 0 else 0
        
        velocity_query = f"SELECT count(*) FROM {TABLE_NAME} WHERE dat_reestr IS NOT NULL"
        velocity_total = conn.execute(velocity_query).fetchone()[0]
        stats['velocity'] = round(velocity_total / 12, 1) # Спрощено для дашборду
        
    return stats

def get_chart_data():
    chart = {}
    with get_db() as conn:
        timeline = conn.execute(f"""
            SELECT strftime('%Y', dat_reestr) as yr, count(*) as cnt 
            FROM {TABLE_NAME} 
            WHERE dat_reestr IS NOT NULL 
            GROUP BY yr ORDER BY yr
        """).fetchall()
        chart['timeline_labels'] = [r['yr'] for r in timeline]
        chart['timeline_values'] = [r['cnt'] for r in timeline]
        
        bar_data = conn.execute(f"""
            SELECT 
                strftime('%Y', dat_reestr) as yr,
                count(*) as new_cnt,
                sum(case when dat_term is not null then 1 else 0 end) as term_cnt
            FROM {TABLE_NAME}
            WHERE dat_reestr IS NOT NULL
            GROUP BY yr ORDER BY yr DESC LIMIT 10
        """).fetchall()
        
        bar_data = bar_data[::-1]
        chart['bar_labels'] = [r['yr'] for r in bar_data]
        chart['bar_new'] = [r['new_cnt'] for r in bar_data]
        chart['bar_term'] = [r['term_cnt'] for r in bar_data]
        
    return chart

@app.route("/")
def index():
    stats = get_dashboard_stats()
    chart = get_chart_data()
    
    with get_db() as conn:
        data = conn.execute(f"SELECT * FROM {TABLE_NAME} LIMIT 100").fetchall()
    
    return render_template(
        "index.html",
        stats=stats,
        chart=chart,
        data=data
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
