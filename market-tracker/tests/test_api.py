import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db import get_db, Base
from app.models import Price, Indicator
from datetime import datetime, timedelta
import os

# Test database URL
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def setup_database():
    """Set up test database"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)

@pytest.fixture
def sample_data(setup_database):
    """Create sample data for testing"""
    db = TestingSessionLocal()
    
    # Create sample price data
    now = datetime.utcnow()
    prices = [
        Price(
            symbol="AAPL",
            ts=now - timedelta(minutes=5),
            o=150.00,
            h=151.00,
            l=149.50,
            c=150.50,
            v=1000000
        ),
        Price(
            symbol="AAPL",
            ts=now - timedelta(minutes=4),
            o=150.50,
            h=152.00,
            l=150.00,
            c=151.50,
            v=1200000
        ),
        Price(
            symbol="MSFT",
            ts=now - timedelta(minutes=5),
            o=300.00,
            h=301.00,
            l=299.50,
            c=300.50,
            v=800000
        )
    ]
    
    # Create sample indicator data
    indicators = [
        Indicator(
            symbol="AAPL",
            ts=now - timedelta(minutes=5),
            indicator_type="ema",
            value=150.25,
            period=21
        ),
        Indicator(
            symbol="AAPL",
            ts=now - timedelta(minutes=5),
            indicator_type="rsi",
            value=65.5,
            period=14
        )
    ]
    
    for price in prices:
        db.add(price)
    for indicator in indicators:
        db.add(indicator)
    
    db.commit()
    yield
    db.close()

class TestHealthEndpoints:
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "unhealthy"]
        assert "timestamp" in data
        assert "database" in data
        assert "version" in data

    def test_readiness_check(self, client):
        """Test readiness check endpoint"""
        response = client.get("/api/v1/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"

    def test_liveness_check(self, client):
        """Test liveness check endpoint"""
        response = client.get("/api/v1/health/live")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "alive"

class TestQuotesEndpoints:
    def test_get_quotes_all(self, client, sample_data):
        """Test getting all quotes"""
        response = client.get("/api/v1/quotes")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert all("symbol" in item for item in data)
        assert all("timestamp" in item for item in data)

    def test_get_quotes_by_symbol(self, client, sample_data):
        """Test getting quotes for specific symbol"""
        response = client.get("/api/v1/quotes?symbol=AAPL")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert all(item["symbol"] == "AAPL" for item in data)

    def test_get_quotes_invalid_symbol(self, client, sample_data):
        """Test getting quotes for non-existent symbol"""
        response = client.get("/api/v1/quotes?symbol=INVALID")
        assert response.status_code == 404

    def test_get_quotes_with_limit(self, client, sample_data):
        """Test getting quotes with limit"""
        response = client.get("/api/v1/quotes?limit=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 1

    def test_get_quotes_with_hours(self, client, sample_data):
        """Test getting quotes with hours filter"""
        response = client.get("/api/v1/quotes?hours=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 0

    def test_get_latest_quotes(self, client, sample_data):
        """Test getting latest quotes"""
        response = client.get("/api/v1/quotes/latest")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0

    def test_get_latest_quotes_specific_symbols(self, client, sample_data):
        """Test getting latest quotes for specific symbols"""
        response = client.get("/api/v1/quotes/latest?symbols=AAPL,MSFT")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        symbols = [item["symbol"] for item in data]
        assert "AAPL" in symbols or "MSFT" in symbols

class TestIndicatorsEndpoints:
    def test_get_indicators_all(self, client, sample_data):
        """Test getting all indicators"""
        response = client.get("/api/v1/indicators")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert all("indicator_type" in item for item in data)

    def test_get_indicators_by_symbol(self, client, sample_data):
        """Test getting indicators for specific symbol"""
        response = client.get("/api/v1/indicators?symbol=AAPL")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert all(item["symbol"] == "AAPL" for item in data)

    def test_get_indicators_by_type(self, client, sample_data):
        """Test getting indicators by type"""
        response = client.get("/api/v1/indicators?indicator_type=ema")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert all(item["indicator_type"] == "ema" for item in data)

    def test_get_indicators_by_period(self, client, sample_data):
        """Test getting indicators by period"""
        response = client.get("/api/v1/indicators?period=21")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert all(item["period"] == 21 for item in data)

    def test_get_latest_indicators(self, client, sample_data):
        """Test getting latest indicators"""
        response = client.get("/api/v1/indicators/latest")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0

    def test_get_available_indicators(self, client, sample_data):
        """Test getting available indicators"""
        response = client.get("/api/v1/indicators/available")
        assert response.status_code == 200
        data = response.json()
        assert "available_indicators" in data
        assert "total_types" in data

class TestRootEndpoint:
    def test_root_endpoint(self, client):
        """Test root endpoint returns HTML"""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "Market Tracker" in response.text

class TestErrorHandling:
    def test_invalid_query_parameters(self, client):
        """Test handling of invalid query parameters"""
        response = client.get("/api/v1/quotes?limit=invalid")
        assert response.status_code == 422  # Validation error

    def test_negative_limit(self, client):
        """Test handling of negative limit"""
        response = client.get("/api/v1/quotes?limit=-1")
        assert response.status_code == 422  # Validation error

    def test_excessive_limit(self, client):
        """Test handling of excessive limit"""
        response = client.get("/api/v1/quotes?limit=10000")
        assert response.status_code == 422  # Validation error
