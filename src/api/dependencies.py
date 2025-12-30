"""FastAPI Dependencies for Dependency Injection"""
import os
import pandas as pd
from functools import lru_cache
from typing import Optional
from fastapi import Depends, HTTPException, status

from src.model.predictor import Predictor
from src.model.ensemble import EnsemblePredictor
from src.cache.redis_client import RedisCache, cache
from src.portfolio.ledger import PortfolioLedger
from src.inference.commentary import CommentaryGenerator
from src.inference.whale import WhaleDetector
from src.analysis.racer_tracker import RacerTracker
from src.monitoring.drift_detector import DriftDetector
from src.analysis.venue_scoring import VenueScorer
from src.analysis.vector_db_manager import vector_db
from src.config.settings import settings
from src.utils.logger import logger

# Constants
DATA_PATH = "data/processed/race_data.csv"
MODEL_DIR = "models"

# Cached DataFrame
_cached_df: Optional[pd.DataFrame] = None
_cached_df_mtime: float = 0


def get_dataframe() -> pd.DataFrame:
    """Get cached DataFrame, reload if file changed"""
    global _cached_df, _cached_df_mtime
    
    if not os.path.exists(DATA_PATH):
        return pd.DataFrame()
    
    current_mtime = os.path.getmtime(DATA_PATH)
    
    if _cached_df is None or current_mtime > _cached_df_mtime:
        logger.info(f"Loading DataFrame from {DATA_PATH}")
        _cached_df = pd.read_csv(DATA_PATH)
        _cached_df_mtime = current_mtime
        logger.info(f"DataFrame loaded: {len(_cached_df)} rows")
    
    return _cached_df


def refresh_dataframe():
    """Force refresh the cached DataFrame"""
    global _cached_df, _cached_df_mtime
    _cached_df = None
    _cached_df_mtime = 0
    return get_dataframe()


@lru_cache(maxsize=1)
def get_predictor() -> Predictor:
    """Get cached Predictor instance"""
    logger.info("Initializing Predictor")
    return Predictor(model_dir=MODEL_DIR)


@lru_cache(maxsize=1)
def get_ensemble_predictor() -> EnsemblePredictor:
    """Get cached EnsemblePredictor instance"""
    logger.info("Initializing EnsemblePredictor")
    predictor = EnsemblePredictor()
    predictor.load_models()
    return predictor


@lru_cache(maxsize=1)
def get_ledger() -> PortfolioLedger:
    """Get cached PortfolioLedger instance"""
    return PortfolioLedger()


@lru_cache(maxsize=1)
def get_commentary_generator() -> CommentaryGenerator:
    """Get cached CommentaryGenerator instance"""
    return CommentaryGenerator()


@lru_cache(maxsize=1)
def get_whale_detector() -> WhaleDetector:
    """Get cached WhaleDetector instance"""
    return WhaleDetector()


@lru_cache(maxsize=1)
def get_racer_tracker() -> RacerTracker:
    """Get cached RacerTracker instance"""
    return RacerTracker()


@lru_cache(maxsize=1)
def get_drift_detector() -> DriftDetector:
    """Get cached DriftDetector instance"""
    return DriftDetector()


@lru_cache(maxsize=1)
def get_venue_scorer() -> VenueScorer:
    """Get cached VenueScorer instance"""
    return VenueScorer()


def get_cache() -> RedisCache:
    """Get Redis cache instance"""
    return cache


def get_vector_db():
    """Get VectorDB instance"""
    return vector_db


# Stadium mapping
STADIUM_MAP = {
    "01": "桐生", "02": "戸田", "03": "江戸川", "04": "平和島", "05": "多摩川",
    "06": "浜名湖", "07": "蒲郡", "08": "常滑", "09": "津", "10": "三国",
    "11": "びわこ", "12": "住之江", "13": "尼崎", "14": "鳴門", "15": "丸亀",
    "16": "児島", "17": "宮島", "18": "徳山", "19": "下関", "20": "若松",
    "21": "芦屋", "22": "福岡", "23": "唐津", "24": "大村"
}


def get_stadium_name(code: str) -> str:
    """Get stadium name from code"""
    return STADIUM_MAP.get(code.zfill(2), f"会場{code}")


# Feature names in Japanese
FEATURE_NAMES_JP = {
    "boat_no": "枚番",
    "racer_win_rate": "勝率",
    "motor_2ren": "モーター性能",
    "exhibition_time": "展示タイム",
    "racer_win_rate_diff": "格差(勝率)",
    "motor_2ren_diff": "格差(モーター)",
    "exhibition_time_diff": "格差(展示)",
    "stadium_avg_rank": "会場相性"
}
