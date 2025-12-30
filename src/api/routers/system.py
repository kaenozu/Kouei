"""System Router - Status and system endpoints"""
from fastapi import APIRouter, Depends, BackgroundTasks, WebSocket, WebSocketDisconnect
from datetime import datetime
import os
import pandas as pd
import json

from src.api.dependencies import get_cache, get_drift_detector, get_venue_scorer
from src.api.routers.sync import get_sync_status
from src.cache.redis_client import RedisCache
from src.monitoring.drift_detector import DriftDetector
from src.utils.logger import logger

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

router = APIRouter(prefix="/api", tags=["system"])

MODEL_PATH = "models/lgbm_model.txt"
DATA_PATH = "data/processed/race_data.csv"

# WebSocket connections
active_connections: list[WebSocket] = []


@router.get("/status")
async def get_status(cache: RedisCache = Depends(get_cache)):
    """Get system status"""
    sync_status = get_sync_status()
    
    dataset_size = 0
    if os.path.exists(DATA_PATH):
        try:
            df = pd.read_csv(DATA_PATH)
            dataset_size = len(df)
        except:
            pass
    
    return {
        "model_loaded": os.path.exists(MODEL_PATH),
        "dataset_size": dataset_size,
        "last_updated": datetime.now().isoformat(),
        "last_sync": sync_status["last_sync"],
        "sync_running": sync_status["is_running"],
        "changelog_ready": os.path.exists("CHANGELOG.md"),
        "hardware_accel": "CUDA/GPU" if TORCH_AVAILABLE and torch.cuda.is_available() else "CPU",
        "cache_status": "connected" if cache.enabled else "disconnected"
    }


@router.post("/optimize")
async def trigger_optimization(
    trials: int = 50,
    background_tasks: BackgroundTasks = None
):
    """Trigger Optuna hyperparameter optimization"""
    try:
        from src.model.optimize_params import run_optimization
    except ImportError:
        return {"status": "error", "message": "Optimization module not available"}
    
    if background_tasks:
        background_tasks.add_task(run_optimization, trials)
    else:
        run_optimization(trials)
    
    return {"status": "started", "message": f"Optimization started with {trials} trials"}


@router.get("/drift-check")
async def check_drift(
    drift_detector: DriftDetector = Depends(get_drift_detector),
    cache: RedisCache = Depends(get_cache)
):
    """Check for model drift"""
    cache_key = "drift:latest"
    
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    report = drift_detector.check_drift()
    cache.set(cache_key, report, ttl=3600)  # 1 hour cache
    
    return report


@router.get("/config")
async def get_config():
    """Get application configuration"""
    if os.path.exists("config.json"):
        try:
            with open("config.json", "r") as f:
                return json.load(f)
        except:
            pass
    return {}


@router.post("/config")
async def update_config(config: dict):
    """Update application configuration"""
    try:
        existing = {}
        if os.path.exists("config.json"):
            with open("config.json", "r") as f:
                existing = json.load(f)
        
        existing.update(config)
        
        with open("config.json", "w") as f:
            json.dump(existing, f, indent=4)
        
        return {"status": "success", "config": existing}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates"""
    await websocket.accept()
    active_connections.append(websocket)
    
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections.remove(websocket)


async def broadcast_event(event_type: str, data: dict):
    """Broadcast event to all connected clients"""
    message = json.dumps({"type": event_type, "data": data})
    for connection in active_connections:
        try:
            await connection.send_text(message)
        except:
            pass


@router.post("/visual/analyze")
async def visual_analysis_placeholder(data: dict):
    """Placeholder for future video/image analysis"""
    return {
        "status": "future_feature",
        "message": "Visual analysis is scheduled for future development."
    }
