"""System Router - Status and system endpoints"""
from fastapi import APIRouter, Depends, BackgroundTasks, WebSocket, WebSocketDisconnect, Query
from datetime import datetime
import os
import pandas as pd
import json
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from src.parser.schedule_parser import parse_today_races

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


@router.get("/drift-history")
async def get_drift_history(
    drift_detector: DriftDetector = Depends(get_drift_detector),
    limit: int = Query(30, ge=1, le=100)
):
    """Get drift history"""
    return drift_detector.get_drift_history(limit)


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


@router.get("/backtest/history")
async def get_backtest_history(days: int = Query(30, ge=1, le=90)):
    """Get backtest history summary"""
    from src.monitoring.auto_backtest import get_backtest_summary, load_backtest_history
    
    summary = get_backtest_summary(days)
    history = load_backtest_history()
    
    return {
        "summary": summary,
        "history": history[-days:]
    }


@router.post("/backtest/run")
async def trigger_backtest(
    date: str = Query(None, pattern=r"^\d{8}$"),
    background_tasks: BackgroundTasks = None
):
    """Trigger backtest for a specific date"""
    from src.monitoring.auto_backtest import run_daily_backtest
    
    result = run_daily_backtest(date)
    return result

# Active odds monitoring tasks
active_odds_monitors = {}


class OddsMonitor:
    """Monitor odds for a specific race and broadcast updates"""
    
    def __init__(self, date: str, jyo_cd: str, race_no: int):
        self.date = date
        self.jyo_cd = jyo_cd
        self.race_no = race_no
        self.running = False
        self.task = None
    
    async def start_monitoring(self):
        """Start monitoring odds"""
        if self.running:
            return
        
        self.running = True
        self.task = asyncio.create_task(self._monitor_loop())
        logger.info(f"Started odds monitoring for {self.date} {self.jyo_cd} R{self.race_no}")
    
    async def stop_monitoring(self):
        """Stop monitoring odds"""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info(f"Stopped odds monitoring for {self.date} {self.jyo_cd} R{self.race_no}")
    
    async def _monitor_loop(self):
        """Monitoring loop"""
        try:
            from src.collector.odds_collector import get_realtime_odds
            
            while self.running:
                try:
                    # Fetch odds
                    odds_data = await get_realtime_odds(self.date, self.jyo_cd, self.race_no)
                    
                    # Broadcast update
                    await broadcast_event("odds_update", {
                        "date": self.date,
                        "jyo_cd": self.jyo_cd,
                        "race_no": self.race_no,
                        "odds": {
                            "tansho": odds_data.tansho,
                            "nirentan": odds_data.nirentan,
                            "timestamp": odds_data.timestamp
                        }
                    })
                    
                    # Wait before next update
                    await asyncio.sleep(30)  # 30 seconds
                except Exception as e:
                    logger.error(f"Error in odds monitoring: {e}")
                    await asyncio.sleep(60)  # Wait longer on error
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Fatal error in odds monitoring: {e}")
        finally:
            self.running = False


@router.post("/monitor/odds/start")
async def start_odds_monitoring(date: str, jyo_cd: str, race_no: int):
    """Start monitoring odds for a specific race"""
    monitor_key = f"{date}_{jyo_cd}_{race_no}"
    
    if monitor_key in active_odds_monitors:
        return {"status": "already_monitoring"}
    
    monitor = OddsMonitor(date, jyo_cd, race_no)
    active_odds_monitors[monitor_key] = monitor
    await monitor.start_monitoring()
    
    return {"status": "started", "monitor_key": monitor_key}


@router.post("/monitor/odds/stop")
async def stop_odds_monitoring(date: str, jyo_cd: str, race_no: int):
    """Stop monitoring odds for a specific race"""
    monitor_key = f"{date}_{jyo_cd}_{race_no}"
    
    if monitor_key not in active_odds_monitors:
        return {"status": "not_monitoring"}
    
    monitor = active_odds_monitors[monitor_key]
    await monitor.stop_monitoring()
    del active_odds_monitors[monitor_key]
    
    return {"status": "stopped", "monitor_key": monitor_key}


@router.get("/monitor/odds/status")
async def get_odds_monitoring_status():
    """Get status of all active odds monitors"""
    return {
        "active_monitors": [
            {
                "date": monitor.date,
                "jyo_cd": monitor.jyo_cd,
                "race_no": monitor.race_no,
                "running": monitor.running
            }
            for monitor in active_odds_monitors.values()
        ]
    }
@router.get("/performance/dashboard")
async def get_performance_dashboard(
    days: int = Query(30, ge=1, le=90)
):
    """Get performance dashboard data"""
    from src.monitoring.auto_backtest import get_backtest_summary, load_backtest_history
    from src.monitoring.drift_detector import DriftDetector
    
    # Get backtest summary
    summary = get_backtest_summary(days)
    
    # Get drift history
    drift_detector = DriftDetector()
    drift_history = drift_detector.get_drift_history(days)
    
    # Get recent predictions count
    from src.api.dependencies import get_dataframe
    df = get_dataframe()
    recent_predictions = len(df) if not df.empty else 0
    
    return {
        "backtest_summary": summary,
        "drift_history": drift_history,
        "recent_predictions": recent_predictions,
        "last_updated": datetime.now().isoformat()
    }


@router.get("/performance/metrics")
async def get_performance_metrics(
    days: int = Query(30, ge=1, le=90)
):
    """Get detailed performance metrics"""
    from src.monitoring.auto_backtest import load_backtest_history
    
    history = load_backtest_history()
    recent = history[-days:] if history else []
    
    # Extract metrics
    metrics = []
    for entry in recent:
        metrics.append({
            "date": entry.get("date"),
            "timestamp": entry.get("timestamp"),
            "auc": entry.get("auc"),
            "top1_accuracy": entry.get("top1_accuracy"),
            "roi": entry.get("sim_roi"),
            "total_races": entry.get("total_races"),
            "total_entries": entry.get("total_entries")
        })
    
    return metrics
@router.get("/cache/stats")
async def get_cache_stats(
    cache: RedisCache = Depends(get_cache)
):
    """Get cache statistics"""
    return cache.get_stats()


@router.post("/cache/reset-stats")
async def reset_cache_stats(
    cache: RedisCache = Depends(get_cache)
):
    """Reset cache statistics"""
    cache.reset_stats()
    return {"status": "reset", "message": "Cache statistics reset"}


@router.post("/cache/clear/{pattern}")
async def clear_cache_pattern(
    pattern: str,
    cache: RedisCache = Depends(get_cache)
):
    """Clear cache keys matching pattern"""
    success = cache.clear_pattern(pattern)
    return {
        "status": "success" if success else "error",
        "pattern": pattern,
        "message": f"Cache cleared for pattern: {pattern}" if success else "Failed to clear cache"
    }

# WebSocketリアルタイム通知
@router.websocket("/api/ws/test5")
async def websocket_test5(websocket: WebSocket):
    print("WebSocket connection attempt")
    await websocket.accept()
    print("WebSocket connection accepted")
    await websocket.send_text("Hello from WebSocket")
    await websocket.close()

@router.websocket("/test/ws")
async def test_websocket(websocket: WebSocket):
    await websocket.accept()
    await websocket.send_text("Hello from test WebSocket")
    await websocket.close()

@router.websocket("/test/ws3")
async def test_websocket3(websocket: WebSocket):
    print("WebSocket connection attempt")
    await websocket.accept()
    print("WebSocket connection accepted")
    await websocket.send_text("Hello from test WebSocket")
    await websocket.close()