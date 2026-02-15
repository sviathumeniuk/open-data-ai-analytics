import pandas as pd
from src.config import DATA_FILE, CSV_SEP, CSV_ENCODING, CSV_ON_BAD_LINES, DATE_FORMAT


def load_data(file_path=DATA_FILE):
    df = pd.read_csv(
        file_path,
        sep=CSV_SEP,
        encoding=CSV_ENCODING,
        on_bad_lines=CSV_ON_BAD_LINES,
    )
    return df


def process_data(df):
    df = df.copy()
    df["dat_term"] = df["dat_term"].replace("null", pd.NA)
    df["dat_reestr"] = pd.to_datetime(df["dat_reestr"], format=DATE_FORMAT, errors="coerce")
    return df
