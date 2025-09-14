# 📁 Market Tracker - Project Structure

This document provides a comprehensive overview of the Market Tracker project structure and organization.

## 🏗️ Architecture Overview

```
Yahoo Finance → ETL Service → PostgreSQL → Grafana
                          ↘ FastAPI API
```

## 📂 Directory Structure

```
MarketAlphaMonitor/
├── README.md                          # Project documentation
├── requirements.txt                   # Python dependencies
├── docker-compose.yml                # Service orchestration
├── .env.example                      # Environment variables template
├── .gitignore                        # Git ignore rules
├── PROJECT_STRUCTURE.md              # This file
│
├── .github/                          # GitHub Actions CI/CD
│   └── workflows/
│       └── ci.yml                    # CI/CD pipeline
│
├── market-tracker/                   # FastAPI Service
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI application
│   │   ├── db.py                     # Database connection
│   │   ├── models.py                 # SQLAlchemy models
│   │   └── routes/                   # API routes
│   │       ├── __init__.py
│   │       ├── quotes.py             # Quotes endpoints
│   │       ├── indicators.py         # Indicators endpoints
│   │       └── health.py             # Health check endpoints
│   ├── tests/                        # FastAPI tests
│   │   ├── test_api.py               # Unit tests
│   │   ├── test_contracts.py         # API contract tests
│   │   └── test_ui.py                # UI tests
│   └── Dockerfile                    # FastAPI container
│
├── yahoo_etl/                        # ETL Microservice
│   ├── etl.py                        # Main ETL logic
│   ├── scheduler.py                  # Celery scheduler
│   ├── db.py                         # Database connection
│   ├── tests/                        # ETL tests
│   │   ├── test_etl.py               # ETL unit tests
│   │   └── test_indicators.py        # Indicator calculation tests
│   └── Dockerfile                    # ETL container
│
├── grafana/                          # Grafana Configuration
│   └── provisioning/
│       ├── datasources/
│       │   └── postgres.yml          # PostgreSQL datasource
│       └── dashboards/
│           ├── dashboard.yml          # Dashboard provisioning
│           └── market.json           # Market dashboard
│
├── postgres/                         # Database Configuration
│   └── init.sql                      # Database schema
│
├── tests/                            # Integration Tests
│   └── load/
│       └── load_test.js              # k6 load tests
│
└── scripts/                          # Utility Scripts
    ├── setup.sh                      # Environment setup
    └── test.sh                       # Test runner
```

## 🔧 Service Details

### FastAPI Service (`market-tracker/`)
- **Purpose**: REST API for market data access
- **Port**: 8000
- **Endpoints**:
  - `GET /` - Web UI
  - `GET /api/v1/quotes` - Market quotes
  - `GET /api/v1/indicators` - Technical indicators
  - `GET /api/v1/health` - Health checks

### ETL Service (`yahoo_etl/`)
- **Purpose**: Data extraction and transformation
- **Features**:
  - Yahoo Finance data fetching
  - Technical indicator calculations (EMA, RSI)
  - Scheduled data updates (Celery Beat)
  - Data cleanup and maintenance

### PostgreSQL Database
- **Purpose**: Data persistence
- **Port**: 5432
- **Tables**:
  - `prices` - OHLCV market data
  - `indicators` - Technical indicators
- **Views**:
  - `latest_prices` - Most recent quotes
  - `latest_indicators` - Most recent indicators
  - `daily_aggregates` - Daily summaries

### Grafana
- **Purpose**: Data visualization and monitoring
- **Port**: 3000
- **Features**:
  - Real-time dashboards
  - Technical indicator charts
  - Volume analysis
  - Alerting capabilities

### Redis
- **Purpose**: Celery message broker
- **Port**: 6379
- **Features**:
  - Task queue management
  - Caching
  - Session storage

## 🧪 Testing Strategy

### Unit Tests
- **FastAPI**: `market-tracker/tests/`
- **ETL**: `yahoo_etl/tests/`
- **Coverage**: ≥85% required

### Integration Tests
- **API Contract Tests**: Schemathesis
- **UI Tests**: Playwright
- **Load Tests**: k6
- **Security Tests**: ZAP

### Test Execution
```bash
# Run all tests
./scripts/test.sh

# Run specific test types
pytest market-tracker/tests/          # FastAPI tests
pytest yahoo_etl/tests/              # ETL tests
k6 run tests/load/load_test.js        # Load tests
```

## 🚀 Deployment

### Local Development
```bash
# Setup environment
./scripts/setup.sh

# Start services
docker-compose up -d

# View logs
docker-compose logs -f
```

### Production
- **CI/CD**: GitHub Actions
- **Container Registry**: Docker Hub
- **Deployment**: EC2 with Docker Compose
- **Monitoring**: Grafana dashboards

## 📊 Monitoring & Observability

### Health Checks
- **FastAPI**: `/api/v1/health`
- **Database**: Connection status
- **Redis**: Ping test
- **ETL**: Task execution status

### Metrics
- **API Response Times**
- **Database Query Performance**
- **ETL Processing Times**
- **Error Rates**
- **Resource Utilization**

### Alerts
- **High Error Rates**
- **Slow Response Times**
- **Database Connection Issues**
- **ETL Processing Failures**

## 🔒 Security

### Authentication
- **API Keys**: For external access
- **JWT Tokens**: For user sessions
- **Rate Limiting**: Per endpoint

### Data Protection
- **Encryption**: At rest and in transit
- **Access Control**: Role-based permissions
- **Audit Logging**: All API calls

### Security Testing
- **ZAP Baseline Scan**: Automated security testing
- **Dependency Scanning**: Vulnerability detection
- **Code Analysis**: Static security analysis

## 📈 Performance

### Optimization
- **Database Indexing**: Optimized queries
- **Caching**: Redis for frequent data
- **Connection Pooling**: Database connections
- **Async Processing**: Non-blocking operations

### Scaling
- **Horizontal Scaling**: Multiple API instances
- **Database Replication**: Read replicas
- **Load Balancing**: Traffic distribution
- **Auto-scaling**: Based on metrics

## 🛠️ Development

### Code Quality
- **Linting**: Ruff
- **Formatting**: Black
- **Type Checking**: MyPy
- **Pre-commit Hooks**: Automated checks

### Documentation
- **API Docs**: OpenAPI/Swagger
- **Code Comments**: Inline documentation
- **README**: Setup and usage
- **Architecture**: System design

### Version Control
- **Git Flow**: Feature branches
- **Conventional Commits**: Standardized messages
- **Pull Requests**: Code review process
- **Automated Testing**: CI/CD pipeline

## 📋 Maintenance

### Regular Tasks
- **Data Cleanup**: Old data removal
- **Security Updates**: Dependency updates
- **Performance Monitoring**: Metrics review
- **Backup Verification**: Data integrity

### Monitoring
- **Uptime**: Service availability
- **Performance**: Response times
- **Errors**: Exception tracking
- **Resources**: CPU, memory, disk

This project structure provides a robust, scalable, and maintainable foundation for the Market Tracker application.
