import pytest
import schemathesis
from fastapi.testclient import TestClient
from app.main import app

# Create test client
client = TestClient(app)

# Create schemathesis test
schema = schemathesis.from_asgi(app)

@schema.parametrize()
def test_api_contracts(case):
    """Test API contracts using schemathesis"""
    response = case.call()
    case.validate_response(response)

class TestAPIContracts:
    def test_quotes_endpoint_contract(self):
        """Test quotes endpoint contract"""
        response = client.get("/api/v1/quotes")
        assert response.status_code in [200, 404]  # 404 if no data
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            for item in data:
                assert "symbol" in item
                assert "timestamp" in item
                assert "open" in item
                assert "high" in item
                assert "low" in item
                assert "close" in item
                assert "volume" in item

    def test_indicators_endpoint_contract(self):
        """Test indicators endpoint contract"""
        response = client.get("/api/v1/indicators")
        assert response.status_code in [200, 404]  # 404 if no data
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            for item in data:
                assert "symbol" in item
                assert "timestamp" in item
                assert "indicator_type" in item
                assert "value" in item
                assert "period" in item

    def test_health_endpoint_contract(self):
        """Test health endpoint contract"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "database" in data
        assert "version" in data
        assert data["status"] in ["healthy", "unhealthy"]

    def test_quotes_latest_endpoint_contract(self):
        """Test quotes latest endpoint contract"""
        response = client.get("/api/v1/quotes/latest")
        assert response.status_code in [200, 404]  # 404 if no data
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            for item in data:
                assert "symbol" in item
                assert "timestamp" in item
                assert "open" in item
                assert "high" in item
                assert "low" in item
                assert "close" in item
                assert "volume" in item

    def test_indicators_latest_endpoint_contract(self):
        """Test indicators latest endpoint contract"""
        response = client.get("/api/v1/indicators/latest")
        assert response.status_code in [200, 404]  # 404 if no data
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list)
            for item in data:
                assert "symbol" in item
                assert "timestamp" in item
                assert "indicator_type" in item
                assert "value" in item
                assert "period" in item

    def test_indicators_available_endpoint_contract(self):
        """Test indicators available endpoint contract"""
        response = client.get("/api/v1/indicators/available")
        assert response.status_code == 200
        data = response.json()
        assert "available_indicators" in data
        assert "total_types" in data
        assert isinstance(data["available_indicators"], dict)
        assert isinstance(data["total_types"], int)

    def test_error_response_contract(self):
        """Test error response contract"""
        # Test with invalid symbol
        response = client.get("/api/v1/quotes?symbol=NONEXISTENT")
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)

    def test_validation_error_contract(self):
        """Test validation error contract"""
        # Test with invalid limit
        response = client.get("/api/v1/quotes?limit=invalid")
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], list)  # Pydantic validation errors

    def test_root_endpoint_contract(self):
        """Test root endpoint contract"""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert isinstance(response.text, str)
        assert len(response.text) > 0
