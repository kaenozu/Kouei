"""
Collection Router - Data collection management endpoints
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Optional
from datetime import datetime

from src.collector.auto_collector import auto_collector
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["collection"])


class CollectionStatus(BaseModel):
    running: bool
    collection_interval: int
    latest_collections: list
    last_update: str


class BackfillRequest(BaseModel):
    start_date: str
    end_date: str


@router.post("/collection/start")
async def start_auto_collection(background_tasks: BackgroundTasks):
    """Start automatic data collection"""
    try:
        if auto_collector.running:
            return {"status": "running", "message": "Collection already running"}
        
        background_tasks.add_task(auto_collector.start_collection)
        logger.info("🚀 Auto collection started via API")
        
        return {
            "status": "started",
            "message": "Auto collection started",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to start collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collection/stop")
async def stop_auto_collection():
    """Stop automatic data collection"""
    try:
        auto_collector.stop_collection()
        logger.info("🛑 Auto collection stopped via API")
        
        return {
            "status": "stopped",
            "message": "Auto collection stopped",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to stop collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collection/status", response_model=CollectionStatus)
async def get_collection_status():
    """Get current collection status"""
    try:
        status = auto_collector.get_collection_status()
        return status
    except Exception as e:
        logger.error(f"Failed to get collection status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collection/backfill")
async def start_backfill(
    request: BackfillRequest,
    background_tasks: BackgroundTasks
):
    """Start backfilling missing data"""
    try:
        background_tasks.add_task(
            auto_collector.backfill_missing_data,
            request.start_date,
            request.end_date
        )
        
        logger.info(f"🔄 Backfill started: {request.start_date} to {request.end_date}")
        
        return {
            "status": "started",
            "message": f"Backfill started for {request.start_date} to {request.end_date}",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to start backfill: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collection/collect-today")
async def collect_today_data(background_tasks: BackgroundTasks):
    """Manually trigger today's data collection"""
    try:
        background_tasks.add_task(auto_collector.collect_today_data)
        
        logger.info("🔄 Manual collection triggered for today")
        
        return {
            "status": "triggered",
            "message": "Today's data collection triggered",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to trigger collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))
