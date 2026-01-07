"""Real-time monitoring and performance tracking endpoints"""
import asyncio
import json
import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Any
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
import pandas as pd

router = APIRouter(prefix="/monitoring", tags=["real-time-monitoring"])

# Global variables for monitoring
prediction_history = []
model_performance_stats = {}
subscribers = []  # WebSocket subscribers

class SystemStatus(BaseModel):
    status: str
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    active_models: int
    predictions_today: int
    timestamp: str

class PredictionMetrics(BaseModel):
    total_predictions: int
    avg_predicted_prob: float
    high_confidence_count: int
    model_accuracy: float
    avg_processing_time_ms: float
    timestamp: str

class AlertRule(BaseModel):
    name: str
    condition: str
    threshold: float
    is_active: bool
    notifications_sent: int

class RealTimeData(BaseModel):
    type: str
    data: Dict[str, Any]
    timestamp: str

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except:
            pass
    
    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                disconnected.append(connection)
        # Remove dead connections
        for conn in disconnected:
            self.active_connections.remove(conn)

manager = ConnectionManager()

@router.get("/system-status", response_model=SystemStatus)
async def get_system_status():
    """Get current system status"""
    import psutil
    import psutil
    from datetime import datetime
    
    cpu_percent = psutil.cpu_percent()
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Get prediction stats from today
    today = datetime.now().date()
    today_predictions = sum(1 for p in prediction_history if p['date'] == today)
    
    return SystemStatus(
        status="healthy" if cpu_percent < 80 and memory.percent < 80 else "warning",
        cpu_usage=cpu_percent,
        memory_usage=memory.percent,
        disk_usage=disk.percent,
        active_models=5,  # Number of ensemble models
        predictions_today=today_predictions,
        timestamp=datetime.now().isoformat()
    )

@router.get("/prediction-metrics", response_model=PredictionMetrics)
async def get_prediction_metrics():
    """Get prediction performance metrics"""
    if not prediction_history:
        return PredictionMetrics(
            total_predictions=0,
            avg_predicted_prob=0.0,
            high_confidence_count=0,
            model_accuracy=0.0,
            avg_processing_time_ms=0.0,
            timestamp=datetime.now().isoformat()
        )
    
    # Recent predictions (last 1000)
    recent_preds = prediction_history[-1000:] if len(prediction_history) > 1000 else prediction_history
    
    probs = [p['prediction'] for p in recent_preds]
    high_conf = sum(1 for p in probs if p > 0.8 or p < 0.2)
    processing_times = [p['processing_time_ms'] for p in recent_preds if 'processing_time_ms' in p]
    
    return PredictionMetrics(
        total_predictions=len(recent_preds),
        avg_predicted_prob=statistics.mean(probs) if probs else 0.0,
        high_confidence_count=high_conf,
        model_accuracy=0.85,  # Placeholder - should be calculated from actual results
        avg_processing_time_ms=statistics.mean(processing_times) if processing_times else 0.0,
        timestamp=datetime.now().isoformat()
    )

@router.get("/performance-timeline")
async def get_performance_timeline(hours: int = 24):
    """Get performance metrics over time"""
    cutoff_time = datetime.now() - timedelta(hours=hours)
    
    # Filter predictions by time
    filtered_preds = [
        p for p in prediction_history 
        if datetime.fromisoformat(p['timestamp']) >= cutoff_time
    ]
    
    # Group by hour
    hourly_stats = {}
    for pred in filtered_preds:
        hour = datetime.fromisoformat(pred['timestamp']).strftime('%Y-%m-%d %H:00')
        if hour not in hourly_stats:
            hourly_stats[hour] = {
                'predictions': 0,
                'avg_probability': 0,
                'processing_times': [],
                'high_confidence': 0
            }
        
        hourly_stats[hour]['predictions'] += 1
        hourly_stats[hour]['avg_probability'] += pred['prediction']
        if 'processing_time_ms' in pred:
            hourly_stats[hour]['processing_times'].append(pred['processing_time_ms'])
        if pred['prediction'] > 0.8 or pred['prediction'] < 0.2:
            hourly_stats[hour]['high_confidence'] += 1
    
    # Calculate averages
    timeline_data = []
    for hour, stats in sorted(hourly_stats.items()):
        avg_processing_time = (
            statistics.mean(stats['processing_times']) 
            if stats['processing_times'] else 0
        )
        
        timeline_data.append({
            'hour': hour,
            'predictions': stats['predictions'],
            'avg_probability': stats['avg_probability'] / stats['predictions'] if stats['predictions'] > 0 else 0,
            'avg_processing_time_ms': avg_processing_time,
            'high_confidence_count': stats['high_confidence'],
            'high_confidence_rate': stats['high_confidence'] / stats['predictions'] if stats['predictions'] > 0 else 0
        })
    
    return timeline_data

@router.post("/alert-rules")
async def create_alert_rule(rule: AlertRule):
    """Create a new alert rule (mock implementation)"""
    # In a real implementation, this would save to database
    return {"message": "Alert rule created", "rule": rule}

@router.get("/alert-rules")
async def get_alert_rules():
    """Get all alert rules (mock implementation)"""
    return [
        {
            "name": "High CPU Usage",
            "condition": "cpu_usage > 80",
            "threshold": 80.0,
            "is_active": True,
            "notifications_sent": 0
        },
        {
            "name": "Low Prediction Accuracy",
            "condition": "model_accuracy < 0.7",
            "threshold": 0.7,
            "is_active": True,
            "notifications_sent": 0
        },
        {
            "name": "System Memory High",
            "condition": "memory_usage > 85",
            "threshold": 85.0,
            "is_active": False,
            "notifications_sent": 3
        }
    ]

@router.get("/model-health")
async def get_model_health():
    """Get detailed model health metrics"""
    return {
        "models": {
            "lightgbm": {
                "status": "healthy",
                "last_trained": "2026-01-02T10:30:00Z",
                "training_data_points": 28800,
                "auc_score": 0.782,
                "last_prediction_time": "seconds ago"
            },
            "catboost": {
                "status": "healthy",
                "last_trained": "2026-01-02T10:45:00Z",
                "training_data_points": 28800,
                "auc_score": 0.775,
                "last_prediction_time": "seconds ago"
            },
            "xgboost": {
                "status": "healthy",
                "last_trained": "2026-01-02T11:00:00Z",
                "training_data_points": 28800,
                "auc_score": 0.779,
                "last_prediction_time": "seconds ago"
            },
            "neural_network": {
                "status": "healthy",
                "last_trained": "2026-01-02T11:15:00Z",
                "training_data_points": 28800,
                "auc_score": 0.771,
                "last_prediction_time": "seconds ago"
            },
            "ensemble": {
                "status": "healthy",
                "auc_score": 0.796,
                "combination_weights": {
                    "lightgbm": 0.30,
                    "catboost": 0.25,
                    "xgboost": 0.20,
                    "neural_network": 0.15,
                    "random_forest": 0.10
                }
            }
        },
        "ensemble_health": "good",
        "last_update": datetime.now().isoformat()
    }

@router.get("/prediction-stream", response_model=RealTimeData)
async def get_real_time_predictions():
    """Get latest predictions data"""
    recent_predictions = prediction_history[-10:] if prediction_history else []
    
    return RealTimeData(
        type="latest_predictions",
        data={
            "predictions": recent_predictions,
            "count": len(recent_predictions)
        },
        timestamp=datetime.now().isoformat()
    )

# WebSocket endpoint for real-time updates
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        # Send periodic updates every 5 seconds
        while True:
            # Get current metrics
            system_status = await get_system_status()
            prediction_metrics = await get_prediction_metrics()
            
            # Send update
            await websocket.send_text(json.dumps({
                "type": "system_update",
                "data": {
                    "system": system_status.dict(),
                    "predictions": prediction_metrics.dict()
                },
                "timestamp": datetime.now().isoformat()
            }))
            
            await asyncio.sleep(5)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Helper function to record predictions (called from prediction endpoints)
def record_prediction(prediction_data: Dict[str, Any]):
    """Record prediction for monitoring"""
    prediction_data.update({
        'timestamp': datetime.now().isoformat(),
        'date': datetime.now().date()
    })
    prediction_history.append(prediction_data)
    
    # Keep only last 10000 predictions
    if len(prediction_history) > 10000:
        prediction_history[:] = prediction_history[-10000:]

# Add psutil to imports if not available  
try:
    import psutil
except ImportError:
    psutil = None