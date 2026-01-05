"""Advanced Feature Engineering V2 - Enhanced prediction features"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import json
import os

# ===== 1. 選手の直近フォーム =====
def add_recent_form_features(df: pd.DataFrame, lookback_days: int = 14) -> pd.DataFrame:
    """選手の直近フォームを特徴量に追加"""
    df = df.copy()
    
    # 日付でソート
    if 'date' in df.columns:
        df['date_dt'] = pd.to_datetime(df['date'].astype(str), format='%Y%m%d', errors='coerce')
        df = df.sort_values('date_dt')
    
    # 選手別の直近成績（簡易版）
    if 'racer_id' in df.columns and 'rank' in df.columns:
        df['rank_num'] = pd.to_numeric(df['rank'], errors='coerce')
        # 直近の平均着順（全体）
        df['recent_avg_rank'] = df.groupby('racer_id')['rank_num'].transform(
            lambda x: x.rolling(window=12, min_periods=1).mean().shift(1)
        ).fillna(3.5)
        
        # 直近1着率
        df['recent_win_count'] = df.groupby('racer_id')['rank_num'].transform(
            lambda x: (x == 1).rolling(window=12, min_periods=1).sum().shift(1)
        ).fillna(0)
        df['recent_win_rate'] = df['recent_win_count'] / 12
        
        # 連対率（2着以内）
        df['recent_rentai_count'] = df.groupby('racer_id')['rank_num'].transform(
            lambda x: (x <= 2).rolling(window=12, min_periods=1).sum().shift(1)
        ).fillna(0)
        df['recent_rentai_rate'] = df['recent_rentai_count'] / 12
    else:
        df['recent_avg_rank'] = 3.5
        df['recent_win_rate'] = 0.0
        df['recent_rentai_rate'] = 0.0
    
    return df


# ===== 2. 選手×会場の相性 =====
def add_venue_affinity_features(df: pd.DataFrame) -> pd.DataFrame:
    """選手×会場の相性特徴量"""
    df = df.copy()
    
    if 'racer_id' in df.columns and 'jyo_cd' in df.columns and 'rank' in df.columns:
        df['rank_num'] = pd.to_numeric(df['rank'], errors='coerce')
        
        # 選手×会場の過去成績
        venue_stats = df.groupby(['racer_id', 'jyo_cd']).agg({
            'rank_num': ['mean', 'count', lambda x: (x == 1).sum()]
        }).reset_index()
        venue_stats.columns = ['racer_id', 'jyo_cd', 'venue_avg_rank', 'venue_race_count', 'venue_win_count']
        venue_stats['venue_win_rate'] = venue_stats['venue_win_count'] / venue_stats['venue_race_count'].clip(lower=1)
        
        # マージ
        df = df.merge(
            venue_stats[['racer_id', 'jyo_cd', 'venue_avg_rank', 'venue_win_rate']],
            on=['racer_id', 'jyo_cd'],
            how='left'
        )
        df['venue_avg_rank'] = df['venue_avg_rank'].fillna(3.5)
        df['venue_win_rate'] = df['venue_win_rate'].fillna(df['racer_win_rate'] / 10 if 'racer_win_rate' in df.columns else 0.15)
        
        # 会場との相性スコア
        df['venue_affinity'] = (df['venue_win_rate'] - 0.166) * 6  # 正規化
    else:
        df['venue_avg_rank'] = 3.5
        df['venue_win_rate'] = 0.166
        df['venue_affinity'] = 0.0
    
    return df


# ===== 3. モーターの会場適性 =====
def add_motor_venue_features(df: pd.DataFrame) -> pd.DataFrame:
    """モーターの会場での成績"""
    df = df.copy()
    
    if 'motor_no' in df.columns and 'jyo_cd' in df.columns and 'rank' in df.columns:
        df['rank_num'] = pd.to_numeric(df['rank'], errors='coerce')
        
        # モーター×会場の成績
        motor_stats = df.groupby(['motor_no', 'jyo_cd']).agg({
            'rank_num': ['mean', 'count']
        }).reset_index()
        motor_stats.columns = ['motor_no', 'jyo_cd', 'motor_venue_avg_rank', 'motor_venue_count']
        
        df = df.merge(
            motor_stats[['motor_no', 'jyo_cd', 'motor_venue_avg_rank']],
            on=['motor_no', 'jyo_cd'],
            how='left'
        )
        df['motor_venue_avg_rank'] = df['motor_venue_avg_rank'].fillna(3.5)
        df['motor_venue_advantage'] = 3.5 - df['motor_venue_avg_rank']
    else:
        df['motor_venue_avg_rank'] = 3.5
        df['motor_venue_advantage'] = 0.0
    
    return df


# ===== 4. スタートタイミング特徴 =====
def add_start_timing_features(df: pd.DataFrame) -> pd.DataFrame:
    """スタートタイミング関連特徴量"""
    df = df.copy()
    
    if 'start_time_result' in df.columns:
        df['st_result'] = pd.to_numeric(df['start_time_result'], errors='coerce').fillna(0.15)
    else:
        df['st_result'] = 0.15
    
    # コース別の平均ST
    if 'racer_id' in df.columns and 'boat_no' in df.columns:
        # 選手のコース別平均ST
        st_stats = df.groupby(['racer_id', 'boat_no'])['st_result'].mean().reset_index()
        st_stats.columns = ['racer_id', 'boat_no', 'racer_course_avg_st']
        
        df = df.merge(st_stats, on=['racer_id', 'boat_no'], how='left')
        df['racer_course_avg_st'] = df['racer_course_avg_st'].fillna(0.15)
        
        # ST優位性（低いほど良い）
        df['st_advantage'] = 0.15 - df['racer_course_avg_st']
    else:
        df['racer_course_avg_st'] = 0.15
        df['st_advantage'] = 0.0
    
    return df


# ===== 5. レース内の力関係 =====
def add_race_power_balance(df: pd.DataFrame) -> pd.DataFrame:
    """レース内での力関係特徴量"""
    df = df.copy()
    
    if 'racer_win_rate' not in df.columns:
        return df
    
    # レースごとにグループ化
    race_key = ['date', 'jyo_cd', 'race_no'] if all(c in df.columns for c in ['date', 'jyo_cd', 'race_no']) else []
    
    if race_key:
        # レース内での勝率順位
        df['win_rate_race_rank'] = df.groupby(race_key)['racer_win_rate'].rank(ascending=False, method='min')
        
        # レース内の最高/最低勝率との差
        df['win_rate_vs_max'] = df.groupby(race_key)['racer_win_rate'].transform('max') - df['racer_win_rate']
        df['win_rate_vs_min'] = df['racer_win_rate'] - df.groupby(race_key)['racer_win_rate'].transform('min')
        
        # レース内の勝率標準偏差（混戦度）
        df['race_std'] = df.groupby(race_key)['racer_win_rate'].transform('std').fillna(0)
        
        # 上位集中度（トップ2の勝率合計）
        def top2_sum(x):
            return x.nlargest(2).sum()
        df['race_top2_concentration'] = df.groupby(race_key)['racer_win_rate'].transform(top2_sum)
        
        # 穴馬ポテンシャル（低勝率選手の躍進可能性）
        df['upset_potential_v2'] = (df['motor_2ren'] - 30) / 10 * (7 - df['win_rate_race_rank']) / 6
    else:
        df['win_rate_race_rank'] = 3
        df['win_rate_vs_max'] = 0
        df['win_rate_vs_min'] = 0
        df['race_std'] = 0
        df['race_top2_concentration'] = 0
        df['upset_potential_v2'] = 0
    
    return df


# ===== 6. 天候×コースの組み合わせ =====
def add_weather_course_features(df: pd.DataFrame) -> pd.DataFrame:
    """天候とコースの組み合わせ特徴量"""
    df = df.copy()
    
    # 風向き効果
    # 追い風(0-2): イン有利、向かい風(4-6): アウト有利
    if 'wind_direction' in df.columns and 'boat_no' in df.columns:
        df['wind_dir'] = pd.to_numeric(df['wind_direction'], errors='coerce').fillna(0)
        df['is_tailwind'] = (df['wind_dir'] <= 2).astype(int)
        df['is_headwind'] = (df['wind_dir'] >= 4).astype(int)
        
        # 風向き×コースの有利度
        df['wind_course_benefit'] = np.where(
            df['is_tailwind'] == 1,
            (4 - df['boat_no']) / 3,  # 追い風時はインが有利
            np.where(
                df['is_headwind'] == 1,
                (df['boat_no'] - 3) / 3,  # 向かい風時はアウトが有利
                0
            )
        )
    else:
        df['wind_course_benefit'] = 0
    
    # 波高効果（波が高いとイン不利）
    if 'wave_height' in df.columns and 'boat_no' in df.columns:
        df['wave'] = pd.to_numeric(df['wave_height'], errors='coerce').fillna(0)
        df['rough_water_penalty'] = np.where(
            df['wave'] >= 3,
            np.where(df['boat_no'] <= 2, -0.5, 0.3),
            0
        )
    else:
        df['rough_water_penalty'] = 0
    
    return df


# ===== 7. 2連単・3連単向け特徴量 =====
def add_exacta_trifecta_features(df: pd.DataFrame) -> pd.DataFrame:
    """連単向けの特徴量"""
    df = df.copy()
    
    race_key = ['date', 'jyo_cd', 'race_no'] if all(c in df.columns for c in ['date', 'jyo_cd', 'race_no']) else []
    
    if not race_key or 'racer_win_rate' not in df.columns:
        return df
    
    # 2着になりやすさ（2号艇は差しで2着が多い）
    COURSE_2ND_RATE = {1: 0.22, 2: 0.25, 3: 0.18, 4: 0.15, 5: 0.11, 6: 0.09}
    df['base_2nd_rate'] = df['boat_no'].map(COURSE_2ND_RATE).fillna(0.15)
    
    # 勝率と2着率の調整
    df['adjusted_2nd_prob'] = df['base_2nd_rate'] * (df['racer_win_rate'] / 5.5)
    
    # 3着になりやすさ
    COURSE_3RD_RATE = {1: 0.12, 2: 0.18, 3: 0.20, 4: 0.19, 5: 0.16, 6: 0.15}
    df['base_3rd_rate'] = df['boat_no'].map(COURSE_3RD_RATE).fillna(0.166)
    df['adjusted_3rd_prob'] = df['base_3rd_rate'] * (df['racer_win_rate'] / 5.5)
    
    # 連対力（1着or2着になる力）
    df['rentai_power'] = df['racer_win_rate'] / 10 + df['base_2nd_rate']
    
    # 3連対力（3着以内になる力）
    df['sanrentai_power'] = df['rentai_power'] + df['base_3rd_rate'] * 0.5
    
    return df


# ===== メイン関数 =====
def add_all_advanced_features_v2(df: pd.DataFrame) -> pd.DataFrame:
    """全ての高度な特徴量を追加"""
    df = add_recent_form_features(df)
    df = add_venue_affinity_features(df)
    df = add_motor_venue_features(df)
    df = add_start_timing_features(df)
    df = add_race_power_balance(df)
    df = add_weather_course_features(df)
    df = add_exacta_trifecta_features(df)
    return df


# 新しい特徴量リスト
ADVANCED_FEATURES_V2 = [
    # 直近フォーム
    'recent_avg_rank', 'recent_win_rate', 'recent_rentai_rate',
    # 会場相性
    'venue_avg_rank', 'venue_win_rate', 'venue_affinity',
    # モーター会場適性
    'motor_venue_avg_rank', 'motor_venue_advantage',
    # ST特徴
    'racer_course_avg_st', 'st_advantage',
    # 力関係
    'win_rate_race_rank', 'win_rate_vs_max', 'win_rate_vs_min',
    'race_std', 'race_top2_concentration', 'upset_potential_v2',
    # 天候×コース
    'wind_course_benefit', 'rough_water_penalty',
    # 連単特徴
    'base_2nd_rate', 'adjusted_2nd_prob', 'base_3rd_rate', 'adjusted_3rd_prob',
    'rentai_power', 'sanrentai_power'
]
