"""Enhanced feature engineering with advanced ML techniques"""
import pandas as pd
import numpy as np
from typing import List, Dict

def add_enhanced_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add enhanced features for better prediction accuracy"""
    df = df.copy()
    
    # 1. タイムベンド相互作用（タイム差とモーター性能）
    if all(col in df.columns for col in ['exhibition_time', 'motor_2ren']):
        df['time_bend_ratio'] = df['motor_2ren'] / (df['exhibition_time'] ** 2 + 1)
    
    # 2. 風向きとコースの複雑な相互作用
    if all(col in df.columns for col in ['wind_direction', 'boat_no']):
        # 風向きを8方位に変換
        wind_dir_rad = np.radians(df['wind_direction'] * 45)  # 0-7度をラジアンに
        course_pos = df['boat_no']  # 1-6
        df['wind_course_complex'] = np.sin(wind_dir_rad) * (course_pos - 3.5)
    
    # 3. 気温と水温の相互作用（パフォーマンスへの影響）
    if all(col in df.columns for col in ['temperature', 'water_temperature']):
        df['temp_diff'] = df['temperature'] - df['water_temperature']
        df['optimal_conditions'] = ((10 <= df['water_temperature']) & (df['water_temperature'] <= 30)).astype(int)
    
    # 4. 選手の最近の成績トレンド
    if 'racer_win_rate' in df.columns:
        # 勝率の変動性（標準偏差が大きいと不安定）
        df['racer_consistency'] = df.groupby(['date', 'jyo_cd', 'race_no'])['racer_win_rate'].transform('std')
        df['racer_consistency'] = df['racer_consistency'].fillna(0)
    
    # 5. モーターとボートの相乗効果
    if all(col in df.columns for col in ['motor_2ren', 'boat_2ren']):
        df['motor_boat_harmony'] = np.sqrt(df['motor_2ren'] * df['boat_2ren'])
    
    # 6. 波高のコース別影響
    if all(col in df.columns for col in ['wave_height', 'boat_no']):
        df['wave_outer_advantage'] = (df['wave_height'] > 2) * (df['boat_no'] >= 4)
    
    # 7. 天候複合スコア
    if all(col in df.columns for col in ['weather', 'wind_speed', 'wave_height']):
        # 晴天(0)かつ風速2-4m/sかつ波高1-2cmが最適
        weather_good = (df['weather'] == 0) | (df['weather'] == 1)
        wind_optimal = (df['wind_speed'] >= 2) & (df['wind_speed'] <= 4)
        wave_optimal = (df['wave_height'] >= 1) & (df['wave_height'] <= 2)
        df['weather_optimal'] = (weather_good & wind_optimal & wave_optimal).astype(int)
    
    # 8. ピット率の重要性
    if 'racer_win_rate' in df.columns:
        df['racer_winning_tendency'] = df['racer_win_rate'] * df.get('racer_course_advantage', 0)
    
    return df

ENHANCED_FEATURES = [
    'time_bend_ratio', 'wind_course_complex', 
    'temp_diff', 'optimal_conditions',
    'racer_consistency', 'motor_boat_harmony',
    'wave_outer_advantage', 'weather_optimal',
    'racer_winning_tendency'
]
