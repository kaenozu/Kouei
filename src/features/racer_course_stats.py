"""
Racer course statistics calculator
Calculates each racer's win rate by course position
"""
import pandas as pd
import numpy as np
import os
import json
from datetime import datetime

STATS_FILE = "data/racer_course_stats.json"

def calculate_racer_course_stats(df: pd.DataFrame, min_races: int = 5) -> dict:
    """
    Calculate win rate by course for each racer
    
    Args:
        df: DataFrame with race data
        min_races: Minimum races required for reliable stats
        
    Returns:
        dict: {racer_id: {course: win_rate, ...}, ...}
    """
    df = df.copy()
    df['rank'] = pd.to_numeric(df['rank'], errors='coerce')
    df = df.dropna(subset=['rank', 'racer_id', 'boat_no'])
    df['racer_id'] = df['racer_id'].astype(str)
    df['boat_no'] = df['boat_no'].astype(int)
    
    stats = {}
    
    # Group by racer and course
    for (racer_id, course), group in df.groupby(['racer_id', 'boat_no']):
        if len(group) < min_races:
            continue
            
        win_rate = (group['rank'] == 1).mean()
        
        if racer_id not in stats:
            stats[racer_id] = {}
        stats[racer_id][str(course)] = round(win_rate, 4)
    
    return stats


def save_stats(stats: dict):
    """Save stats to JSON file"""
    os.makedirs(os.path.dirname(STATS_FILE), exist_ok=True)
    with open(STATS_FILE, 'w') as f:
        json.dump({
            'updated': datetime.now().isoformat(),
            'stats': stats
        }, f)
    print(f"Saved racer course stats to {STATS_FILE}")


def load_stats() -> dict:
    """Load stats from JSON file"""
    if not os.path.exists(STATS_FILE):
        return {}
    with open(STATS_FILE, 'r') as f:
        data = json.load(f)
    return data.get('stats', {})


def get_racer_course_win_rate(racer_id: str, course: int, stats: dict = None) -> float:
    """
    Get win rate for a specific racer at a specific course
    
    Returns:
        float: Win rate (0-1) or None if no data
    """
    if stats is None:
        stats = load_stats()
    
    racer_id = str(racer_id)
    course = str(course)
    
    if racer_id in stats and course in stats[racer_id]:
        return stats[racer_id][course]
    return None


def add_racer_course_features(df: pd.DataFrame, stats: dict = None) -> pd.DataFrame:
    """
    Add racer course-specific features to dataframe
    
    New columns:
    - racer_course_win_rate: This racer's win rate at this course
    - racer_course_advantage: Win rate compared to baseline for this course
    """
    if stats is None:
        stats = load_stats()
    
    # Baseline win rates by course
    BASELINE = {1: 0.486, 2: 0.114, 3: 0.178, 4: 0.118, 5: 0.069, 6: 0.048}
    
    df = df.copy()
    df['racer_id'] = df['racer_id'].astype(str)
    df['boat_no'] = df['boat_no'].astype(int)
    
    def get_course_win_rate(row):
        racer_id = str(row['racer_id'])
        course = str(int(row['boat_no']))
        if racer_id in stats and course in stats[racer_id]:
            return stats[racer_id][course]
        return None
    
    def get_course_advantage(row):
        win_rate = row.get('racer_course_win_rate')
        course = int(row['boat_no'])
        baseline = BASELINE.get(course, 0.1)
        if win_rate is not None:
            return win_rate - baseline
        return 0.0
    
    df['racer_course_win_rate'] = df.apply(get_course_win_rate, axis=1)
    df['racer_course_win_rate'] = df['racer_course_win_rate'].fillna(
        df['boat_no'].map(BASELINE)
    )
    df['racer_course_advantage'] = df.apply(get_course_advantage, axis=1)
    
    return df


if __name__ == "__main__":
    # Build stats from current data
    import pandas as pd
    
    DATA_PATH = "data/processed/race_data.csv"
    if os.path.exists(DATA_PATH):
        print("Loading data...")
        df = pd.read_csv(DATA_PATH)
        print(f"Loaded {len(df)} rows")
        
        print("Calculating racer course stats...")
        stats = calculate_racer_course_stats(df, min_races=3)
        print(f"Calculated stats for {len(stats)} racers")
        
        save_stats(stats)
        
        # Show some examples
        print("\nSample stats:")
        for racer_id in list(stats.keys())[:3]:
            print(f"  Racer {racer_id}: {stats[racer_id]}")
