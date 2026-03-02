from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd
from src.config import ANALYSIS_START_YEAR, ECONOMIC_EVENT_YEAR

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = (PROJECT_ROOT / "reports" / "figures").resolve()

def _ensure_output_dir() -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    return OUTPUT_DIR


def plot_registrations_by_year(registrations_by_year: pd.Series) -> None:
    plt.figure(figsize=(10, 4))
    registrations_by_year.plot(kind="bar", color="steelblue")
    plt.title("Кiлькiсть реєстрацiй за роками")
    plt.xlabel("Рiк")
    plt.ylabel("Кiлькiсть")
    plt.tight_layout()
    plt.savefig(_ensure_output_dir() / "eda" / "registrations_by_year.png", dpi=300)
    plt.show()


def plot_seasonality(results: dict) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    results["registrations_by_month"].plot(kind="bar", ax=axes[0], color="steelblue")
    axes[0].set_title("Розподіл реєстрацій за місяцями")
    axes[0].set_xlabel("Місяць")
    axes[0].set_ylabel("Кількість реєстрацій")
    axes[0].set_xticklabels(range(1, 13))
    axes[0].grid(True, alpha=0.3, axis="y")

    results["registrations_by_quarter"].plot(kind="bar", ax=axes[1], color="coral")
    axes[1].set_title("Розподіл реєстрацій за кварталами")
    axes[1].set_xlabel("Квартал")
    axes[1].set_ylabel("Кількість реєстрацій")
    axes[1].set_xticklabels(range(1, 5))
    axes[1].grid(True, alpha=0.3, axis="y")

    plt.tight_layout()
    plt.savefig(_ensure_output_dir() / "hypothesis_1" / "hypothesis_1_seasonality.png", dpi=300)
    plt.show()


def plot_legal_forms(results: dict) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    results["forms_by_year"].plot(ax=axes[0], marker="o")
    axes[0].set_title("Динаміка популярності форм за роками")
    axes[0].set_xlabel("Рік")
    axes[0].set_ylabel("Кількість реєстрацій")
    axes[0].legend(title="Форма", loc="best")
    axes[0].grid(True, alpha=0.3)

    periods = ["До 2010", "Від 2010"]
    pp_values = [results["pp_before"], results["pp_after"]]
    tov_values = [results["tov_before"], results["tov_after"]]

    x = range(len(periods))
    width = 0.35

    axes[1].bar([i - width/2 for i in x], pp_values, width, label="ПП", color="steelblue")
    axes[1].bar([i + width/2 for i in x], tov_values, width, label="ТОВ", color="coral")
    axes[1].set_title("Популярність ПП vs ТОВ до/від 2010")
    axes[1].set_ylabel("Кількість реєстрацій")
    axes[1].set_xticks(x)
    axes[1].set_xticklabels(periods)
    axes[1].legend()
    axes[1].grid(True, alpha=0.3, axis="y")

    plt.tight_layout()
    plt.savefig(_ensure_output_dir() / "hypothesis_2" / "hypothesis_2_legal_forms.png", dpi=300)
    plt.show()


def plot_economic_impact(results: dict) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    years_list = results["registrations_per_year"].index.tolist()
    colors_bars = [
        'steelblue' if ANALYSIS_START_YEAR <= year < ECONOMIC_EVENT_YEAR
        else 'coral' if year >= ECONOMIC_EVENT_YEAR
        else 'darkgray'
        for year in years_list
    ]

    results["registrations_per_year"].plot(kind="bar", ax=axes[0], color=colors_bars)

    if ECONOMIC_EVENT_YEAR in years_list:
        idx_event = years_list.index(ECONOMIC_EVENT_YEAR)
        axes[0].axvline(x=idx_event, color="black", linestyle="--", linewidth=2)

    axes[0].set_title("Динаміка реєстрацій з виділенням періодів")
    axes[0].set_xlabel("Рік")
    axes[0].set_ylabel("Кількість реєстрацій")
    axes[0].grid(True, alpha=0.3, axis="y")

    periods = [results['before_event']['period'], results['after_event']['period']]
    averages = [
        results['before_event']['avg_per_year'],
        results['after_event']['avg_per_year']
    ]
    colors = ["steelblue", "coral"]

    axes[1].bar(periods, averages, color=colors, edgecolor="black")
    axes[1].set_title("Середня кількість реєстрацій на рік")
    axes[1].set_ylabel("Кількість реєстрацій")
    axes[1].grid(True, alpha=0.3, axis="y")

    for i, v in enumerate(averages):
        axes[1].text(i, v + v*0.02, f"{v:,.0f}", ha="center", va="bottom", fontweight="bold")

    plt.tight_layout()
    plt.savefig(_ensure_output_dir() / "hypothesis_3" / "hypothesis_3_economic_impact.png", dpi=300)
    plt.show()
