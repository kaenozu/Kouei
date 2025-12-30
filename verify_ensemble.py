import sys
import os
sys.path.append(os.getcwd())
try:
    from src.model.ensemble import EnsemblePredictor
    predictor = EnsemblePredictor()
    predictor.load_models()
    print("EnsemblePredictor initialized successfully.")
    print(f"Loaded models: {predictor.models.keys()}")
except Exception as e:
    print(f"Ensemble verification failed: {e}")
