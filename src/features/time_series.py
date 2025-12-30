"""時系列特徴量生成

選手の直近レースのモメンタムを分析し、特徴量として追加
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from src.utils.logger import logger


class TimeSeriesFeatureGenerator:
    """選手の時系列特徴量を生成"""
    
    def __init__(self, lookback_races: int = 10):
        self.lookback_races = lookback_races
    
    def generate_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        時系列特徴量を生成してDataFrameに追加
        
        追加される特徴量:
        - momentum_score: 直近の着順の傾向（上昇/下降）
        - win_streak: 連勝数
        - top3_rate_recent: 直近Nレースの3着以内率
        - avg_rank_recent: 直近Nレースの平均着順
        - rank_improvement: 着順の改善傾向
        - days_since_last_win: 最後の勝利からの日数
        """
        df = df.copy()
        
        # 必須カラムの確認
        required_cols = ['date', 'racer_id', 'rank']
        if not all(col in df.columns for col in required_cols):
            logger.warning("時系列特徴量生成に必要なカラムがありません")
            return df
        
        # 日付のソート
        df['date'] = pd.to_datetime(df['date'].astype(str), format='%Y%m%d', errors='coerce')
        df = df.sort_values(['racer_id', 'date'])
        
        # 各選手ごとに特徴量を計算
        feature_dfs = []
        
        for racer_id, racer_df in df.groupby('racer_id'):
            racer_features = self._calculate_racer_features(racer_df)
            feature_dfs.append(racer_features)
        
        if feature_dfs:
            features_df = pd.concat(feature_dfs, ignore_index=True)
            
            # 元のDataFrameにマージ
            merge_cols = ['date', 'racer_id', 'race_no', 'jyo_cd']
            available_merge_cols = [c for c in merge_cols if c in df.columns and c in features_df.columns]
            
            if available_merge_cols:
                df = df.merge(
                    features_df,
                    on=available_merge_cols,
                    how='left',
                    suffixes=('', '_ts')
                )
        
        return df
    
    def _calculate_racer_features(self, racer_df: pd.DataFrame) -> pd.DataFrame:
        """個別選手の特徴量を計算"""
        result_rows = []
        
        for idx in range(len(racer_df)):
            row = racer_df.iloc[idx]
            
            # 直近Nレースを取得（現在のレースは含まない）
            past_races = racer_df.iloc[max(0, idx - self.lookback_races):idx]
            
            features = {
                'date': row['date'],
                'racer_id': row['racer_id'],
                'race_no': row.get('race_no'),
                'jyo_cd': row.get('jyo_cd'),
            }
            
            if len(past_races) == 0:
                # 過去データなし
                features.update({
                    'momentum_score': 0.0,
                    'win_streak': 0,
                    'top3_rate_recent': 0.0,
                    'avg_rank_recent': 3.5,
                    'rank_improvement': 0.0,
                    'days_since_last_win': 999,
                })
            else:
                past_ranks = past_races['rank'].dropna().values
                
                if len(past_ranks) > 0:
                    # モメンタムスコア（直近が良いほど高い）
                    weights = np.exp(np.linspace(0, 1, len(past_ranks)))
                    weighted_ranks = np.average(past_ranks, weights=weights)
                    features['momentum_score'] = (3.5 - weighted_ranks) / 3.5
                    
                    # 連勝数
                    win_streak = 0
                    for rank in reversed(past_ranks):
                        if rank == 1:
                            win_streak += 1
                        else:
                            break
                    features['win_streak'] = win_streak
                    
                    # 3着以内率
                    features['top3_rate_recent'] = np.mean(past_ranks <= 3)
                    
                    # 平均着順
                    features['avg_rank_recent'] = np.mean(past_ranks)
                    
                    # 着順改善傾向（線形回帰の傾き）
                    if len(past_ranks) >= 3:
                        x = np.arange(len(past_ranks))
                        slope = np.polyfit(x, past_ranks, 1)[0]
                        features['rank_improvement'] = -slope  # 負の傾き = 改善
                    else:
                        features['rank_improvement'] = 0.0
                    
                    # 最後の勝利からの日数
                    win_indices = np.where(past_ranks == 1)[0]
                    if len(win_indices) > 0:
                        last_win_idx = win_indices[-1]
                        races_since_win = len(past_ranks) - last_win_idx - 1
                        features['days_since_last_win'] = races_since_win * 2  # おおよそ2日に1レースと仮定
                    else:
                        features['days_since_last_win'] = 999
                else:
                    features.update({
                        'momentum_score': 0.0,
                        'win_streak': 0,
                        'top3_rate_recent': 0.0,
                        'avg_rank_recent': 3.5,
                        'rank_improvement': 0.0,
                        'days_since_last_win': 999,
                    })
            
            result_rows.append(features)
        
        return pd.DataFrame(result_rows)
    
    def calculate_start_timing_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """スタートタイミング関連の特徴量を追加"""
        df = df.copy()
        
        if 'exhibition_time' not in df.columns:
            return df
        
        # 展示タイムのレース内偏差値
        if all(col in df.columns for col in ['date', 'jyo_cd', 'race_no']):
            race_groups = df.groupby(['date', 'jyo_cd', 'race_no'])
            
            df['exhibition_zscore'] = race_groups['exhibition_time'].transform(
                lambda x: (x - x.mean()) / x.std() if x.std() > 0 else 0
            )
            
            # レース内の展示タイム順位
            df['exhibition_rank'] = race_groups['exhibition_time'].transform(
                lambda x: x.rank(method='min')
            )
        
        return df


# シングルトン
_generator: Optional[TimeSeriesFeatureGenerator] = None


def get_time_series_generator() -> TimeSeriesFeatureGenerator:
    global _generator
    if _generator is None:
        _generator = TimeSeriesFeatureGenerator()
    return _generator


def add_time_series_features(df: pd.DataFrame) -> pd.DataFrame:
    """時系列特徴量をDataFrameに追加するユーティリティ関数"""
    generator = get_time_series_generator()
    df = generator.generate_features(df)
    df = generator.calculate_start_timing_features(df)
    return df


if __name__ == "__main__":
    # テスト
    test_data = pd.DataFrame({
        'date': ['20240101', '20240102', '20240103', '20240104', '20240105'] * 2,
        'racer_id': ['1234'] * 5 + ['5678'] * 5,
        'race_no': [1, 2, 3, 4, 5] * 2,
        'jyo_cd': ['02'] * 10,
        'rank': [1, 2, 1, 3, 2, 3, 4, 5, 2, 1],
        'exhibition_time': [6.75, 6.80, 6.72, 6.85, 6.78, 6.90, 6.88, 6.95, 6.82, 6.70],
    })
    
    result = add_time_series_features(test_data)
    print(result[['racer_id', 'date', 'momentum_score', 'win_streak', 'top3_rate_recent']].tail(10))
