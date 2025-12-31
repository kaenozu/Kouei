import pandas as pd
import sys
import os
import numpy as np
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
        
        # Handle NaN values in the dataframe
        if not racer_df.empty:
            racer_df = racer_df.fillna({'racer_name': 'N/A', 'start_time_result': 0})
            # Fill other numeric columns with 0
            numeric_cols = racer_df.select_dtypes(include=[np.number]).columns
            racer_df[numeric_cols] = racer_df[numeric_cols].fillna(0)
        
        if len(racer_df) == 0:
            return {'error': 'Racer not found'}
        
        # Sort by date desc
        racer_df['date'] = pd.to_datetime(racer_df['date'].astype(str), format='%Y%m%d', errors='coerce')
        racer_df = racer_df.sort_values('date', ascending=False)
        
        # Recent races
        recent = racer_df.head(n_races)
        
        # Calculate stats
        # Handle case where 'rank' column might be named 'result_rank'
        rank_col = 'rank' if 'rank' in recent.columns else 'result_rank' if 'result_rank' in recent.columns else None
        if rank_col:
            wins = len(recent[recent[rank_col] == 1])
            win_rate = wins / len(recent) * 100 if len(recent) > 0 else 0
        else:
            wins = 0
            win_rate = 0
        
        # Avg ST
        if 'start_time_result' in recent.columns:
            avg_st = recent['start_time_result'].mean()
            # Handle NaN values for JSON compliance
            if pd.isna(avg_st) or (isinstance(avg_st, float) and (np.isnan(avg_st) or np.isinf(avg_st))):
                avg_st = None
            # Additional check for any remaining NaN values
            if isinstance(avg_st, float) and np.isnan(avg_st):
                avg_st = None
        else:
            avg_st = None
        
        # Motor compatibility
        # Handle case where 'rank' column might be named 'result_rank'
        rank_col_for_motor = 'rank' if 'rank' in racer_df.columns else 'result_rank' if 'result_rank' in racer_df.columns else None
        if rank_col_for_motor:
            motor_stats = racer_df.groupby('motor_no').agg({
                rank_col_for_motor: lambda x: (x == 1).sum() / len(x) * 100  # Win rate per motor
            }).sort_values(rank_col_for_motor, ascending=False)
        else:
            motor_stats = pd.DataFrame()
        
        best_motors = motor_stats.head(3).to_dict()[rank_col_for_motor] if not motor_stats.empty else {}
        
        # Recent race details
        race_list = []
        for _, row in recent.iterrows():
            # Create race entry with default values
            race_entry = {
                'date': row['date'].strftime('%Y-%m-%d') if pd.notna(row['date']) else 'N/A',
                'jyo': row.get('jyo_cd', 'N/A'),
                'race_no': row.get('race_no', 'N/A'),
                'boat_no': row.get('boat_no', 'N/A'),
                'rank': row.get(rank_col, 'N/A') if rank_col else 'N/A',
                'motor_no': row.get('motor_no', 'N/A'),
                'st': row.get('start_time_result', 'N/A')
            }
            
            # Ensure all float values are JSON compliant
            for key, value in race_entry.items():
                if isinstance(value, float) and (np.isnan(value) or np.isinf(value)):
                    race_entry[key] = None
                elif pd.isna(value):
                    race_entry[key] = None
            
            race_list.append(race_entry)
        
        # Ensure all numeric values are JSON compliant
        win_rate_safe = round(win_rate, 2) if not pd.isna(win_rate) else 0.0
        avg_st_safe = round(avg_st, 2) if avg_st and not pd.isna(avg_st) else None
        
        # Handle best_motors to ensure no NaN values
        best_motors_safe = {}
        for motor, value in best_motors.items():
            if not (pd.isna(value) or np.isnan(value) or np.isinf(value)):
                best_motors_safe[motor] = round(value, 2)
        
        # Ensure recent_races values are JSON compliant
        for race in race_list:
            for key, value in race.items():
                if isinstance(value, float) and (np.isnan(value) or np.isinf(value)):
                    race[key] = None
        
        return {
            'racer_id': racer_id,
            'racer_name': recent.iloc[0].get('racer_name', 'Unknown') if len(recent) > 0 else 'Unknown',
            'total_races_in_db': len(racer_df),
            'recent_n': n_races,
            'win_rate': win_rate_safe,
            'avg_st': avg_st_safe,
            'best_motors': best_motors_safe,
            'recent_races': race_list
        }

if __name__ == "__main__":
    tracker = RacerTracker()
    print("Racer Tracker Ready")
