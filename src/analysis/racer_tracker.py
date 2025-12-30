import pandas as pd
import sys
import os
sys.path.append(os.getcwd())
from src.db.database import DatabaseData

class RacerTracker:
    def __init__(self):
        self.db = DatabaseData()

    def get_racer_stats(self, racer_id: str, n_races: int = 10):
        """
        Get recent performance for a specific racer.
        
        Returns:
        - recent_races: list of recent race results
        - win_rate: percentage
        - avg_st: average start timing
        - motor_compatibility: best motors used
        """
        df = self.db.load_df()
        
        # Filter by racer
        racer_df = df[df['racer_id'] == racer_id].copy()
        
        if len(racer_df) == 0:
            return {'error': 'Racer not found'}
        
        # Sort by date desc
        racer_df['date'] = pd.to_datetime(racer_df['date'].astype(str), format='%Y%m%d', errors='coerce')
        racer_df = racer_df.sort_values('date', ascending=False)
        
        # Recent races
        recent = racer_df.head(n_races)
        
        # Calculate stats
        wins = len(recent[recent['rank'] == 1])
        win_rate = wins / len(recent) * 100 if len(recent) > 0 else 0
        
        # Avg ST
        if 'start_time_result' in recent.columns:
            avg_st = recent['start_time_result'].mean()
        else:
            avg_st = None
        
        # Motor compatibility
        motor_stats = racer_df.groupby('motor_no').agg({
            'rank': lambda x: (x == 1).sum() / len(x) * 100  # Win rate per motor
        }).sort_values('rank', ascending=False)
        
        best_motors = motor_stats.head(3).to_dict()['rank']
        
        # Recent race details
        race_list = []
        for _, row in recent.iterrows():
            race_list.append({
                'date': row['date'].strftime('%Y-%m-%d') if pd.notna(row['date']) else 'N/A',
                'jyo': row.get('jyo_cd', 'N/A'),
                'race_no': row.get('race_no', 'N/A'),
                'boat_no': row.get('boat_no', 'N/A'),
                'rank': row.get('rank', 'N/A'),
                'motor_no': row.get('motor_no', 'N/A'),
                'st': row.get('start_time_result', 'N/A')
            })
        
        return {
            'racer_id': racer_id,
            'racer_name': recent.iloc[0].get('racer_name', 'Unknown') if len(recent) > 0 else 'Unknown',
            'total_races_in_db': len(racer_df),
            'recent_n': n_races,
            'win_rate': round(win_rate, 2),
            'avg_st': round(avg_st, 2) if avg_st else None,
            'best_motors': best_motors,
            'recent_races': race_list
        }

if __name__ == "__main__":
    tracker = RacerTracker()
    print("Racer Tracker Ready")
