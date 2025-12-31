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
import asyncio

DATA_PATH = "data/processed/race_data.csv"
BASELINE_STATS_PATH = "models/baseline_stats.json"
DRIFT_HISTORY_PATH = "data/drift_history.json"

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
                    "drift": bool(p_value < threshold),
                    "statistic": float(statistic)
                }
                if p_value < threshold:
                    drift_detected = True
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "drift_detected": bool(drift_detected),
            "metrics": results
        }
        
        # Save to history
        self._save_to_history(report)
        
        return report
    
    def _save_to_history(self, report):
        """Save drift report to history"""
        history = []
        if os.path.exists(DRIFT_HISTORY_PATH):
            try:
                with open(DRIFT_HISTORY_PATH, "r") as f:
                    history = json.load(f)
            except:
                pass
        
        history.append(report)
        
        # Keep only last 100 reports
        if len(history) > 100:
            history = history[-100:]
        
        with open(DRIFT_HISTORY_PATH, "w") as f:
            json.dump(history, f, indent=2)
    
    def get_drift_history(self, limit=30):
        """Get drift history"""
        if not os.path.exists(DRIFT_HISTORY_PATH):
            return []
        
        try:
            with open(DRIFT_HISTORY_PATH, "r") as f:
                history = json.load(f)
            return history[-limit:]
        except:
            return []

if __name__ == "__main__":
    detector = DriftDetector()
    print("Checking for data drift...")
    report = detector.check_drift()
    print(json.dumps(report, indent=2))
