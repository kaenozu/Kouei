"""
Venue Event Scoring
Analyzes historical race data to calculate Bias Scores for each stadium.
Example: Strength of Boat 1 (Escaping), Influence of Wind on Turn 1 results.
"""
import pandas as pd
import os
import json

DATA_PATH = "data/processed/race_data.csv"
VENUE_STATS_PATH = "models/venue_stats.json"

class VenueScorer:
    def __init__(self, data_path=DATA_PATH):
        self.data_path = data_path

    def calculate_scores(self):
        if not os.path.exists(self.data_path):
            return {}
            
        df = pd.read_csv(self.data_path)
        if df.empty: return {}
        
        # We need 'rank' and 'boat_no'
        if 'rank' not in df.columns or 'boat_no' not in df.columns:
            return {}
            
        # Calculate win rate for Boat 1 per stadium (In-Escape strength)
        stadium_stats = {}
        
        for jyo, group in df.groupby('jyo_cd'):
            # Identification of unique races: (date, jyo_cd, race_no)
            # Since we are already grouped by jyo_cd, we count unique (date, race_no)
            unique_races = group.drop_duplicates(subset=['date', 'race_no'])
            total_races = len(unique_races)
            
            if total_races < 10: continue # Lowered threshold for test data
            
            # Win count for Boat 1
            boat1_wins = group[(group['boat_no'] == 1) & (group['rank'] == 1)].shape[0]
            escape_rate = boat1_wins / total_races if total_races > 0 else 0
            
            # Influence of wind - (Placeholder logic: correlation between wind and boat 1 win)
            # 1: Strong escape stadium, 0: Weak
            stadium_stats[str(jyo).zfill(2)] = {
                "escape_rate": round(escape_rate, 3),
                "in_strength": "High" if escape_rate > 0.55 else "Normal" if escape_rate > 0.45 else "Low",
                "sample_size": total_races,
                "bias_score": round((escape_rate - 0.5) * 10, 1) # Relative to avg
            }
            
        with open(VENUE_STATS_PATH, "w") as f:
            json.dump(stadium_stats, f, indent=4)
            
        print(f"✅ Venue scores updated: {VENUE_STATS_PATH}")
        return stadium_stats

if __name__ == "__main__":
    scorer = VenueScorer()
    stats = scorer.calculate_scores()
    print(json.dumps(stats, indent=2))
