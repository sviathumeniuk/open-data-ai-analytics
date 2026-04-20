# Open Data AI Analytics

## Опис

Проєкт аналізує відкриті дані про платників ПДВ та побудований як набір окремих сервісів, які запускаються у Docker Compose.

Моніторинг: Prometheus використовується як Docker-образ `prom/prometheus:v2.54.1`.

Джерело даних:  
https://data.gov.ua/dataset/db391c93-1e68-43c9-bd85-7c6a8427b114

## Сервіси

- `db` — PostgreSQL;
- `data_load` — читає CSV з `raw/` і завантажує дані в таблицю `vat_registry`;
- `data_quality_analysis` — обчислює метрики якості та зберігає їх у БД і JSON;
- `data_research` — формує аналітичні агрегати та зберігає їх у БД і JSON;
- `visualization` — будує графіки у `reports/figures`;
- `web` — веб-інтерфейс для перегляду результатів.

## Актуальна структура

```text
.
├── .env
├── .env.template
├── compose.yaml
├── compose.prod.yaml
├── raw/
├── data_load/
├── data_quality_analysis/
├── data_research/
├── visualization/
├── web/
└── reports/
```

## Локальний запуск

1. Скопіюйте змінні середовища:

```bash
cp .env.template .env
```

2. Запустіть усі сервіси:

```bash
docker compose up --build
```

Після успішного запуску:

- веб-інтерфейс: http://localhost:8000
- PostgreSQL: `localhost:5432`

## Розділення dev/prod

- **Development (за замовчуванням):** `compose.yaml`
- **Production override:** `compose.prod.yaml`

Запуск у production-режимі:

```bash
docker compose -f compose.yaml -f compose.prod.yaml up --build -d
```

У production override вимкнено публікацію порту БД назовні (`db.ports: []`) і додано `restart` політики.

## Обмін даними між контейнерами

- через PostgreSQL (`vat_registry`, `data_quality_metrics`, `research_results`);
- через shared volume `./reports:/workspace/reports` для JSON-результатів і фігур.

## Виконані технічні вимоги

- окремий `Dockerfile` для кожного сервісу;
- єдиний `compose.yaml` для підняття всіх сервісів;
- власна Docker network (`analytics_net`);
- volumes для збереження БД та результатів (`db_data`, `./reports`);
- healthcheck для БД і веб-сервісу;
- автоматичне очікування готовності БД в сервісах (retry-loop);
- `.env`/`.env.template` для конфігурації;
- розділення development і production конфігурацій;
- базова оптимізація образів (`python:3.11-slim`, `--no-cache-dir`, `PYTHONDONTWRITEBYTECODE`, `PYTHONUNBUFFERED`).

## Автогенерація графіків

Поточні PNG-графіки можна видалити з `reports/figures`. Під час наступного запуску `visualization` сервіс згенерує їх автоматично.

## Лабораторні звіти

- `reports/labs/REPORT_1.md`
- `reports/labs/REPORT_2.md`
- `reports/labs/REPORT_3.md`
