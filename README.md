# 📈 Market Alpha Monitor

A monitoring service that ingests live market data, computes trading indicators, and exposes them as **Prometheus metrics** for visualization and alerting in **Grafana**.  
Think of it as **Prometheus for financial markets** — not a TradingView clone, but an observability system for trading signals and portfolio risk.

---

## 🚀 Features
- Fetches live market data (Binance API by default; CSV replay fallback).
- Computes core technical indicators:
  - RSI(14)
  - MACD(12,26,9)
  - ATR(14)
- Tracks **PnL** and **max drawdown** for simulated trades.
- Exposes everything at `/metrics` for **Prometheus** scraping.
- REST API endpoints:
  - `GET /api/signals?symbol=BTCUSDT`
  - `GET /api/trades`
  - `POST /api/trades`
  - `GET /metrics`
- Prebuilt **Grafana dashboards** for:
  - Price + Indicators
  - Portfolio Risk
  - Trades Overview
  - Service Health
- Example **alerts**:
  - Drawdown > 10%
  - Data feed stale
  - Volatility spike (ATR / Price > threshold)

---

## 🛠️ Architecture
```mermaid
flowchart LR
    A[Binance API / CSV Replay] --> B[FastAPI Service]
    B -->|/metrics| C[Prometheus]
    B -->|REST /api| D[Frontend / Users]
    C --> E[Grafana Dashboards]
    C --> F[Alertmanager]
    F --> G[Slack/Telegram Alerts]
    B --> H[Postgres DB: candles, signals, trades]
    B --> I[Celery Worker + Redis Queue]
