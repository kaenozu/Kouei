"""Notifications Router - Alert management"""
from fastapi import APIRouter, Query, BackgroundTasks
from typing import Optional
from datetime import datetime

from src.notifications.notifier import get_notifier, RaceAlert, Notifier
from src.utils.logger import logger

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


@router.post("/test")
async def test_notification(
    channel: str = Query("discord", pattern="^(discord|line|all)$")
):
    """Send a test notification"""
    notifier = get_notifier()
    
    test_alert = RaceAlert(
        date=datetime.now().strftime("%Y%m%d"),
        jyo_cd="21",
        jyo_name="芦屋",
        race_no=12,
        race_time="15:30",
        boat_no=1,
        racer_name="テスト選手",
        probability=0.72,
        confidence="A",
        tansho_odds=2.5,
        ev=0.15
    )
    
    results = {}
    
    if channel in ("discord", "all"):
        embed = notifier.format_discord_embed(test_alert)
        results["discord"] = await notifier.send_discord("🔔 テスト通知", embeds=[embed])
    
    if channel in ("line", "all"):
        message = notifier.format_alert(test_alert)
        results["line"] = await notifier.send_line(message)
    
    return {"status": "sent", "results": results}


@router.get("/config")
async def get_notification_config():
    """Get current notification configuration"""
    notifier = get_notifier()
    
    return {
        "discord_configured": bool(notifier.discord_webhook),
        "line_configured": bool(notifier.line_token),
        "threshold": 0.6  # Default threshold for alerts
    }


@router.post("/alert")
async def send_custom_alert(
    jyo_name: str,
    race_no: int,
    boat_no: int,
    probability: float,
    racer_name: str = "",
    race_time: str = "",
    confidence: str = "B"
):
    """Send a custom alert"""
    notifier = get_notifier()
    
    alert = RaceAlert(
        date=datetime.now().strftime("%Y%m%d"),
        jyo_cd="00",
        jyo_name=jyo_name,
        race_no=race_no,
        race_time=race_time or datetime.now().strftime("%H:%M"),
        boat_no=boat_no,
        racer_name=racer_name,
        probability=probability,
        confidence=confidence
    )
    
    success = await notifier.send_alert(alert)
    
    return {"status": "sent" if success else "failed", "alert": alert.__dict__}


@router.get("/high-value-races")
async def get_high_value_races(
    threshold: float = Query(0.55, ge=0.3, le=0.9),
    send_notification: bool = Query(False)
):
    """Find high-value races and optionally send notifications"""
    from src.model.ensemble import get_ensemble
    import pandas as pd
    import os
    
    DATA_PATH = "data/processed/race_data.csv"
    
    if not os.path.exists(DATA_PATH):
        return {"error": "No data available"}
    
    df = pd.read_csv(DATA_PATH)
    today = datetime.now().strftime("%Y%m%d")
    
    # Filter to today's races without results
    df_today = df[df['date'].astype(str) == today]
    
    if len(df_today) == 0:
        return {"races": [], "message": "No races today"}
    
    # Get predictions
    try:
        from src.features.preprocessing import preprocess, FEATURES
        df_proc = preprocess(df_today.copy(), is_training=False)
        
        if len(df_proc) == 0:
            return {"races": [], "message": "No valid races after preprocessing"}
        
        ensemble = get_ensemble()
        predictions = ensemble.predict(df_proc[FEATURES])
        df_proc['pred_prob'] = predictions
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        return {"error": str(e)}
    
    # Find high probability predictions
    high_value = df_proc[df_proc['pred_prob'] >= threshold].copy()
    
    results = []
    notifier = get_notifier()
    
    for _, row in high_value.iterrows():
        race_info = {
            "date": str(row['date']),
            "jyo_cd": str(row['jyo_cd']),
            "jyo_name": Notifier.VENUE_NAMES.get(str(row['jyo_cd']).zfill(2), "不明"),
            "race_no": int(row['race_no']),
            "boat_no": int(row['boat_no']),
            "racer_name": str(row.get('racer_name', '')),
            "probability": round(float(row['pred_prob']), 3),
            "confidence": "S" if row['pred_prob'] >= 0.7 else "A" if row['pred_prob'] >= 0.6 else "B"
        }
        results.append(race_info)
        
        # Send notification if requested
        if send_notification:
            alert = RaceAlert(
                date=race_info["date"],
                jyo_cd=race_info["jyo_cd"],
                jyo_name=race_info["jyo_name"],
                race_no=race_info["race_no"],
                race_time=str(row.get('start_time', '')),
                boat_no=race_info["boat_no"],
                racer_name=race_info["racer_name"],
                probability=race_info["probability"],
                confidence=race_info["confidence"]
            )
            await notifier.send_alert(alert)
    
    # Sort by probability
    results.sort(key=lambda x: -x["probability"])
    
    return {
        "threshold": threshold,
        "count": len(results),
        "races": results[:20]  # Top 20
    }
