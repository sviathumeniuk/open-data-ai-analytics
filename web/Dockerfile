FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Копіюємо залежності та встановлюємо їх
COPY web/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Копіюємо код веб-додатка та пайплайна
COPY web/ ./web/
COPY pipeline/ ./pipeline/

# Встановлюємо змінні середовища
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=web/app.py
ENV PYTHONPATH=/workspace

EXPOSE 8000

# Запускаємо через gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "web.app:app"]
