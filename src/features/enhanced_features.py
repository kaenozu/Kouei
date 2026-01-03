"""
Enhanced Features - Advanced feature engineering for better predictions
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class EnhancedFeatures:
    """拡張特徴量エンジニアリング"""
    
    def __init__(self):
        self.feature_names = []
        
    def create_all_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """全ての拡張特徴量を作成"""
        df = df.copy()
        
        # レーサー特徴量
        df = self._create_racer_features(df)
        
        # モーター・ボート特徴量
        df = self._create_equipment_features(df)
        
        # コース特徴量
        df = self._create_course_features(df)
        
        # 天候・水面特徴量
        df = self._create_weather_features(df)
        
        # 時系列特徴量
        df = self._create_temporal_features(df)
        
        # 相互作用特徴量
        df = self._create_interaction_features(df)
        
        # 統計特徴量
        df = self._create_statistical_features(df)
        
        logger.info(f"✅ Enhanced features created: {len(df.columns)} features")
        return df
    
    def _create_racer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """レーサー関連の特徴量"""
        # レーサー年齢（推定）
        df['racer_age_est'] = df['racer_id'].apply(self._estimate_racer_age)
        
        # 勝率から安定性指標
        df['win_rate_stability'] = df['racer_win_rate'] * (1 - df['racer_win_rate'])
        
        # 勝率カテゴリ
        df['win_rate_category'] = pd.cut(df['racer_win_rate'], 
                                       bins=[0, 2, 4, 6, 8, 10],
                                       labels=['新手', 'C', 'B', 'A', 'S'])
        
        # レーサー経験度
        df['racer_experience'] = df['racer_id'].apply(self._calculate_racer_experience)
        
        return df
    
    def _create_equipment_features(self, df: pdDataFrame) -> pd.DataFrame:
        """装備（モーター・ボート）特徴量"""
        # モーターコードからタイプ推定
        df['motor_type'] = df['motor_no'].apply(self._get_motor_type)
        
        # モーター連続使用期間による疲労度
        df['motor_fatigue'] = df['motor_2ren'].apply(self._calculate_equipment_fatigue)
        
        # ボート連続使用期間による疲労度
        df['boat_fatigue'] = df['boat_hull_no'].apply(self._calculate_equipment_fatigue)
        
        # 装備性能スコア
        df['equipment_score'] = (df['motor_2ren'] * 0.6 + df['boat_2ren'] * 0.4)
        
        # 装備マッチングスコア
        df['equipment_matching'] = np.abs(df['motor_2ren'] - df['boat_2ren'])
        
        return df
    
    def _create_course_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """コース関連の特徴量"""
        # コース番号の優位性
        course_advantage = [1.0, 0.95, 0.82, 0.63, 0.39, 0.17]
        df['course_advantage_score'] = df['boat_no'].apply(
            lambda x: course_advantage[x-1] if 1 <= x <= 6 else 0.5
        )
        
        # スタートタイムからスタート性能
        df['start_performance'] = np.where(df['exhibition_time'] < 6.8, 1.0,
                                         np.where(df['exhibition_time'] < 7.0, 0.8, 0.6))
        
        # コースとスタート性能の相互作用
        df['course_start_match'] = (df['course_advantage_score'] * df['start_performance'])
        
        return df
    
    def _create_weather_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """天候・水面特徴量"""
        # 風の強さカテゴリ
        df['wind_level'] = pd.cut(df['wind_speed'], 
                                  bins=[0, 1, 3, 5, 10],
                                  labels=['無風', '微風', '中風', '強風'])
        
        # 風向きとコースの関係性
        df['wind_course_impact'] = self._calculate_wind_course_impact(df)
        
        # 波高に対する安定性
        df['wave_stability'] = np.where(df['wave_height'] <= 1.0, 1.0,
                                       np.where(df['wave_height'] <= 3.0, 0.8, 0.6))
        
        # 水温によるパフォーマンス変動
        df['temp_performance'] = self._calculate_temperature_impact(df)
        
        return df
    
    def _create_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """時系列特徴量"""
        # レース時間帯カテゴリ
        df['time_slot'] = pd.to_datetime(df['start_time'], format='%H:%M', errors='coerce').dt.hour.fillna(12)
        df['time_slot'] = pd.cut(df['time_slot'], 
                                bins=[0, 9, 12, 15, 18, 24],
                                labels=['午前', '昼前', '昼後', '夕方', '夜'])
        
        # 曜日からの影響（週末は競争が激しい）
        df['weekend_effect'] = 0  # 後で計算
        
        return df
    
    def _create_interaction_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """相互作用特徴量"""
        # レーサー能力と装備性能の相互作用
        df['racer_equipment_synergy'] = (df['racer_win_rate'] * df['equipment_score']) / 100
        
        # 天候と装備の相互作用
        df['weather_equipment_impact'] = self._calculate_weather_equipment_interaction(df)
        
        # コースとモーターの相互作用
        df['course_motor_match'] = df['course_advantage_score'] * df['motor_fatigue']
        
        return df
    
    def _create_statistical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """統計特徴量"""
        # レース内の相対的な評価
        for stat in ['racer_win_rate', 'equipment_score', 'exhibition_time']:
            df[f'{stat}_race_rank'] = df.groupby(['date', 'jyo_cd', 'race_no'])[stat].transform('rank', ascending=False)
            df[f'{stat}_race_zscore'] = df.groupby(['date', 'jyo_cd', 'race_no'])[stat].transform(
                lambda x: (x - x.mean()) / x.std()
            )
        
        return df
    
    def _estimate_racer_age(self, racer_id: int) -> float:
        """レーサー年齢推定（簡易）"""
        # レーサーIDから年代を推定（現実的なロジックではない）
        return 45 + (racer_id % 20) - 10
    
    def _calculate_racer_experience(self, racer_id: int) -> float:
        """レーサー経験度"""
        # IDから経験度を計算（簡易）
        return racer_id / 1000
    
    def _get_motor_type(self, motor_no: int) -> str:
        """モータータイプ分類"""
        if motor_no < 20:
            return '旧型'
        elif motor_no < 40:
            return '標準型'
        elif motor_no < 60:
            return '新型'
        else:
            return '最新型'
    
    def _calculate_equipment_fatigue(self, ren_count: float) -> float:
        """装備疲労度計算"""
        # 連続使用が多いほど疲労
        return np.exp(-ren_count / 10)
    
    def _calculate_wind_course_impact(self, df: pd.DataFrame) -> pd.Series:
        """風向きとコースの影響計算"""
        # 風向きを0-360度に変換（簡易）
        df['wind_deg'] = df['wind_direction'] * 45
        
        # 各コースの風影響を計算（簡易計算）
        result = pd.Series(0, index=df.index)
        for boat_no in range(1, 7):
            course_wind_angle = abs(boat_no * 60 - df['wind_deg'])  # 簡易計算
            result[df['boat_no'] == boat_no] = np.cos(np.radians(course_wind_angle))
        
        return result
    
    def _calculate_temperature_impact(self, df: pd.DataFrame) -> pd.Series:
        """水温によるパフォーマンス影響"""
        # 最適水温範囲
        optimal_temp = 20
        temp_diff = abs(df['water_temperature'] - optimal_temp)
        return np.exp(-temp_diff / 10)
    
    def _calculate_weather_equipment_interaction(self, df: pd.DataFrame) -> pd.Series:
        """天候と装備の相互作用"""
        # 悪天候では装備性能がより重要に
        weather_severity = (df['wind_speed'] / 5 + df['wave_height'] / 2)
        return df['equipment_score'] * (1 + weather_severity * 0.1)


# グローバルインスタンス
enhanced_features = EnhancedFeatures()


def apply_enhanced_features(df: pd.DataFrame) -> pd.DataFrame:
    """拡張特徴量を適用"""
    if df.empty:
        return df
    return enhanced_features.create_all_features(df)
