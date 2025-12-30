"""Common Pydantic schemas for API"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class ConfidenceLevel(str, Enum):
    S = "S"
    A = "A"
    B = "B"
    C = "C"


class BetType(str, Enum):
    TANSHO = "tansho"
    NIRENTAN = "nirentan"
    NIRENUFUKU = "nirenufuku"
    SANRENTAN = "sanrentan"
    SANRENFUKU = "sanrenfuku"


class RaceStatus(str, Enum):
    NO_DATA = "no_data"
    AWAITING_RESULT = "awaiting_result"
    FINISHED = "finished"


# Request Schemas
class PredictionRequest(BaseModel):
    date: str = Field(..., pattern=r"^\d{8}$", description="Date in YYYYMMDD format")
    jyo: str = Field(..., pattern=r"^\d{2}$", description="Stadium code")
    race: int = Field(..., ge=1, le=12, description="Race number")


class BacktestRequest(BaseModel):
    stadium: Optional[str] = Field(None, pattern=r"^\d{2}$")
    min_prob: float = Field(0.4, ge=0.1, le=0.9)
    wind_min: Optional[float] = None
    wind_max: Optional[float] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class WhatIfRequest(BaseModel):
    race_id: Optional[str] = None
    modifications: Dict[str, float] = Field(default_factory=dict)


class BettingOptimizeRequest(BaseModel):
    date: str
    jyo: str
    race: int
    budget: float = Field(10000, ge=100)
    bet_type: BetType = BetType.SANRENTAN
    kelly_fraction: float = Field(0.5, ge=0.1, le=1.0)


class ChatRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    context: Optional[Dict[str, Any]] = None


# Response Schemas
class BoatPrediction(BaseModel):
    boat_no: int
    racer_name: str
    probability: float
    motor_rank: str
    racer_rank: str
    expected_value: Optional[float] = None


class BettingTip(BaseModel):
    combo: str
    ev: float
    odds: Optional[float] = None
    recommended_amount: Optional[float] = None


class PredictionResponse(BaseModel):
    date: str
    jyo_cd: str
    race_no: int
    race_name: str
    predictions: List[BoatPrediction]
    tips: Dict[str, List[BettingTip]]
    confidence: ConfidenceLevel
    insights: List[str]
    展開予測: Optional[Dict[str, float]] = None


class RaceInfo(BaseModel):
    jyo_cd: str
    jyo_name: str
    race_no: int
    race_name: str
    start_time: str
    status: RaceStatus
    has_prediction: bool
    racers: List[str] = []


class TodayRacesResponse(BaseModel):
    meta: Dict[str, Any]
    races: List[RaceInfo]


class StatusResponse(BaseModel):
    model_loaded: bool
    dataset_size: int
    last_updated: str
    last_sync: Optional[str]
    sync_running: bool
    changelog_ready: bool
    hardware_accel: str
    cache_status: str = "unknown"


class SimulationSummary(BaseModel):
    roi: float
    hit_rate: float
    profit: float
    total_bets: int
    wins: int


class PortfolioSummary(BaseModel):
    balance: float
    roi: float
    win_rate: float
    total_bets: int
    transactions: List[Dict[str, Any]]


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    traceback: Optional[str] = None


class SuccessResponse(BaseModel):
    status: str = "success"
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
