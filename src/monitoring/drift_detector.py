"""
Data Drift Monitoring
Compares latest race data distribution with training data distribution to detect model degradation.
Uses Kolmogorov-Smirnov test for distribution comparison.
"""
import pandas as pd
import numpy as np
from scipy.stats import ks_2samp
import os
import json
from datetime import datetime

DATA_PATH = "data/processed/race_data.csv"
BASELINE_STATS_PATH = "models/baseline_stats.json"

class DriftDetector:
    def __init__(self, data_path=DATA_PATH):
        self.data_path = data_path
        self.features = [
            'racer_win_rate', 'motor_2ren', 'exhibition_time',
            'wind_speed', 'wave_height', 'temperature'
        ]

    def _load_data(self):
        if not os.path.exists(self.data_path):
            return None
        return pd.read_csv(self.data_path)

    def generate_baseline(self):
        """Generate baseline statistics from current data (assumed stable)"""
        df = self._load_data()
        if df is None: return
        
        # Use older data as baseline (e.g., first 70%)
        baseline_df = df.head(int(len(df) * 0.7))
        stats = {}
        for feat in self.features:
            if feat in baseline_df.columns:
                stats[feat] = baseline_df[feat].dropna().tolist()
        
        with open(BASELINE_STATS_PATH, "w") as f:
            # We don't save all values, maybe just a sample or summary
            json.dump({k: np.random.choice(v, min(len(v), 500)).tolist() for k, v in stats.items()}, f)
        print(f"✅ Baseline generated: {BASELINE_STATS_PATH}")

    def check_drift(self, threshold=0.05):
        """Check if recent data has drifted from baseline"""
        if not os.path.exists(BASELINE_STATS_PATH):
            self.generate_baseline()
            
        with open(BASELINE_STATS_PATH, "r") as f:
            baseline_data = json.load(f)
            
        df = self._load_data()
        if df is None: return {"status": "error", "message": "No data"}
        
        # Latest data (last 30%)
        recent_df = df.tail(int(len(df) * 0.3))
        
        results = {}
        drift_detected = False
        
        for feat in self.features:
            if feat in recent_df.columns and feat in baseline_data:
                recent_vals = recent_df[feat].dropna().tolist()
                baseline_vals = baseline_data[feat]
                
                # KS Test
                statistic, p_value = ks_2samp(baseline_vals, recent_vals)
                
                results[feat] = {
                    "p_value": float(p_value),
                    "drift": bool(p_value < threshold)
                }
                if p_value < threshold:
                    drift_detected = True
        
        return {
            "timestamp": datetime.now().isoformat(),
            "drift_detected": bool(drift_detected),
            "metrics": results
        }

if __name__ == "__main__":
    detector = DriftDetector()
    print("Checking for data drift...")
    report = detector.check_drift()
    print(json.dumps(report, indent=2))
