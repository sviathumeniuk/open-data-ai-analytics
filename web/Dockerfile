FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

# Створюємо структури папок ПЕРЕД копіюванням, щоб гарантувати права
RUN mkdir -p /workspace/data /workspace/raw /workspace/reports/figures/eda \
    /workspace/reports/data_quality /workspace/reports/data_research \
    && chmod -R 777 /workspace/data /workspace/reports

# Копіюємо залежності та встановлюємо їх
COPY web/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Копіюємо проект покроково
COPY raw/ /workspace/raw/
COPY pipeline/ /workspace/pipeline/
COPY web/ /workspace/web/

# Налаштовуємо шляхи пошуку модулів Python
ENV PYTHONPATH=/workspace
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "web.app:app"]
