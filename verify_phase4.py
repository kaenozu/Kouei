import sys
import os
import json
import logging
sys.path.append(os.getcwd())

from src.schemas.config import AppConfig
from src.model.predictor import Predictor
from src.inference.whale import WhaleDetector

def verify():
    # 1. Pydantic
    print("--- 1. Testing Pydantic ---")
    cfg = AppConfig(discord_webhook_url="http://fake.com")
    print(f"Config Valid: {cfg}")
    
    # 2. ONNX
    print("--- 2. Testing ONNX Predictor ---")
    predictor = Predictor()
    if predictor.mode == "onnx":
        print("Success: Loaded ONNX mode.")
    else:
        print(f"Fallback: Loaded {predictor.mode} mode.")
    # Dummy predict
    try:
        # 16 features dummy
        dummy_x = [[0.5]*16]
        pred = predictor.predict(dummy_x)
        print(f"Prediction result: {pred[0]}")
    except Exception as e:
        print(f"Prediction Error: {e}")

    # 3. Whale Watcher
    print("--- 3. Testing Whale Watcher ---")
    wd = WhaleDetector()
    race_id = "TEST_RACE_001"
    
    # First check (init)
    first_odds = {"1-2-3": 10.0}
    wd.detect_abnormal_drop(race_id, first_odds)
    
    # Second check (drop)
    second_odds = {"1-2-3": 5.0} # 50% drop
    alerts = wd.detect_abnormal_drop(race_id, second_odds)
    print(f"Alerts Triggered: {len(alerts)}")
    if len(alerts) > 0:
        print(f"Example Alert: {alerts[0]}")

if __name__ == "__main__":
    verify()
