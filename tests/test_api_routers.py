"""Tests for API Routers"""
import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="module")
def client():
    """Create test client"""
    try:
        from src.api.main_api_new import app
        return TestClient(app)
    except Exception as e:
        pytest.skip(f"Could not import API: {e}")


class TestSystemEndpoints:
    """Test system endpoints"""
    
    def test_root(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert data["name"] == "Kouei AI API"
    
    def test_health(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_status(self, client):
        response = client.get("/api/status")
        assert response.status_code == 200
        data = response.json()
        assert "model_loaded" in data
        assert "dataset_size" in data
        assert "cache_status" in data


class TestRacesEndpoints:
    """Test races endpoints"""
    
    def test_stadiums(self, client):
        response = client.get("/api/stadiums")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 24  # 24 boat race stadiums
        assert all("code" in s and "name" in s for s in data)
    
    def test_races_invalid_date(self, client):
        response = client.get("/api/races?date=invalid&jyo=02")
        assert response.status_code == 422  # Validation error
    
    def test_races_valid_params(self, client):
        response = client.get("/api/races?date=20240101&jyo=02")
        assert response.status_code == 200
    
    def test_today_races(self, client):
        response = client.get("/api/today")
        assert response.status_code == 200
        data = response.json()
        # Should have meta and races keys, or error
        assert "meta" in data or "error" in data or "races" in data


class TestPredictionEndpoints:
    """Test prediction endpoints"""
    
    def test_prediction_missing_data(self, client):
        response = client.get("/api/prediction?date=19000101&jyo=99&race=1")
        assert response.status_code == 200
        data = response.json()
        # Should return error or empty predictions
        assert "error" in data or "predictions" in data
    
    def test_similar_races(self, client):
        response = client.get("/api/similar-races?jyo_cd=02&wind=3.0&wave=1.0")
        assert response.status_code == 200
    
    def test_what_if_simulation(self, client):
        response = client.post(
            "/api/simulate-what-if",
            json={"modifications": {"wind_speed": 5.0}}
        )
        assert response.status_code == 200


class TestBettingEndpoints:
    """Test betting endpoints"""
    
    def test_odds(self, client):
        response = client.get("/api/odds?date=20240101&jyo=02&race=1")
        assert response.status_code == 200
    
    def test_betting_optimize(self, client):
        response = client.post(
            "/api/betting/optimize",
            json={
                "date": "20240101",
                "jyo": "02",
                "race": 1,
                "budget": 10000,
                "bet_type": "sanrentan",
                "kelly_fraction": 0.5
            }
        )
        assert response.status_code == 200
    
    def test_formation_optimize(self, client):
        response = client.post(
            "/api/betting/formation?date=20240101&jyo=02&race=1&budget=10000&formation_type=box"
        )
        assert response.status_code == 200


class TestPortfolioEndpoints:
    """Test portfolio endpoints"""
    
    def test_portfolio(self, client):
        response = client.get("/api/portfolio")
        assert response.status_code == 200
    
    def test_simulation(self, client):
        response = client.get("/api/simulation?threshold=0.4")
        assert response.status_code == 200
    
    def test_backtest(self, client):
        response = client.post(
            "/api/backtest",
            json={"stadium": "02", "min_prob": 0.4}
        )
        assert response.status_code == 200
    
    def test_strategies(self, client):
        response = client.get("/api/strategies")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestAnalysisEndpoints:
    """Test analysis endpoints"""
    
    def test_racer_stats(self, client):
        response = client.get("/api/racer/4444?n_races=10")
        assert response.status_code == 200
    
    def test_compatibility(self, client):
        response = client.get(
            "/api/compatibility?racer_id=4444&motor_no=01&stadium=02&course=1"
        )
        assert response.status_code == 200
    
    def test_stadium_matrix(self, client):
        response = client.get("/api/stadium-matrix/02")
        assert response.status_code == 200
    
    def test_concierge_chat(self, client):
        response = client.post(
            "/api/concierge/chat",
            json={"query": "今日のおすすめは？"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data


class TestSyncEndpoints:
    """Test sync endpoints"""
    
    def test_sync(self, client):
        response = client.get("/api/sync")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
    
    def test_config_get(self, client):
        response = client.get("/api/config")
        assert response.status_code == 200
    
    def test_config_update(self, client):
        response = client.post(
            "/api/config",
            json={"test_key": "test_value"}
        )
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
