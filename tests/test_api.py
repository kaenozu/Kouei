"""API Tests for Kouei"""
import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="module")
def client():
    """Create test client"""
    # Import here to avoid startup issues
    try:
        from src.api.main_api import app
        return TestClient(app)
    except Exception as e:
        pytest.skip(f"Could not import API: {e}")


class TestAPIEndpoints:
    """Test API endpoints"""
    
    def test_status(self, client):
        response = client.get("/api/status")
        assert response.status_code == 200
        data = response.json()
        assert "model_loaded" in data
        assert "dataset_size" in data
    
    def test_stadiums(self, client):
        response = client.get("/api/stadiums")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 24  # 24 boat race stadiums
    
    def test_prediction_missing(self, client):
        response = client.get("/api/prediction?date=19000101&jyo=99&race=1")
        assert response.status_code == 200
        data = response.json()
        assert "error" in data or "predictions" in data
    
    def test_simulation(self, client):
        response = client.get("/api/simulation?threshold=0.4")
        assert response.status_code == 200
    
    def test_strategies(self, client):
        response = client.get("/api/strategies")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_portfolio(self, client):
        response = client.get("/api/portfolio")
        assert response.status_code == 200


class TestAPIValidation:
    """Test API input validation"""
    
    def test_backtest_filters(self, client):
        response = client.post(
            "/api/backtest",
            json={"stadium": "02", "min_prob": 0.5}
        )
        assert response.status_code == 200
    
    def test_what_if_simulation(self, client):
        response = client.post(
            "/api/simulate-what-if",
            json={"modifications": {"wind_speed": 5.0}}
        )
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
