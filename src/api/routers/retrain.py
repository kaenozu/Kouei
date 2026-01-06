"""モデル再トレーニングAPIルーター

ドリフト検出・自動再トレーニング機能を提供。
"""
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime
import json
import os

from src.utils.logger import logger
from src.model.auto_retrain import get_auto_retrain_pipeline, run_auto_retrain_check

router = APIRouter(prefix="/api/retrain", tags=["Retraining"])


class RetrainStatus(BaseModel):
    last_retrain: Optional[str] = None
    is_running: bool = False
    last_result: Optional[Dict[str, Any]] = None


class RetrainTriggerResponse(BaseModel):
    status: str
    message: str
    task_id: Optional[str] = None


# 実行中フラグ
_retrain_running = False
_last_retrain_result: Optional[Dict[str, Any]] = None


@router.get("/status")
async def get_retrain_status() -> RetrainStatus:
    """再トレーニングのステータスを取得"""
    pipeline = get_auto_retrain_pipeline()
    return RetrainStatus(
        last_retrain=pipeline.last_retrain_time.isoformat() if pipeline.last_retrain_time else None,
        is_running=_retrain_running,
        last_result=_last_retrain_result
    )


@router.post("/trigger")
async def trigger_retrain(background_tasks: BackgroundTasks, force: bool = False) -> RetrainTriggerResponse:
    """再トレーニングを手動トリガー"""
    global _retrain_running
    
    if _retrain_running:
        return RetrainTriggerResponse(
            status="busy",
            message="Retrain is already running"
        )
    
    async def run_retrain_task():
        global _retrain_running, _last_retrain_result
        _retrain_running = True
        try:
            pipeline = get_auto_retrain_pipeline()
            if force:
                _last_retrain_result = await pipeline.run_retrain()
            else:
                _last_retrain_result = await pipeline.check_and_retrain()
        finally:
            _retrain_running = False
    
    background_tasks.add_task(run_retrain_task)
    
    return RetrainTriggerResponse(
        status="started",
        message="Retrain task started in background",
        task_id=datetime.now().strftime("%Y%m%d%H%M%S")
    )


@router.get("/history")
async def get_retrain_history() -> Dict[str, Any]:
    """再トレーニング履歴を取得"""
    history_file = "data/retrain_history.json"
    if os.path.exists(history_file):
        with open(history_file, 'r') as f:
            return json.load(f)
    return {"message": "No retrain history found"}


@router.post("/check-drift")
async def check_drift_and_retrain(background_tasks: BackgroundTasks) -> Dict[str, Any]:
    """ドリフトをチェックし、必要であれば再トレーニング"""
    global _retrain_running
    
    if _retrain_running:
        return {
            "status": "busy",
            "message": "Retrain is already running"
        }
    
    # ドリフトチェック
    from src.monitoring.drift_detector import DriftDetector
    detector = DriftDetector()
    drift_result = detector.check_drift()
    
    pipeline = get_auto_retrain_pipeline()
    should_retrain = pipeline.should_retrain(drift_result)
    
    if should_retrain:
        async def run_retrain_task():
            global _retrain_running, _last_retrain_result
            _retrain_running = True
            try:
                _last_retrain_result = await pipeline.run_retrain()
            finally:
                _retrain_running = False
        
        background_tasks.add_task(run_retrain_task)
        
        return {
            "status": "retrain_triggered",
            "drift_detected": True,
            "drift_result": drift_result
        }
    else:
        return {
            "status": "no_action",
            "drift_detected": drift_result.get('drift_detected', False),
            "drift_result": drift_result
        }
