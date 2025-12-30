"""Pytest Configuration and Fixtures"""
import pytest
import pandas as pd
import numpy as np
import os
import sys
import tempfile
import shutil

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session")
def project_root():
    """Get project root directory"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@pytest.fixture(scope="session")
def sample_race_data():
    """Create sample race data for testing"""
    np.random.seed(42)
    n_races = 10
    n_boats = 6
    
    data = []
    for race_idx in range(n_races):
        date = f"202401{(race_idx + 1):02d}"
        jyo_cd = "02"
        race_no = (race_idx % 12) + 1
        
        for boat_no in range(1, n_boats + 1):
            data.append({
                'date': date,
                'jyo_cd': jyo_cd,
                'race_no': race_no,
                'boat_no': boat_no,
                'racer_id': f"{4000 + boat_no}",
                'racer_name': f"Racer {boat_no}",
                'racer_win_rate': 3.0 + np.random.random() * 4,
                'motor_2ren': 20 + np.random.random() * 30,
                'boat_2ren': 20 + np.random.random() * 25,
                'exhibition_time': 6.6 + np.random.random() * 0.4,
                'tilt': -0.5,
                'temperature': 15 + np.random.random() * 10,
                'water_temperature': 12 + np.random.random() * 8,
                'wind_speed': np.random.random() * 8,
                'wave_height': np.random.randint(1, 6),
                'wind_direction': np.random.randint(1, 17),
                'weather': np.random.randint(1, 5),
                'rank': boat_no,  # Simplified: boat 1 always wins
            })
    
    return pd.DataFrame(data)


@pytest.fixture(scope="session")
def sample_race_data_no_results():
    """Create sample race data without results (for prediction testing)"""
    np.random.seed(42)
    
    data = []
    date = "20240115"
    jyo_cd = "02"
    race_no = 1
    
    for boat_no in range(1, 7):
        data.append({
            'date': date,
            'jyo_cd': jyo_cd,
            'race_no': race_no,
            'boat_no': boat_no,
            'racer_id': f"{4000 + boat_no}",
            'racer_name': f"Racer {boat_no}",
            'racer_win_rate': 3.0 + np.random.random() * 4,
            'motor_2ren': 20 + np.random.random() * 30,
            'boat_2ren': 20 + np.random.random() * 25,
            'exhibition_time': 6.6 + np.random.random() * 0.4,
            'tilt': -0.5,
            'temperature': 18.5,
            'water_temperature': 15.0,
            'wind_speed': 3.0,
            'wave_height': 2,
            'wind_direction': 8,
            'weather': 1,
            'rank': None,  # No result yet
        })
    
    return pd.DataFrame(data)


@pytest.fixture(scope="function")
def temp_data_dir():
    """Create temporary data directory"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


@pytest.fixture(scope="session")
def mock_model():
    """Create mock predictor for testing"""
    class MockPredictor:
        def predict(self, X, pred_contrib=False):
            n = len(X)
            if pred_contrib:
                # Return contributions (n_samples, n_features + 1)
                return np.random.random((n, len(X.columns) + 1))
            else:
                # Return probabilities
                probs = np.random.random(n)
                return probs / probs.sum()  # Normalize
    
    return MockPredictor()


@pytest.fixture(scope="session")
def stadiums():
    """Stadium mapping"""
    return {
        "01": "桐生", "02": "戸田", "03": "江戸川", "04": "平和島", "05": "多摩川",
        "06": "浜名湖", "07": "蒲郡", "08": "常滑", "09": "津", "10": "三国",
        "11": "びわこ", "12": "住之江", "13": "尼崎", "14": "鳴門", "15": "丸亀",
        "16": "児島", "17": "宮島", "18": "徳山", "19": "下関", "20": "若松",
        "21": "芦屋", "22": "福岡", "23": "唐津", "24": "大村"
    }


# Markers
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
