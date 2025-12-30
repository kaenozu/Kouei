"""Sync Router - Data synchronization endpoints"""
from fastapi import APIRouter, Depends, BackgroundTasks, Query
from datetime import datetime
import asyncio
import subprocess

from src.api.dependencies import get_ledger, get_cache, refresh_dataframe
from src.cache.redis_client import RedisCache
from src.utils.logger import logger

router = APIRouter(prefix="/api", tags=["sync"])

# Global state
last_sync_time = None
sync_lock = False


@router.get("/sync")
async def sync_data(background_tasks: BackgroundTasks):
    """Trigger background data synchronization"""
    global last_sync_time, sync_lock
    
    now = datetime.now()
    if last_sync_time and (now - last_sync_time).total_seconds() < 300:  # 5 min cooldown
        return {
            "status": "skipped",
            "reason": "recently_updated",
            "last_sync": last_sync_time.isoformat()
        }
    
    if sync_lock:
        return {"status": "skipped", "reason": "already_running"}
    
    background_tasks.add_task(run_sync)
    return {"status": "started"}


@router.post("/fetch")
async def trigger_fetch(date: str = Query(..., pattern=r"^\d{8}$")):
    """Trigger data collection for a specific date"""
    try:
        # 1. Download
        result1 = subprocess.run(
            ["python", "-m", "src.collector.collect_data", "--start_date", date, "--end_date", date],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        # 2. Rebuild dataset
        result2 = subprocess.run(
            ["python", "-m", "src.features.build_dataset"],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        # Refresh cached dataframe
        refresh_dataframe()
        
        return {
            "status": "success",
            "message": f"Data for {date} fetched and dataset rebuilt."
        }
    except subprocess.TimeoutExpired:
        return {"status": "error", "message": "Operation timed out"}
    except Exception as e:
        logger.error(f"Fetch error: {e}")
        return {"status": "error", "message": str(e)}


@router.post("/mlops/retrain")
async def trigger_retraining(background_tasks: BackgroundTasks):
    """Trigger MLOps pipeline for model retraining"""
    try:
        background_tasks.add_task(_run_retraining)
        return {"status": "started", "message": "Retraining pipeline started"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


async def _run_retraining():
    """Run retraining in background"""
    try:
        logger.info("MLOps: Starting retraining...")
        result = subprocess.run(
            ["python", "-m", "src.model.train_model"],
            capture_output=True,
            text=True,
            timeout=1800  # 30 minutes
        )
        logger.info(f"Retraining completed: {result.returncode}")
    except Exception as e:
        logger.error(f"Retraining error: {e}")


def run_sync():
    """Run synchronization in background"""
    global sync_lock, last_sync_time
    
    if sync_lock:
        return
    
    sync_lock = True
    try:
        logger.info("Starting background sync...")
        now = datetime.now()
        
        from src.collector.collect_data import RaceCollector
        from src.features.build_dataset import build_dataset
        
        collector = RaceCollector()
        collector.collect(now.date(), now.date())
        
        build_dataset()
        last_sync_time = now
        
        # Refresh cached dataframe
        refresh_dataframe()
        
        # Check for auto-training
        _check_auto_training()
        
        logger.info("Background sync completed.")
    except Exception as e:
        logger.error(f"Error during background sync: {e}")
    finally:
        sync_lock = False


def _check_auto_training():
    """Check if auto-training is needed"""
    import os
    import json
    import pandas as pd
    
    DATA_PATH = "data/processed/race_data.csv"
    
    config = {}
    if os.path.exists("config.json"):
        try:
            with open("config.json", "r") as f:
                config = json.load(f)
        except:
            pass
    
    threshold = config.get("auto_train_threshold_races", 1000)
    last_size = config.get("last_trained_dataset_size", 0)
    
    if os.path.exists(DATA_PATH):
        df = pd.read_csv(DATA_PATH)
        current_size = len(df)
        if current_size - last_size >= threshold:
            logger.info(f"Re-training needed: {current_size} rows (last: {last_size})")
            try:
                from src.model.train_model import train_model
                train_model()
                config["last_trained_dataset_size"] = current_size
                with open("config.json", "w") as f:
                    json.dump(config, f, indent=4)
                logger.info("Auto-training completed successfully.")
            except Exception as e:
                logger.error(f"Error during auto-training: {e}")


def get_sync_status():
    """Get current sync status"""
    return {
        "last_sync": last_sync_time.isoformat() if last_sync_time else None,
        "is_running": sync_lock
    }
