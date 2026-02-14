from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
DATA_DIR = PROJECT_DIR / "data" / "raw"
NOTEBOOKS_DIR = PROJECT_DIR / "notebooks"
REPORTS_DIR = PROJECT_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

DATA_FILE = DATA_DIR / "pdv_actual_28-08-2019.csv"

DATA_URL = "https://data.gov.ua/dataset/95d06529-0367-48da-96dd-c6eb9beeedf3/resource/e5af2194-f78d-46df-9de0-7eeb4155c0e6/download/pdv_actual_28-08-2019.csv"
REQUEST_TIMEOUT = 30

CSV_SEP = ";"
CSV_ENCODING = "utf-8"
CSV_ON_BAD_LINES = "skip"

DATE_FORMAT = "%d.%m.%Y"

COLUMNS = {
    "name": "Назва юридичної особи",
    "code": "ЄДРПОУ/РНОКПП",
    "dat_reestr": "Дата реєстрації",
    "dat_term": "Дата завершення",
}

LEGAL_FORMS = {
    "ТОВ": "Товариство з обмеженою відповідальністю",
    "ПП": "Приватне підприємство",
    "ЗАТ": "Закрите акціонерне товариство",
    "АТ": "Акціонерне товариство",
    "ООО": "Обмежене господарське об'єднання",
}

ANALYSIS_START_YEAR = 2010
ANALYSIS_END_YEAR = 2019
ECONOMIC_EVENT_YEAR = 2014

PLOT_STYLE = "ggplot"
PLOT_DPI = 100
PLOT_FIGSIZE_DEFAULT = (10, 6)

PANDAS_MAX_COLUMNS = None
PANDAS_MAX_ROWS = 100
