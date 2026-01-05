"""Advanced feature engineering for improved prediction"""
import pandas as pd
import numpy as np
from typing import Dict, Optional

def add_advanced_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add advanced features to improve prediction accuracy"""
    df = df.copy()
    
    # 1. レース内の相対的な強さ
    for col in ['racer_win_rate', 'motor_2ren', 'boat_2ren']:
        if col in df.columns:
            # レース内での順位 (1が最高)
            df[f'{col}_rank'] = df.groupby(['date', 'jyo_cd', 'race_no'])[col].rank(ascending=False)
            # レース内での偏差
            race_mean = df.groupby(['date', 'jyo_cd', 'race_no'])[col].transform('mean')
            race_std = df.groupby(['date', 'jyo_cd', 'race_no'])[col].transform('std').replace(0, 1)
            df[f'{col}_zscore'] = (df[col] - race_mean) / race_std
    
    # 2. コース×勝率の交互作用
    if 'boat_no' in df.columns and 'racer_win_rate' in df.columns:
        # 1コースの高勝率選手は特に有利
        df['course1_high_winrate'] = ((df['boat_no'] == 1) & (df['racer_win_rate'] > 6)).astype(int)
        # 6コースの高勝率選手（穴）
        df['course6_high_winrate'] = ((df['boat_no'] == 6) & (df['racer_win_rate'] > 5.5)).astype(int)
    
    # 3. モーター×展示タイムの相乗効果
    if 'motor_2ren' in df.columns and 'exhibition_time' in df.columns:
        # 高モーター勝率 & 良い展示タイム
        motor_good = df['motor_2ren'] > df.groupby(['date', 'jyo_cd', 'race_no'])['motor_2ren'].transform('median')
        exhibition_good = df['exhibition_time'] < df.groupby(['date', 'jyo_cd', 'race_no'])['exhibition_time'].transform('median')
        df['motor_exhibition_synergy'] = (motor_good & exhibition_good).astype(int)
    
    # 4. 風と波の影響（アウトコース有利条件）
    if 'wind_speed' in df.columns and 'wave_height' in df.columns and 'boat_no' in df.columns:
        # 強風・高波はアウトコース有利
        rough_condition = (df['wind_speed'] > 4) | (df['wave_height'] > 3)
        df['rough_outer_advantage'] = (rough_condition & (df['boat_no'] >= 4)).astype(int)
        df['calm_inner_advantage'] = (~rough_condition & (df['boat_no'] <= 2)).astype(int)
    
    # 5. 会場特性
    if 'jyo_cd' in df.columns and 'boat_no' in df.columns:
        # インが強い会場 (桐生、戸田など)
        inner_strong_venues = [1, 2, 4, 5]  # 桐生、戸田、平和島、多摩川
        df['venue_inner_bias'] = (df['jyo_cd'].isin(inner_strong_venues) & (df['boat_no'] <= 2)).astype(int)
        
        # 差しが決まりやすい会場 (住之江、尼崎など)
        sashi_venues = [12, 15]  # 住之江、尼崎
        df['venue_sashi_bias'] = (df['jyo_cd'].isin(sashi_venues) & (df['boat_no'].isin([2, 3, 4]))).astype(int)
    
    # 6. 選手の実力差
    if 'racer_win_rate' in df.columns:
        race_max = df.groupby(['date', 'jyo_cd', 'race_no'])['racer_win_rate'].transform('max')
        race_min = df.groupby(['date', 'jyo_cd', 'race_no'])['racer_win_rate'].transform('min')
        df['race_competitiveness'] = race_max - race_min
        df['is_top_racer'] = (df['racer_win_rate'] == race_max).astype(int)
    
    # NaN処理
    df = df.fillna(0)
    
    return df


# 新しい特徴量リスト
ADVANCED_FEATURES = [
    'racer_win_rate_rank', 'racer_win_rate_zscore',
    'motor_2ren_rank', 'motor_2ren_zscore', 
    'boat_2ren_rank', 'boat_2ren_zscore',
    'course1_high_winrate', 'course6_high_winrate',
    'motor_exhibition_synergy',
    'rough_outer_advantage', 'calm_inner_advantage',
    'venue_inner_bias', 'venue_sashi_bias',
    'race_competitiveness', 'is_top_racer'
]

# Additional features for improvement
def add_course_interaction_features(df):
    """Add course-specific interaction features"""
    df = df.copy()
    
    # 1号艇の脅威度（2-4号艇の強さ）
    for (date, jyo, race), group in df.groupby(['date', 'jyo_cd', 'race_no']):
        if len(group) < 6:
            continue
        
        boat1 = group[group['boat_no'] == 1]
        if len(boat1) == 0:
            continue
        
        # 2-4号艇の平均勝率
        inner_boats = group[group['boat_no'].isin([2, 3, 4])]
        if len(inner_boats) > 0:
            threat = inner_boats['racer_win_rate'].mean()
            df.loc[group.index, 'inner_threat'] = threat
            df.loc[boat1.index, 'boat1_threat_level'] = threat - boat1['racer_win_rate'].values[0]
    
    # 穴馬指数（低勝率選手の期待値）
    df['upset_potential'] = (df['motor_2ren'] * 0.5 + df['boat_2ren'] * 0.5) / (df['racer_win_rate'] + 1)
    
    return df

def add_st_prediction_features(df):
    """Add start timing prediction features (simplified)"""
    df = df.copy()
    
    # 展示タイムからSTを推定
    if 'exhibition_time' in df.columns:
        # 展示タイムが速い=ST良い傾向
        mean_ex = df.groupby(['date', 'jyo_cd', 'race_no'])['exhibition_time'].transform('mean')
        df['st_advantage'] = (mean_ex - df['exhibition_time']) / 0.1  # 0.1秒差で1ポイント
    
    return df

EXTRA_FEATURES = [
    'inner_threat', 'boat1_threat_level', 'upset_potential', 'st_advantage'
]
