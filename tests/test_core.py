"""Core Tests for Kouei"""
import pytest
import pandas as pd
import numpy as np
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestSettings:
    """Test configuration settings"""
    
    def test_settings_load(self):
        from src.config.settings import settings
        assert settings is not None
        assert settings.api_port == 8000
    
    def test_settings_defaults(self):
        from src.config.settings import settings
        assert settings.redis_host == "localhost"
        assert settings.fractional_kelly == 0.5


class TestPreprocessing:
    """Test preprocessing functions"""
    
    def test_preprocess_basic(self):
        from src.features.preprocessing import preprocess, FEATURES
        
        # Create sample data
        df = pd.DataFrame({
            'date': ['20240101'] * 6,
            'jyo_cd': ['02'] * 6,
            'race_no': [1] * 6,
            'boat_no': [1, 2, 3, 4, 5, 6],
            'racer_win_rate': [6.5, 5.0, 4.5, 4.0, 3.5, 3.0],
            'motor_2ren': [35, 30, 28, 25, 22, 20],
            'boat_2ren': [32, 28, 25, 23, 20, 18],
            'exhibition_time': [6.75, 6.80, 6.85, 6.90, 6.95, 7.00],
            'tilt': [-0.5, -0.5, -0.5, -0.5, -0.5, -0.5],
            'temperature': [15.0] * 6,
            'water_temperature': [12.0] * 6,
            'wind_speed': [3.0] * 6,
            'wave_height': [2] * 6,
            'wind_direction': [1] * 6,
            'weather': [1] * 6,
            'rank': [1, 2, 3, 4, 5, 6]
        })
        
        result = preprocess(df, is_training=True)
        
        assert 'target' in result.columns
        assert 'racer_win_rate_diff' in result.columns
        assert result['target'].sum() == 1  # Only one winner
    
    def test_preprocess_inference(self):
        from src.features.preprocessing import preprocess
        
        df = pd.DataFrame({
            'date': ['20240101'] * 6,
            'jyo_cd': ['02'] * 6,
            'race_no': [1] * 6,
            'boat_no': [1, 2, 3, 4, 5, 6],
            'racer_win_rate': [6.5, 5.0, 4.5, 4.0, 3.5, 3.0],
            'motor_2ren': [35, 30, 28, 25, 22, 20],
            'boat_2ren': [32, 28, 25, 23, 20, 18],
            'exhibition_time': [6.75, 6.80, None, 6.90, 6.95, 7.00],  # With missing
            'tilt': [-0.5] * 6,
        })
        
        result = preprocess(df, is_training=False)
        
        # Should handle missing values
        assert not result['exhibition_time'].isna().any()


class TestKelly:
    """Test Kelly Criterion calculations"""
    
    def test_kelly_basic(self):
        from src.portfolio.kelly import calculate_kelly_fraction
        
        # Favorable bet: 60% win prob, 2.0 odds
        kelly = calculate_kelly_fraction(0.6, 2.0, 1.0)
        assert kelly > 0
        assert kelly < 1
    
    def test_kelly_negative(self):
        from src.portfolio.kelly import calculate_kelly_fraction
        
        # Unfavorable bet: 30% win prob, 2.0 odds
        kelly = calculate_kelly_fraction(0.3, 2.0)
        assert kelly == 0  # Should not bet
    
    def test_kelly_fractional(self):
        from src.portfolio.kelly import calculate_kelly_fraction
        
        full_kelly = calculate_kelly_fraction(0.6, 2.0, 1.0)
        half_kelly = calculate_kelly_fraction(0.6, 2.0, 0.5)
        
        assert half_kelly == pytest.approx(full_kelly * 0.5)


class TestFormationOptimizer:
    """Test formation and box betting optimizer"""
    
    def test_formation_basic(self):
        from src.portfolio.formation_optimizer import FormationOptimizer
        
        optimizer = FormationOptimizer(bankroll=100000)
        
        predictions = [
            {"boat_no": 1, "probability": 0.40},
            {"boat_no": 3, "probability": 0.25},
            {"boat_no": 2, "probability": 0.15},
            {"boat_no": 4, "probability": 0.10},
            {"boat_no": 5, "probability": 0.06},
            {"boat_no": 6, "probability": 0.04},
        ]
        
        trifecta_odds = {
            (1, 3, 2): 8.5,
            (1, 2, 3): 12.0,
        }
        
        formation = optimizer.optimize_formation(predictions, trifecta_odds)
        
        # Should return a formation
        assert formation is not None or len(trifecta_odds) == 0
    
    def test_joint_probability(self):
        from src.portfolio.formation_optimizer import FormationOptimizer
        
        optimizer = FormationOptimizer()
        
        predictions = [
            {"boat_no": 1, "probability": 0.50},
            {"boat_no": 2, "probability": 0.30},
            {"boat_no": 3, "probability": 0.20},
        ]
        
        prob = optimizer.calculate_joint_probability(predictions, (1, 2, 3))
        
        assert prob > 0
        assert prob < 1


class TestCompatibility:
    """Test compatibility matrix"""
    
    def test_analyzer_init(self):
        from src.analysis.compatibility_matrix import get_compatibility_analyzer
        
        analyzer = get_compatibility_analyzer()
        assert analyzer is not None
    
    def test_risk_level(self):
        from src.portfolio.formation_optimizer import FormationOptimizer
        
        optimizer = FormationOptimizer()
        
        assert optimizer._get_risk_level(0.5) == "low"
        assert optimizer._get_risk_level(0.2) == "medium"
        assert optimizer._get_risk_level(0.1) == "high"


class TestLogger:
    """Test structured logging"""
    
    def test_logger_creation(self):
        from src.utils.logger import get_logger, StructuredLogger
        
        logger = get_logger("test")
        assert isinstance(logger, StructuredLogger)
    
    def test_logger_info(self, capsys):
        from src.utils.logger import StructuredLogger
        
        logger = StructuredLogger("test", json_format=False)
        logger.info("Test message", key="value")
        
        captured = capsys.readouterr()
        assert "Test message" in captured.out


class TestWeatherPredictor:
    """Test weather prediction"""
    
    def test_wind_impact(self):
        from src.analysis.weather_predictor import WeatherPredictor
        
        predictor = WeatherPredictor()
        
        # Strong wind
        impact = predictor.analyze_wind_impact("02", 6.0, 1)
        assert impact['severity'] == 'strong'
        
        # Light wind
        impact = predictor.analyze_wind_impact("02", 1.0, 1)
        assert impact['severity'] == 'normal'
    
    def test_tide_prediction(self):
        from src.analysis.weather_predictor import WeatherPredictor
        from datetime import datetime
        
        predictor = WeatherPredictor()
        
        tide = predictor.get_tide_prediction("03", datetime.now())
        
        assert 'tide_level' in tide
        assert 'tide_status' in tide
        assert tide['tide_level'] >= -1 and tide['tide_level'] <= 1


class TestAsyncCollector:
    """Test async data collector"""
    
    @pytest.mark.asyncio
    async def test_cache_check(self):
        from src.collector.async_collector import AsyncRaceCollector
        
        collector = AsyncRaceCollector()
        
        # Non-existent file should not be cached
        assert not collector._is_cache_valid("/nonexistent/path", None)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
