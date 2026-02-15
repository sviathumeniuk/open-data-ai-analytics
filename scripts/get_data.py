import requests
import pandas as pd
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.config import DATA_DIR, DATA_FILE, DATA_URL, REQUEST_TIMEOUT, CSV_SEP, CSV_ENCODING, CSV_ON_BAD_LINES


def download_data():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    print("Завантаження даних...")
    
    try:
        response = requests.get(DATA_URL, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        
        with open(DATA_FILE, "wb") as f:
            f.write(response.content)
        
        df = pd.read_csv(
            DATA_FILE,
            sep=CSV_SEP,
            on_bad_lines=CSV_ON_BAD_LINES,
            encoding=CSV_ENCODING
        )
        
        print(f"Збережено: {DATA_FILE}")
        return df
    
    except Exception as e:
        print(f"Помилка: {e}")
        return None


if __name__ == "__main__":
    download_data()
