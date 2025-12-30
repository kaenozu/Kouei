"""API Routers"""
from .prediction import router as prediction_router
from .races import router as races_router
from .portfolio import router as portfolio_router
from .analysis import router as analysis_router
from .betting import router as betting_router
from .sync import router as sync_router
from .system import router as system_router

__all__ = [
    "prediction_router",
    "races_router", 
    "portfolio_router",
    "analysis_router",
    "betting_router",
    "sync_router",
    "system_router",
]
