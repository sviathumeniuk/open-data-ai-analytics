import requests
import pandas as pd
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "raw"
DATA_URL = "https://data.gov.ua/dataset/95d06529-0367-48da-96dd-c6eb9beeedf3/resource/e5af2194-f78d-46df-9de0-7eeb4155c0e6/download/pdv_actual_28-08-2019.csv"


def download_data():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    print("Завантаження даних...")
    
    try:
        response = requests.get(DATA_URL, timeout=30)
        response.raise_for_status()
        
        output_file = DATA_DIR / "pdv_actual_28-08-2019.csv"
        with open(output_file, "wb") as f:
            f.write(response.content)
        
        df = pd.read_csv(
            output_file,
            sep=None,
            engine='python',
            on_bad_lines='skip',
            encoding='utf-8'
        )
        
        print(f"Збережено: {output_file}")
        return df
    
    except Exception as e:
        print(f"Помилка: {e}")
        return None


if __name__ == "__main__":
    download_data()
