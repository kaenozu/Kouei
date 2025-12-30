import pandas as pd
import numpy as np

# Standard feature list used by the current model
FEATURES = [
    'jyo_cd', 'boat_no', 'racer_win_rate', 'motor_2ren', 'boat_2ren',
    'exhibition_time', 'tilt', 
    'temperature', 'water_temperature', 
    'wind_speed', 'wave_height', 
    'wind_direction', 'weather',
    'racer_win_rate_diff', 'motor_2ren_diff', 'exhibition_time_diff'
]

CAT_FEATURES = ['jyo_cd', 'boat_no', 'wind_direction', 'weather']

def preprocess(df, is_training=False):
    """
    Centralized preprocessing for Boat Race data.
    Works for both training (with target) and inference.
    """
    # Create a copy to avoid modifying the original dataframe
    df = df.copy()
    
    # Convert numeric columns
    numeric_cols = [
        'racer_win_rate', 'motor_2ren', 'boat_2ren', 'exhibition_time', 
        'wind_speed', 'wave_height', 'temperature', 'water_temperature', 'tilt'
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        else:
            df[col] = 0.0
    
    # Fill NAs
    # Exhibition time is better filled with something realistic if possible
    # In training we use the global mean, in inference we should ideally use the race average 
    # but as a fallback we use a typical value or global mean.
    if 'exhibition_time' in df.columns:
        df['exhibition_time'] = df['exhibition_time'].fillna(df['exhibition_time'].mean() if training else 6.80)
    
    df[numeric_cols] = df[numeric_cols].fillna(0)
    
    # Categorical columns
    if 'jyo_cd' in df.columns:
        df['jyo_cd'] = pd.to_numeric(df['jyo_cd'], errors='coerce').fillna(0).astype(int)
    else:
        df['jyo_cd'] = 0
        
    if 'boat_no' in df.columns:
        df['boat_no'] = pd.to_numeric(df['boat_no'], errors='coerce').fillna(0).astype(int)
        
    if 'wind_direction' in df.columns:
        df['wind_direction'] = pd.to_numeric(df['wind_direction'], errors='coerce').fillna(-1).astype(int)
    else:
        df['wind_direction'] = -1
        
    if 'weather' in df.columns:
        df['weather'] = pd.to_numeric(df['weather'], errors='coerce').fillna(-1).astype(int)
    else:
        df['weather'] = -1

    # Target (only for training)
    if training and 'rank' in df.columns:
        df['rank'] = pd.to_numeric(df['rank'], errors='coerce')
        df['target'] = (df['rank'] == 1).astype(int)
        # Filter out rows where rank is NaN
        df = df.dropna(subset=['rank'])

    # Add Relative Features (Difference from race average)
    if all(col in df.columns for col in ['date', 'jyo_cd', 'race_no']):
        race_groups = df.groupby(['date', 'jyo_cd', 'race_no'])
        
        # Win Rate Diff
        df['win_rate_avg'] = race_groups['racer_win_rate'].transform('mean')
        df['racer_win_rate_diff'] = df['racer_win_rate'] - df['win_rate_avg']
        
        # Motor Diff
        df['motor_2ren_avg'] = race_groups['motor_2ren'].transform('mean')
        df['motor_2ren_diff'] = df['motor_2ren'] - df['motor_2ren_avg']
        
        # Exhibition Time Diff
        df['exh_time_avg'] = race_groups['exhibition_time'].transform('mean')
        df['exhibition_time_diff'] = df['exhibition_time'] - df['exh_time_avg']
    else:
        # Fallback if race keys are missing (should not happen in proper usage)
        df['racer_win_rate_diff'] = 0.0
        df['motor_2ren_diff'] = 0.0
        df['exhibition_time_diff'] = 0.0

    return df
