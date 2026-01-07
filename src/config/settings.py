"""Centralized Settings Management using Pydantic"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional
from functools import lru_cache
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False
    
    # Database
    database_url: str = "sqlite:///data/race_data.db"
    use_postgres: bool = False
    
    # Redis Cache
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    cache_ttl_default: int = 300
    cache_ttl_realtime: int = 60
    
    # Model Paths
    model_dir: str = "models"
    lgbm_model_path: str = "models/lgbm_model.txt"
    xgb_model_path: str = "models/xgb_model.json"
    cat_model_path: str = "models/cat_model.cbm"
    onnx_model_path: str = "models/model.onnx"
    use_onnx: bool = True
    
    # Data Paths
    data_dir: str = "data"
    raw_data_dir: str = "data/raw"
    processed_data_path: str = "data/processed/race_data.csv"
    
    # Notifications
    discord_webhook_url: str = ""
    notification_threshold: float = 0.5
    
    # Training
    auto_train_threshold_races: int = 1000
    last_trained_dataset_size: int = 0
    
    # Scraping
    scrape_delay: float = 1.0
    scrape_timeout: int = 30
    max_concurrent_requests: int = 10
    
    # Kelly Criterion
    fractional_kelly: float = 0.5
    max_bet_percentage: float = 0.1
    min_bet_amount: int = 100
    
    # LLM Integration
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    llm_provider: str = "none"  # none, openai, anthropic
    
    # Feature Flags
    enable_whale_detection: bool = True
    enable_drift_detection: bool = True
    enable_realtime_odds: bool = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Global settings instance
settings = get_settings()


def reload_settings():
    """Reload settings (clears cache)"""
    get_settings.cache_clear()
    return get_settings()
