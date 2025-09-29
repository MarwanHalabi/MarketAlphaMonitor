# 📈 Market Tracker – Final Project

## Overview
This project is a **self-hosted market tracker** that demonstrates automation, software development, and testing practices.  
It pulls **1-minute interval market data** from **Yahoo Finance**, loads it into a **PostgreSQL database**, and visualizes it with **Grafana** dashboards.  

It includes:
- **ETL service** (`yahoo_etl`) for pulling + loading data
- **FastAPI service** (`market-tracker`) exposing APIs
- **PostgreSQL** for persistence
- **Grafana** for visualization + alerts
- **Automated tests** (API, ETL, UI, load, security)
- **CI/CD pipeline** with GitHub Actions

---

## ⚙️ Architecture

```
Yahoo Finance → ETL Service → PostgreSQL → Grafana
                          ↘ FastAPI API
```

- **ETL Service (Python, `yfinance`)**
  - Runs on a schedule (Celery Beat or cron).
  - Fetches 1-minute OHLCV bars (`AAPL`, `MSFT`, etc.).
  - UPSERTs rows into `prices` table.
  - Retries on errors, ensures idempotency.

- **Postgres**
  - Stores `prices` and computed `indicators`.
  - Schema:
    ```sql
    CREATE TABLE prices (
        symbol TEXT,
        ts TIMESTAMPTZ,
        o NUMERIC,
        h NUMERIC,
        l NUMERIC,
        c NUMERIC,
        v BIGINT,
        PRIMARY KEY(symbol, ts)
    );
    ```

- **FastAPI (`market-tracker`)**
  - Endpoints:
    - `GET /api/v1/quotes`
    - `GET /api/v1/indicators`
    - `GET /api/v1/health`
  - Minimal UI page for quick checks.

- **Grafana**
  - Connects to Postgres.
  - Dashboards with auto-refresh (5–10s).
  - Candlestick chart + EMA/RSI indicators.
  - Alerts when indicators cross thresholds.

---

## 📂 File Hierarchy

```
market-tracker/
├── README.md                 # This file
├── docker-compose.yml        # Orchestration for local + EC2
├── .github/
│   └── workflows/
│       └── ci.yml            # GitHub Actions pipeline
│
├── market-tracker/           # FastAPI service
│   ├── app/
│   │   ├── main.py
│   │   ├── routes/
│   │   │   ├── quotes.py
│   │   │   ├── indicators.py
│   │   │   └── health.py
│   │   ├── models.py
│   │   ├── db.py
│   │   └── __init__.py
│   ├── tests/
│   │   ├── test_api.py
│   │   ├── test_contracts.py
│   │   └── test_ui.py
│   └── Dockerfile
│
├── yahoo_etl/                # ETL microservice
│   ├── etl.py                # Main fetch + load logic
│   ├── scheduler.py          # Celery beat / cron
│   ├── db.py
│   ├── tests/
│   │   ├── test_etl.py
│   │   └── test_indicators.py
│   └── Dockerfile
│
├── grafana/
│   ├── provisioning/
│   │   ├── datasources/
│   │   │   └── postgres.yml
│   │   └── dashboards/
│   │       └── market.json   # Dashboard definition
│
└── postgres/
    └── init.sql              # DB schema init (prices, indicators)
```

---

## 🚀 Running Locally

```bash
# Build and run all services
docker compose up -d
```

Services:
- FastAPI → http://localhost:8000  
- Grafana → http://localhost:3000 (admin/admin)  
- Postgres → localhost:5432  

---

## 🧪 Testing

- **Unit tests**: pytest for ETL and API
- **API contract tests**: schemathesis
- **UI tests**: Playwright (minimal UI page)
- **Load tests**: k6
- **Security tests**: ZAP baseline
- **Linting**: ruff, black, mypy
- **Coverage**: pytest-cov (≥85%)

Run locally:
```bash
pytest --cov=.
```

---

## 🔄 CI/CD

GitHub Actions pipeline runs:
1. Lint + type check
2. Unit + integration tests
3. API contract tests
4. UI tests (Playwright headless)
5. Load tests (smoke)
6. Security scan
7. Build & push Docker images
8. Deploy to EC2

Reports:
- Allure (API + UI tests)
- Coverage XML
- k6 summaries
- ZAP logs

---

## 📊 Demo Flow

1. Show architecture diagram.  
2. Run CI in GitHub Actions → show reports.  
3. Trigger ETL manually → Grafana dashboard updates live.  
4. Show code snippets (ETL upsert, contract test, k6 script).  
