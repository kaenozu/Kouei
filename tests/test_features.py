"""Tests for Feature Engineering"""
import pytest
import pandas as pd
import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestPreprocessing:
    """Test preprocessing functions"""
    
    def test_preprocess_basic(self):
        from src.features.preprocessing import preprocess, FEATURES
        
        df = pd.DataFrame({
            'date': ['20240101'] * 6,
            'jyo_cd': ['02'] * 6,
            'race_no': [1] * 6,
            'boat_no': [1, 2, 3, 4, 5, 6],
            'racer_win_rate': [6.5, 5.0, 4.5, 4.0, 3.5, 3.0],
            'motor_2ren': [35, 30, 28, 25, 22, 20],
            'boat_2ren': [32, 28, 25, 23, 20, 18],
            'exhibition_time': [6.75, 6.80, 6.85, 6.90, 6.95, 7.00],
            'tilt': [-0.5] * 6,
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
        assert 'motor_2ren_diff' in result.columns
        assert result['target'].sum() == 1  # Only one winner
    
    def test_preprocess_inference(self):
        from src.features.preprocessing import preprocess, FEATURES
        
        df = pd.DataFrame({
            'date': ['20240101'] * 6,
            'jyo_cd': ['02'] * 6,
            'race_no': [1] * 6,
            'boat_no': [1, 2, 3, 4, 5, 6],
            'racer_win_rate': [6.5, 5.0, 4.5, 4.0, 3.5, 3.0],
            'motor_2ren': [35, 30, 28, 25, 22, 20],
            'boat_2ren': [32, 28, 25, 23, 20, 18],
            'exhibition_time': [6.75, 6.80, 6.85, 6.90, 6.95, 7.00],
        })
        
        result = preprocess(df, is_training=False)
        
        # Should not have target column
        assert 'target' not in result.columns
        # Should have diff features
        assert 'racer_win_rate_diff' in result.columns
    
    def test_preprocess_missing_values(self):
        from src.features.preprocessing import preprocess
        
        df = pd.DataFrame({
            'date': ['20240101'] * 3,
            'jyo_cd': ['02'] * 3,
            'race_no': [1] * 3,
            'boat_no': [1, 2, 3],
            'racer_win_rate': [6.5, None, 4.5],
            'motor_2ren': [35, 30, None],
            'exhibition_time': [None, 6.80, 6.85],
        })
        
        result = preprocess(df, is_training=False)
        
        # Should handle NaN values
        assert not result['racer_win_rate'].isna().any()
        assert not result['motor_2ren'].isna().any()


class TestTimeSeriesFeatures:
    """Test time series feature generation"""
    
    def test_momentum_score(self):
        from src.features.time_series import TimeSeriesFeatureGenerator
        
        generator = TimeSeriesFeatureGenerator(lookback_races=5)
        
        df = pd.DataFrame({
            'date': ['20240101', '20240102', '20240103', '20240104', '20240105'],
            'racer_id': ['1234'] * 5,
            'race_no': [1, 2, 3, 4, 5],
            'jyo_cd': ['02'] * 5,
            'rank': [1, 1, 1, 1, 1],  # All wins
        })
        
        result = generator.generate_features(df)
        
        # Last race should have high momentum
        assert 'momentum_score' in result.columns
        last_momentum = result.iloc[-1]['momentum_score']
        assert last_momentum > 0  # Positive momentum for wins
    
    def test_win_streak(self):
        from src.features.time_series import TimeSeriesFeatureGenerator
        
        generator = TimeSeriesFeatureGenerator(lookback_races=5)
        
        df = pd.DataFrame({
            'date': ['20240101', '20240102', '20240103', '20240104', '20240105'],
            'racer_id': ['1234'] * 5,
            'race_no': [1, 2, 3, 4, 5],
            'jyo_cd': ['02'] * 5,
            'rank': [3, 2, 1, 1, 1],  # 3 consecutive wins at end
        })
        
        result = generator.generate_features(df)
        
        assert 'win_streak' in result.columns
        # Last race should show 2 win streak (not counting itself)
        last_streak = result.iloc[-1]['win_streak']
        assert last_streak == 2
    
    def test_top3_rate(self):
        from src.features.time_series import TimeSeriesFeatureGenerator
        
        generator = TimeSeriesFeatureGenerator(lookback_races=5)
        
        df = pd.DataFrame({
            'date': ['20240101', '20240102', '20240103', '20240104', '20240105', '20240106'],
            'racer_id': ['1234'] * 6,
            'race_no': [1, 2, 3, 4, 5, 6],
            'jyo_cd': ['02'] * 6,
            'rank': [1, 2, 3, 4, 5, 6],  # Degrading performance
        })
        
        result = generator.generate_features(df)
        
        assert 'top3_rate_recent' in result.columns
        # Last race should have 60% top3 rate (3 out of 5)
        last_top3_rate = result.iloc[-1]['top3_rate_recent']
        assert 0.5 <= last_top3_rate <= 0.7


class TestCompatibilityAnalysis:
    """Test compatibility matrix analysis"""
    
    def test_analyzer_initialization(self):
        from src.analysis.compatibility_matrix import CompatibilityAnalyzer
        
        analyzer = CompatibilityAnalyzer()
        assert analyzer is not None
    
    def test_confidence_levels(self):
        from src.analysis.compatibility_matrix import CompatibilityAnalyzer
        
        analyzer = CompatibilityAnalyzer()
        
        assert analyzer._get_confidence(100) == "S"
        assert analyzer._get_confidence(50) == "S"
        assert analyzer._get_confidence(25) == "A"
        assert analyzer._get_confidence(15) == "B"
        assert analyzer._get_confidence(5) == "C"
    
    def test_recommendation(self):
        from src.analysis.compatibility_matrix import CompatibilityAnalyzer
        
        analyzer = CompatibilityAnalyzer()
        
        assert "有利" in analyzer._get_recommendation(0.6)
        assert "標準" in analyzer._get_recommendation(0.0)
        assert "不利" in analyzer._get_recommendation(-0.6)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
