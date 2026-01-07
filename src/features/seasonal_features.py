"""季節調整特徴量モジュール

temperatureドリフトに対応するため、季節性を考慮した特徴量を生成。
月別・季節別の正規化により、モデルの汎化性能を向上。
"""
import pandas as pd
import numpy as np
from typing import Dict, Optional
from datetime import datetime

from src.utils.logger import logger

# 月別の気温・水温の基準値（日本の競艇場の平均）
MONTHLY_TEMP_BASELINE = {
    1: {'temp': 7.0, 'water_temp': 10.0},
    2: {'temp': 8.0, 'water_temp': 9.0},
    3: {'temp': 12.0, 'water_temp': 11.0},
    4: {'temp': 17.0, 'water_temp': 15.0},
    5: {'temp': 21.0, 'water_temp': 19.0},
    6: {'temp': 24.0, 'water_temp': 23.0},
    7: {'temp': 28.0, 'water_temp': 27.0},
    8: {'temp': 29.0, 'water_temp': 28.0},
    9: {'temp': 25.0, 'water_temp': 25.0},
    10: {'temp': 19.0, 'water_temp': 21.0},
    11: {'temp': 14.0, 'water_temp': 17.0},
    12: {'temp': 9.0, 'water_temp': 13.0},
}

# 季節の定義
SEASON_MAP = {
    1: 'winter', 2: 'winter', 3: 'spring',
    4: 'spring', 5: 'spring', 6: 'summer',
    7: 'summer', 8: 'summer', 9: 'autumn',
    10: 'autumn', 11: 'autumn', 12: 'winter'
}

# 会場別の気温補正（暖かい会場は+、寒い会場は-）
VENUE_TEMP_ADJUSTMENT = {
    '01': 0,    # 桐生
    '02': 1,    # 戸田
    '03': 1,    # 江戸川
    '04': 1,    # 平和島
    '05': 1,    # 多摩川
    '06': 0,    # 浜名湖
    '07': 2,    # 蒲郡
    '08': 3,    # 常滑
    '09': 3,    # 津
    '10': 2,    # 三国
    '11': 3,    # びわこ
    '12': 2,    # 住之江
    '13': 3,    # 尼崎
    '14': 4,    # 鳴門
    '15': 4,    # 丸亀
    '16': 6,    # 児島
    '17': 5,    # 宮島
    '18': 6,    # 徳山
    '19': 6,    # 下関
    '20': 7,    # 若松
    '21': 8,    # 芦屋
    '22': 8,    # 福岡
    '23': 8,    # 唐津
    '24': 10,   # 大村
}


class SeasonalFeatureGenerator:
    """季節調整特徴量を生成するクラス"""
    
    def __init__(self):
        self.monthly_baseline = MONTHLY_TEMP_BASELINE
        self.season_map = SEASON_MAP
        self.venue_adjustment = VENUE_TEMP_ADJUSTMENT
    
    def extract_month(self, df: pd.DataFrame) -> pd.Series:
        """日付から月を抽出"""
        if 'date' not in df.columns:
            return pd.Series([1] * len(df), index=df.index)
        
        date_col = df['date']
        if date_col.dtype == 'object' or date_col.dtype == 'int64':
            date_col = pd.to_datetime(date_col.astype(str), format='%Y%m%d', errors='coerce')
        
        return date_col.dt.month.fillna(1).astype(int)
    
    def generate_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        季節調整特徴量を生成
        
        追加される特徴量:
        - month: 月 (1-12)
        - season: 季節 (winter/spring/summer/autumn)
        - is_winter/spring/summer/autumn: 季節フラグ
        - temp_seasonal_baseline: その月の基準気温
        - temp_deviation: 基準からの偏差
        - temp_zscore_seasonal: 季節内でのZ-score
        - water_temp_deviation: 水温の基準からの偏差
        - temp_venue_adjusted: 会場補正後の気温偏差
        - temp_anomaly: 異常気温フラグ (基準から±5度以上)
        - winter_advantage: 冬季のアウターコース有利度
        - summer_advantage: 夏季の水温影響
        """
        df = df.copy()
        
        # 月を抽出
        df['month'] = self.extract_month(df)
        
        # 季節を設定
        df['season'] = df['month'].map(self.season_map)
        
        # 季節フラグ
        df['is_winter'] = (df['season'] == 'winter').astype(int)
        df['is_spring'] = (df['season'] == 'spring').astype(int)
        df['is_summer'] = (df['season'] == 'summer').astype(int)
        df['is_autumn'] = (df['season'] == 'autumn').astype(int)
        
        # 月別基準気温
        df['temp_seasonal_baseline'] = df['month'].map(
            lambda m: self.monthly_baseline.get(m, {}).get('temp', 18)
        )
        df['water_temp_baseline'] = df['month'].map(
            lambda m: self.monthly_baseline.get(m, {}).get('water_temp', 18)
        )
        
        # 気温偏差
        if 'temperature' in df.columns:
            df['temperature'] = pd.to_numeric(df['temperature'], errors='coerce').fillna(18)
            df['temp_deviation'] = df['temperature'] - df['temp_seasonal_baseline']
            
            # 季節別Z-score
            seasonal_stats = df.groupby('season')['temperature'].agg(['mean', 'std'])
            seasonal_stats['std'] = seasonal_stats['std'].replace(0, 1)  # ゼロ除算防止
            
            def calc_zscore(row):
                season = row['season']
                if season in seasonal_stats.index:
                    mean = seasonal_stats.loc[season, 'mean']
                    std = seasonal_stats.loc[season, 'std']
                    return (row['temperature'] - mean) / std if std > 0 else 0
                return 0
            
            df['temp_zscore_seasonal'] = df.apply(calc_zscore, axis=1)
        else:
            df['temp_deviation'] = 0
            df['temp_zscore_seasonal'] = 0
        
        # 水温偏差
        if 'water_temperature' in df.columns:
            df['water_temperature'] = pd.to_numeric(df['water_temperature'], errors='coerce').fillna(18)
            df['water_temp_deviation'] = df['water_temperature'] - df['water_temp_baseline']
        else:
            df['water_temp_deviation'] = 0
        
        # 会場補正
        if 'jyo_cd' in df.columns:
            df['jyo_cd_str'] = df['jyo_cd'].astype(str).str.zfill(2)
            venue_adj = df['jyo_cd_str'].map(self.venue_adjustment).fillna(0)
            df['temp_venue_adjusted'] = df.get('temp_deviation', 0) - venue_adj
            df = df.drop(columns=['jyo_cd_str'])
        else:
            df['temp_venue_adjusted'] = df.get('temp_deviation', 0)
        
        # 異常気温フラグ
        df['temp_anomaly'] = (abs(df.get('temp_deviation', 0)) >= 5).astype(int)
        
        # 季節×コース相互作用
        if 'boat_no' in df.columns:
            # 冬季はアウターコースが有利になりやすい（インが不利）
            df['winter_outer_advantage'] = df['is_winter'] * (df['boat_no'] >= 4).astype(int)
            
            # 夏季は水温が高く全体的にスピードが出やすい
            df['summer_speed_factor'] = df['is_summer'] * df.get('water_temp_deviation', 0).clip(0, 5) / 5
        else:
            df['winter_outer_advantage'] = 0
            df['summer_speed_factor'] = 0
        
        # 気温×展示タイム相互作用（寒いとエンジンに影響）
        if 'exhibition_time' in df.columns and 'temperature' in df.columns:
            df['temp_exhibition_interaction'] = df['temp_deviation'] * (df['exhibition_time'] - 6.80)
        else:
            df['temp_exhibition_interaction'] = 0
        
        logger.debug(f"Generated seasonal features for {len(df)} records")
        return df


# シングルトン
_generator: Optional[SeasonalFeatureGenerator] = None


def get_seasonal_generator() -> SeasonalFeatureGenerator:
    global _generator
    if _generator is None:
        _generator = SeasonalFeatureGenerator()
    return _generator


def add_seasonal_features(df: pd.DataFrame) -> pd.DataFrame:
    """季節調整特徴量をDataFrameに追加するユーティリティ関数"""
    generator = get_seasonal_generator()
    return generator.generate_features(df)


# エクスポートする特徴量リスト
SEASONAL_FEATURES = [
    'month',
    'is_winter', 'is_spring', 'is_summer', 'is_autumn',
    'temp_deviation', 'temp_zscore_seasonal',
    'water_temp_deviation', 'temp_venue_adjusted',
    'temp_anomaly',
    'winter_outer_advantage', 'summer_speed_factor',
    'temp_exhibition_interaction'
]


if __name__ == "__main__":
    # テスト
    test_data = pd.DataFrame({
        'date': ['20240115', '20240415', '20240715', '20241015'],
        'jyo_cd': ['02', '12', '21', '06'],
        'temperature': [5, 18, 32, 20],
        'water_temperature': [8, 16, 29, 22],
        'exhibition_time': [6.75, 6.80, 6.72, 6.85],
        'boat_no': [1, 3, 5, 2],
    })
    
    result = add_seasonal_features(test_data)
    print("\n=== Seasonal Features Test ===")
    for col in SEASONAL_FEATURES:
        if col in result.columns:
            print(f"{col}: {result[col].tolist()}")
