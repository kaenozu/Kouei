import pandas as pd
import numpy as np

try:
    from src.features.advanced_features import add_advanced_features, ADVANCED_FEATURES
    HAS_ADVANCED = True
except ImportError:
    HAS_ADVANCED = False
    ADVANCED_FEATURES = []

# Standard feature list used by the current model
FEATURES = [
    'jyo_cd', 'boat_no', 'racer_win_rate', 'motor_2ren', 'boat_2ren',
    'exhibition_time', 'tilt', 
    'temperature', 'water_temperature', 
    'wind_speed', 'wave_height', 
    'wind_direction', 'weather',
    'racer_win_rate_diff', 'motor_2ren_diff', 'exhibition_time_diff',
    # Course-based features
    'is_course_1', 'course_advantage',
    'is_inner_course', 'is_outer_course',
    'wind_course_interaction', 'motor_exhibition_ratio',
    # Racer course-specific features
    'racer_course_win_rate', 'racer_course_advantage',
    # Advanced features
    'racer_win_rate_rank', 'racer_win_rate_zscore',
    'motor_2ren_rank', 'motor_2ren_zscore',
    'course1_high_winrate', 'course6_high_winrate',
    'motor_exhibition_synergy',
    'rough_outer_advantage', 'calm_inner_advantage',
    'venue_inner_bias', 'venue_sashi_bias',
    'race_competitiveness', 'is_top_racer',
    # Course interaction features (new)
    'inner_threat', 'boat1_threat_level', 'upset_potential', 'st_advantage'
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
        df['exhibition_time'] = df['exhibition_time'].fillna(df['exhibition_time'].mean() if is_training else 6.80)
    
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
    if is_training and 'rank' in df.columns:
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

    # === NEW FEATURES ===
    # Course-based features (boat_no 1 has ~50% win rate, 6 has ~5%)
    COURSE_BASE_WIN_RATE = {1: 0.486, 2: 0.115, 3: 0.177, 4: 0.118, 5: 0.069, 6: 0.048}
    df['is_course_1'] = (df['boat_no'] == 1).astype(int)
    df['course_advantage'] = df['boat_no'].map(COURSE_BASE_WIN_RATE).fillna(0.1)
    df['is_inner_course'] = (df['boat_no'] <= 2).astype(int)  # 1,2 = inner
    df['is_outer_course'] = (df['boat_no'] >= 5).astype(int)  # 5,6 = outer
    
    # Wind-Course interaction (wind affects outer courses more)
    df['wind_course_interaction'] = df['wind_speed'] * (df['boat_no'] - 3.5)  # centered at 3.5
    
    # Motor-Exhibition ratio (good motor + fast exhibition = strong)
    df['motor_exhibition_ratio'] = df['motor_2ren'] / (df['exhibition_time'] + 0.1)
    
    # === RACER COURSE-SPECIFIC FEATURES ===
    df = add_racer_course_features(df)
    
    # === ADVANCED FEATURES ===
    if HAS_ADVANCED:
        df = add_advanced_features(df)
    
    # === COURSE INTERACTION FEATURES ===
    df = add_course_interaction_features(df)
    
    return df


# Racer course stats integration
def add_racer_course_features(df):
    """Add racer's course-specific win rate features"""
    try:
        from src.features.racer_course_stats import load_stats
        stats = load_stats()
    except:
        stats = {}
    
    BASELINE = {1: 0.486, 2: 0.114, 3: 0.178, 4: 0.118, 5: 0.069, 6: 0.048}
    
    df = df.copy()
    
    def get_course_win_rate(row):
        racer_id = str(row.get('racer_id', ''))
        course = str(int(row.get('boat_no', 1)))
        if racer_id in stats and course in stats[racer_id]:
            return stats[racer_id][course]
        return BASELINE.get(int(course), 0.1)
    
    df['racer_course_win_rate'] = df.apply(get_course_win_rate, axis=1)
    
    # Advantage over baseline
    df['racer_course_advantage'] = df.apply(
        lambda r: r['racer_course_win_rate'] - BASELINE.get(int(r['boat_no']), 0.1),
        axis=1
    )
    
    return df


def add_course_interaction_features(df):
    """Add course-specific interaction features for better prediction"""
    df = df.copy()
    
    # Initialize new columns
    df['inner_threat'] = 0.0
    df['boat1_threat_level'] = 0.0
    df['upset_potential'] = 0.0
    df['st_advantage'] = 0.0
    
    # Group by race
    for (date, jyo, race), group in df.groupby(['date', 'jyo_cd', 'race_no']):
        if len(group) < 3:
            continue
        
        idx = group.index
        
        # 1. Inner threat - strength of boats 2-4 (can challenge boat 1)
        inner_boats = group[group['boat_no'].isin([2, 3, 4])]
        if len(inner_boats) > 0:
            inner_threat = inner_boats['racer_win_rate'].mean()
            df.loc[idx, 'inner_threat'] = inner_threat
            
            # Boat 1's threat level (how much stronger are challengers)
            boat1 = group[group['boat_no'] == 1]
            if len(boat1) > 0:
                boat1_rate = boat1['racer_win_rate'].values[0]
                df.loc[boat1.index, 'boat1_threat_level'] = inner_threat - boat1_rate
        
        # 2. Upset potential - low win rate but good equipment
        motor_avg = group['motor_2ren'].mean() if group['motor_2ren'].mean() > 0 else 30
        boat_avg = group['boat_2ren'].mean() if group['boat_2ren'].mean() > 0 else 30
        equipment_score = (group['motor_2ren'] / motor_avg + group['boat_2ren'] / boat_avg) / 2
        df.loc[idx, 'upset_potential'] = equipment_score / (group['racer_win_rate'] / 5 + 0.5)
        
        # 3. ST advantage from exhibition time
        if 'exhibition_time' in group.columns:
            mean_ex = group['exhibition_time'].mean()
            if mean_ex > 0:
                df.loc[idx, 'st_advantage'] = (mean_ex - group['exhibition_time']) / 0.1
    
    return df
