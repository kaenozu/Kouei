"""
Kouei API - AI-powered boat race prediction system

Refactored modular API with separated routers for better maintainability.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
from datetime import datetime

from src.api.routers import (
    prediction_router,
    races_router,
    portfolio_router,
    analysis_router,
    betting_router,
    sync_router,
    system_router,
)
from src.api.routers.analytics import router as analytics_router
from src.api.dependencies import get_predictor, get_dataframe
from src.api.routers.system import broadcast_event, active_connections
from src.api.routers.sync import run_sync, last_sync_time
from src.monitoring.drift_detector import DriftDetector
from src.analysis.venue_scoring import VenueScorer
from src.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("🚀 Starting Kouei API...")
    
    # Warm up models and data
    try:
        logger.info("Warming up predictor...")
        get_predictor()
        logger.info("Loading initial data...")
        get_dataframe()
        logger.info("✅ Warmup complete")
    except Exception as e:
        logger.warning(f"Warmup failed: {e}")
    
    # Start background pipeline
    pipeline_task = asyncio.create_task(unified_streaming_pipeline())
    
    yield
    
    # Shutdown
    logger.info("🚫 Shutting down Kouei API...")
    pipeline_task.cancel()
    try:
        await pipeline_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="Kyotei AI API",
    description="AI-powered boat race prediction system",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(prediction_router)
app.include_router(races_router)
app.include_router(portfolio_router)
app.include_router(analysis_router)
app.include_router(betting_router)
app.include_router(sync_router)
app.include_router(system_router)
app.include_router(analytics_router)

# Include enhanced API router if available
try:
    from src.api.enhanced_api import router as enhanced_router
    app.include_router(enhanced_router)
except ImportError as e:
    logger.warning(f"Enhanced API not loaded: {e}")


# Background pipeline
async def unified_streaming_pipeline():
    """Unified background loop for Sync, Sniper, Drift, and Venue Scoring"""
    logger.info("🚀 Unified Streaming Pipeline Started")
    
    drift_detector = DriftDetector()
    venue_scorer = VenueScorer()
    last_drift_check = None
    notified_races = set()
    
    while True:
        try:
            now = datetime.now()
            
            # 1. Periodic Sync (Every 15 min)
            global last_sync_time
            if not last_sync_time or (now - last_sync_time).total_seconds() > 900:
                logger.info("🔄 Pipeline: Triggering Sync")
                try:
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, run_sync)
                except Exception as e:
                    logger.error(f"Sync Error: {e}")
            
            # 2. Sniper Mode (Real-time race alerts)
            await run_sniper_cycle(now, notified_races)
            
            # 3. Daily Maintenance (Drift & Venue Scoring)
            if not last_drift_check or last_drift_check.date() != now.date():
                logger.info("🧹 Pipeline: Running Daily Maintenance")
                drift_report = drift_detector.check_drift()
                venue_scorer.calculate_scores()
                last_drift_check = now
                
                if drift_report.get("drift_detected"):
                    await broadcast_event("DRIFT_ALERT", drift_report)
            
            await asyncio.sleep(60)
            
        except asyncio.CancelledError:
            logger.info("Pipeline cancelled")
            break
        except Exception as e:
            logger.error(f"Pipeline Error: {e}")
            await asyncio.sleep(60)


async def run_sniper_cycle(now: datetime, notified_races: set):
    """Sniper mode for real-time race alerts"""
    try:
        import os
        import pandas as pd
        
        DATA_PATH = "data/processed/race_data.csv"
        date_str = now.strftime('%Y%m%d')
        
        if os.path.exists(DATA_PATH):
            df = pd.read_csv(DATA_PATH)
            today_df = df[df['date'].astype(str).str.replace('-', '') == date_str]
            
            for (jyo, race), group in today_df.groupby(['jyo_cd', 'race_no']):
                if 'start_time' not in group.columns:
                    continue
                    
                start_time_str = group['start_time'].iloc[0]
                if pd.isna(start_time_str):
                    continue
                
                try:
                    st_dt = datetime.strptime(f"{date_str} {start_time_str}", "%Y%m%d %H:%M")
                    diff = (st_dt - now).total_seconds()
                    
                    # Alert 4-6 minutes before race
                    if 240 <= diff <= 360:
                        race_key = f"SNIPER_{date_str}_{jyo}_{race}"
                        if race_key not in notified_races:
                            logger.info(f"🎯 Sniper: Target detected {jyo} R{race}")
                            notified_races.add(race_key)
                            await broadcast_event("SNIPER_ALERT", {
                                "jyo": str(jyo),
                                "race": int(race),
                                "time": str(start_time_str)
                            })
                except:
                    pass
                    
    except Exception as e:
        logger.error(f"Sniper Cycle Error: {e}")


@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": "Kouei AI API",
        "version": "3.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
