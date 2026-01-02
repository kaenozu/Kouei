"""Tests for new features: Odds, Accuracy, and Enhanced Components"""
import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.api.main_api_new import app


@pytest.fixture(scope="module")
def client():
    """Create test client for API testing"""
    with TestClient(app) as c:
        yield c


class TestOddsAPI:
    """Tests for odds analysis API"""
    
    def test_get_odds_returns_structure(self, client):
        """Test that odds endpoint returns expected structure"""
        response = client.get("/api/odds/analysis?date=20260101&jyo=21&race=1")
        assert response.status_code == 200
        data = response.json()
        
        assert "date" in data
        assert "jyo_cd" in data
        assert "race_no" in data
        assert "tansho" in data
        assert "value_bets" in data
        assert "alerts" in data
    
    def test_odds_tansho_structure(self, client):
        """Test tansho odds structure"""
        response = client.get("/api/odds/analysis?date=20260101&jyo=21&race=1")
        data = response.json()
        
        tansho = data.get("tansho", [])
        assert len(tansho) >= 1
        
        for item in tansho:
            assert "odds" in item
    
    def test_value_bets_have_ev(self, client):
        """Test that value bets include expected value"""
        response = client.get("/api/odds/analysis?date=20260101&jyo=21&race=1")
        data = response.json()
        
        value_bets = data.get("value_bets", [])
        for bet in value_bets:
            assert "ev" in bet
            assert bet["ev"] > 1.0  # Should only include positive EV bets


class TestAccuracyAPI:
    """Tests for accuracy tracking API"""
    
    def test_get_accuracy_stats(self, client):
        """Test accuracy stats endpoint"""
        response = client.get("/api/accuracy?days=7")
        assert response.status_code == 200
        data = response.json()
        
        assert "overall" in data
        assert "daily" in data
        assert "by_confidence" in data
        assert "by_course" in data
    
    def test_overall_stats_structure(self, client):
        """Test overall stats structure"""
        response = client.get("/api/accuracy?days=7")
        data = response.json()
        
        overall = data.get("overall", {})
        assert "win_rate" in overall
        assert "top2_rate" in overall
        assert "top3_rate" in overall
        assert "roi" in overall
        
        # Validate ranges
        assert 0 <= overall["win_rate"] <= 1
        assert 0 <= overall["top2_rate"] <= 1
        assert 0 <= overall["top3_rate"] <= 1
    
    def test_daily_stats_structure(self, client):
        """Test daily stats structure"""
        response = client.get("/api/accuracy?days=7")
        data = response.json()
        
        daily = data.get("daily", [])
        assert len(daily) <= 7
        
        for day in daily:
            assert "date" in day
            assert "accuracy" in day
    
    def test_by_confidence_structure(self, client):
        """Test by-confidence stats structure"""
        response = client.get("/api/accuracy?days=7")
        data = response.json()
        
        by_confidence = data.get("by_confidence", [])
        for item in by_confidence:
            assert "level" in item
            assert "count" in item
            assert "hit_rate" in item
    
    def test_by_course_structure(self, client):
        """Test by-course stats structure"""
        response = client.get("/api/accuracy?days=7")
        data = response.json()
        
        by_course = data.get("by_course", [])
        for item in by_course:
            assert "course" in item
            assert "predictions" in item
            assert "wins" in item
            assert "rate" in item
    
    def test_record_prediction(self, client):
        """Test recording a prediction"""
        response = client.post(
            "/api/accuracy/record",
            params={
                "date": "20260101",
                "jyo": "21",
                "race": 1,
                "boat": 1,
                "probability": 0.45,
                "confidence": "A"
            }
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
    
    def test_record_result(self, client):
        """Test recording a race result"""
        response = client.post(
            "/api/accuracy/result",
            params={
                "date": "20260101",
                "jyo": "21",
                "race": 1,
                "winner": 1
            }
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestExistingEndpoints:
    """Regression tests for existing endpoints"""
    
    def test_prediction_endpoint(self, client):
        """Test prediction endpoint still works"""
        response = client.get("/api/prediction?date=20260101&jyo=21&race=1")
        assert response.status_code == 200
        data = response.json()
        assert "predictions" in data
    
    def test_today_endpoint(self, client):
        """Test today endpoint still works"""
        response = client.get("/api/today")
        assert response.status_code == 200
    
    def test_status_endpoint(self, client):
        """Test status endpoint still works"""
        response = client.get("/api/status")
        assert response.status_code == 200
    
    def test_stadiums_endpoint(self, client):
        """Test stadiums endpoint still works"""
        response = client.get("/api/stadiums")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0


class TestIntegration:
    """Integration tests"""
    
    def test_prediction_with_accuracy_tracking(self, client):
        """Test that predictions can be tracked for accuracy"""
        # Get a prediction
        pred_response = client.get("/api/prediction?date=20260101&jyo=21&race=1")
        assert pred_response.status_code == 200
        predictions = pred_response.json().get("predictions", [])
        
        if predictions:
            # Record the top prediction
            top_pred = predictions[0]
            record_response = client.post(
                "/api/accuracy/record",
                params={
                    "date": "20260101",
                    "jyo": "21",
                    "race": 1,
                    "boat": top_pred.get("boat_no", 1),
                    "probability": top_pred.get("probability", 0.5)
                }
            )
            assert record_response.status_code == 200
    
    def test_odds_with_prediction(self, client):
        """Test that odds can be combined with predictions for EV calculation"""
        # Get odds
        odds_response = client.get("/api/odds/analysis?date=20260101&jyo=21&race=1")
        assert odds_response.status_code == 200
        
        # Get prediction
        pred_response = client.get("/api/prediction?date=20260101&jyo=21&race=1")
        assert pred_response.status_code == 200
        
        # Both should work together
        odds_data = odds_response.json()
        pred_data = pred_response.json()
        
        # Value bets should be calculated if we have both
        assert "value_bets" in odds_data
