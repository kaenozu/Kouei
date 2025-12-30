from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List

class AppConfig(BaseModel):
    discord_webhook_url: Optional[str] = None
    auto_train_threshold_races: int = Field(default=1000, ge=100)
    enable_sniper_mode: bool = True
    enable_whale_watcher: bool = True
    
    # Model Params (optional overlap with model_params.json, but here for app settings)
    model_version: str = "v1"

    class Config:
        extra = "ignore" # Allow extra fields in json
