import pandas as pd
import numpy as np

try:
    from src.features.advanced_features import add_advanced_features, ADVANCED_FEATURES
    HAS_ADVANCED = True
except ImportError:
    HAS_ADVANCED = False
    ADVANCED_FEATURES = []

try:
    from src.features.seasonal_features import add_seasonal_features, SEASONAL_FEATURES
    HAS_SEASONAL = True
except ImportError:
    HAS_SEASONAL = False
    SEASONAL_FEATURES = []

# Standard feature list used by the current model
# Model-compatible features (41 features)
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
    # Course interaction features
    'inner_threat', 'boat1_threat_level', 'upset_potential', 'st_advantage'
]

# Extended features for V2 model (train with train_v2.py)
FEATURES_V2 = FEATURES + [
    # V2 matchup features
    'avg_opponent_winrate', 'winrate_advantage', 'is_top_racer_in_race',
    'motor_venue_advantage', 'boat_venue_advantage', 'equipment_score', 'equipment_rank',
    'is_final', 'is_semifinal', 'is_sg', 'race_importance',
    # V2 連単 features
    'base_2nd_rate', 'adjusted_2nd_prob', 'rentai_power', 'sanrentai_power',
    'wind_course_benefit', 'rough_water_penalty'
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
    
    # === SEASONAL FEATURES ===
    if HAS_SEASONAL:
        df = add_seasonal_features(df)
    
    # === COURSE INTERACTION FEATURES ===
    df = add_course_interaction_features(df)
    
    # === RACER MATCHUP FEATURES ===
    df = add_racer_matchup_features(df)
    
    # === MOTOR/BOAT FEATURES ===
    df = add_motor_boat_features(df)
    
    # === RACE TYPE FEATURES ===
    df = add_race_type_features(df)
    
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


def add_racer_matchup_features(df):
    """Add racer matchup features - how racers perform against each other"""
    df = df.copy()
    
    # Initialize
    df['avg_opponent_winrate'] = 0.0
    df['winrate_advantage'] = 0.0
    df['is_top_racer_in_race'] = 0
    
    for (date, jyo, race), group in df.groupby(['date', 'jyo_cd', 'race_no']):
        if len(group) < 3:
            continue
        
        idx = group.index
        winrates = group['racer_win_rate'].values
        avg_winrate = winrates.mean()
        max_winrate = winrates.max()
        
        for i, row_idx in enumerate(idx):
            # Average opponent win rate
            opponents = [w for j, w in enumerate(winrates) if j != i]
            df.loc[row_idx, 'avg_opponent_winrate'] = sum(opponents) / len(opponents) if opponents else 0
            
            # Win rate advantage over average
            df.loc[row_idx, 'winrate_advantage'] = winrates[i] - avg_winrate
            
            # Is top racer in race
            df.loc[row_idx, 'is_top_racer_in_race'] = 1 if winrates[i] == max_winrate else 0
    
    return df


def add_motor_boat_features(df):
    """Add motor and boat specific features"""
    df = df.copy()
    
    # Motor performance relative to venue average
    if 'motor_2ren' in df.columns and 'jyo_cd' in df.columns:
        venue_motor_avg = df.groupby('jyo_cd')['motor_2ren'].transform('mean')
        df['motor_venue_advantage'] = df['motor_2ren'] - venue_motor_avg
    
    # Boat performance relative to venue average
    if 'boat_2ren' in df.columns and 'jyo_cd' in df.columns:
        venue_boat_avg = df.groupby('jyo_cd')['boat_2ren'].transform('mean')
        df['boat_venue_advantage'] = df['boat_2ren'] - venue_boat_avg
    
    # Combined equipment score
    df['equipment_score'] = (
        df.get('motor_2ren', 0).fillna(30) * 0.6 + 
        df.get('boat_2ren', 0).fillna(30) * 0.4
    )
    
    # Equipment rank in race
    for (date, jyo, race), group in df.groupby(['date', 'jyo_cd', 'race_no']):
        idx = group.index
        ranks = group['equipment_score'].rank(ascending=False)
        df.loc[idx, 'equipment_rank'] = ranks
    
    return df


def add_race_type_features(df):
    """Add race type features (予選, 準決, 決勝, SG, etc.)"""
    df = df.copy()
    
    df['is_final'] = 0
    df['is_semifinal'] = 0
    df['is_sg'] = 0
    df['race_importance'] = 1.0
    
    if 'race_name' in df.columns:
        race_names = df['race_name'].astype(str).str.lower()
        
        # Finals
        df.loc[race_names.str.contains('優勝|決勝|ファイナル', na=False), 'is_final'] = 1
        df.loc[df['is_final'] == 1, 'race_importance'] = 2.0
        
        # Semi-finals
        df.loc[race_names.str.contains('準決|準優|セミ', na=False), 'is_semifinal'] = 1
        df.loc[df['is_semifinal'] == 1, 'race_importance'] = 1.5
        
        # SG races
        df.loc[race_names.str.contains('sg|グランプリ|クラシック|オールスター|メモリアル|ダービー', na=False), 'is_sg'] = 1
        df.loc[df['is_sg'] == 1, 'race_importance'] = 2.5
    
    return df


# Update FEATURES list
EXTRA_FEATURES_V2 = [
    'avg_opponent_winrate', 'winrate_advantage', 'is_top_racer_in_race',
    'motor_venue_advantage', 'boat_venue_advantage', 'equipment_score', 'equipment_rank',
    'is_final', 'is_semifinal', 'is_sg', 'race_importance'
]

# Seasonal features for V3 model
SEASONAL_FEATURES_LIST = [
    'month', 'is_winter', 'is_spring', 'is_summer', 'is_autumn',
    'temp_deviation', 'temp_zscore_seasonal', 'water_temp_deviation',
    'temp_venue_adjusted', 'temp_anomaly', 'winter_outer_advantage',
    'summer_speed_factor', 'temp_exhibition_interaction'
]
