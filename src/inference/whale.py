import os
import json
import logging
from datetime import datetime

CACHE_DIR = "data/odds_history"

class WhaleDetector:
    def __init__(self):
        os.makedirs(CACHE_DIR, exist_ok=True)

    def _get_path(self, race_id):
        return os.path.join(CACHE_DIR, f"{race_id}.json")

    def detect_abnormal_drop(self, race_id, current_odds_map, threshold_ratio=0.2):
        """
        Detects if odds dropped significantly since last check.
        current_odds_map: dict of {combo_str: odds_float}
        threshold_ratio: 0.2 means 20% drop (e.g. 10.0 -> 8.0)
        """
        path = self._get_path(race_id)
        
        alerts = []
        history = {}
        
        if os.path.exists(path):
            try:
                with open(path, 'r') as f:
                    history = json.load(f)
            except:
                pass
        
        # Compare
        last_odds = history.get("latest", {})
        
        if last_odds:
            for combo, curr_val in current_odds_map.items():
                prev_val = last_odds.get(combo)
                if prev_val:
                    # Check drop
                    # Drop means curr < prev
                    if curr_val < prev_val:
                        ratio = (prev_val - curr_val) / prev_val
                        if ratio >= threshold_ratio:
                            # Whale Detected!
                            alerts.append({
                                "combo": combo,
                                "prev": prev_val,
                                "curr": curr_val,
                                "drop_pct": ratio * 100
                            })
        
        # Save current as latest
        history["latest"] = current_odds_map
        history["updated_at"] = datetime.now().isoformat()
        
        with open(path, 'w') as f:
            json.dump(history, f)
            
        return alerts
