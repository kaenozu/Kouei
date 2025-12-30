"""Enhanced API endpoints for new features"""
from fastapi import APIRouter, Query, HTTPException, BackgroundTasks
from typing import Optional, List, Dict
from datetime import datetime
import asyncio

from src.config.settings import settings
from src.utils.logger import get_logger, log_api_request
from src.analysis.compatibility_matrix import get_compatibility_analyzer
from src.analysis.weather_predictor import WeatherPredictor
from src.portfolio.formation_optimizer import FormationOptimizer
from src.inference.llm_commentary import get_commentary_generator, RaceContext
from src.collector.async_collector import AsyncRaceCollector

logger = get_logger()
router = APIRouter(prefix="/api/v2", tags=["Enhanced API"])


# Initialize components
compatibility_analyzer = get_compatibility_analyzer()
weather_predictor = WeatherPredictor()
formation_optimizer = FormationOptimizer()
commentary_generator = get_commentary_generator()


@router.get("/compatibility")
@log_api_request()
async def get_compatibility(
    racer_id: str,
    motor_no: str,
    stadium: str,
    course: int = Query(ge=1, le=6)
):
    """Get racer-motor-course compatibility analysis"""
    try:
        result = compatibility_analyzer.get_full_compatibility_matrix(
            racer_id=racer_id,
            motor_no=motor_no,
            stadium=stadium,
            course=course
        )
        return result
    except Exception as e:
        logger.error(f"Compatibility analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compatibility/racer/{racer_id}")
@log_api_request()
async def get_racer_course_stats(
    racer_id: str,
    stadium: Optional[str] = None
):
    """Get racer's course-wise performance statistics"""
    try:
        result = compatibility_analyzer.analyze_racer_course(racer_id, stadium)
        return {
            "racer_id": racer_id,
            "stadium": stadium or "all",
            "courses": {
                k: {
                    "score": v.score,
                    "win_rate": v.win_rate,
                    "sample_size": v.sample_size,
                    "confidence": v.confidence
                }
                for k, v in result.items()
            }
        }
    except Exception as e:
        logger.error(f"Racer course stats failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stadium-matrix/{stadium}")
@log_api_request()
async def get_stadium_matrix(stadium: str):
    """Get course performance matrix for a stadium"""
    try:
        df = compatibility_analyzer.build_stadium_matrix(stadium)
        if df.empty:
            return {"stadium": stadium, "matrix": []}
        return {
            "stadium": stadium,
            "matrix": df.to_dict('records')
        }
    except Exception as e:
        logger.error(f"Stadium matrix failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/weather/forecast")
@log_api_request()
async def get_weather_forecast(
    stadium: str,
    race_time: Optional[str] = None,
    wind_speed: float = 0,
    wind_direction: int = 0,
    wave_height: float = 0
):
    """Get comprehensive weather forecast and impact analysis"""
    try:
        if race_time:
            race_dt = datetime.strptime(race_time, "%Y%m%d%H%M")
        else:
            race_dt = datetime.now()
        
        current_conditions = {
            "wind_speed": wind_speed,
            "wind_direction": wind_direction,
            "wave_height": wave_height
        }
        
        forecast = weather_predictor.get_comprehensive_forecast(
            stadium=stadium,
            race_time=race_dt,
            current_conditions=current_conditions
        )
        return forecast
    except Exception as e:
        logger.error(f"Weather forecast failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/betting/optimize")
@log_api_request()
async def optimize_betting(data: Dict):
    """Get optimized betting recommendations"""
    try:
        predictions = data.get("predictions", [])
        tansho_odds = {int(k): v for k, v in data.get("tansho_odds", {}).items()}
        exacta_odds = {
            tuple(map(int, k.split("-"))): v 
            for k, v in data.get("exacta_odds", {}).items()
        }
        trifecta_odds = {
            tuple(map(int, k.split("-"))): v 
            for k, v in data.get("trifecta_odds", {}).items()
        }
        budget = data.get("budget", 10000)
        
        formation_optimizer.bankroll = budget
        
        result = formation_optimizer.get_optimal_strategy(
            predictions=predictions,
            tansho_odds=tansho_odds,
            exacta_odds=exacta_odds,
            trifecta_odds=trifecta_odds,
            budget=budget
        )
        
        # Convert dataclass to dict
        result["recommendations"] = [
            {
                "bet_type": r.bet_type,
                "combination": r.combination,
                "probability": r.probability,
                "odds": r.odds,
                "expected_value": r.expected_value,
                "kelly_fraction": r.kelly_fraction,
                "recommended_amount": r.recommended_amount,
                "risk_level": r.risk_level
            }
            for r in result["recommendations"]
        ]
        
        return result
    except Exception as e:
        logger.error(f"Betting optimization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/betting/formation")
@log_api_request()
async def get_formation_recommendation(data: Dict):
    """Get formation bet recommendation"""
    try:
        predictions = data.get("predictions", [])
        trifecta_odds = {
            tuple(map(int, k.split("-"))): v 
            for k, v in data.get("odds", {}).items()
        }
        max_cost = data.get("max_cost", 5000)
        
        formation = formation_optimizer.optimize_formation(
            predictions=predictions,
            odds=trifecta_odds,
            max_cost=max_cost
        )
        
        if not formation:
            return {"error": "No suitable formation found"}
        
        return {
            "heads": formation.heads,
            "seconds": formation.seconds,
            "thirds": formation.thirds,
            "total_combinations": formation.total_combinations,
            "total_cost": formation.total_cost,
            "expected_return": formation.expected_return,
            "expected_value": formation.expected_value
        }
    except Exception as e:
        logger.error(f"Formation recommendation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/commentary/generate")
@log_api_request()
async def generate_commentary(data: Dict):
    """Generate AI commentary for a race"""
    try:
        context = RaceContext(
            stadium_name=data.get("stadium_name", ""),
            race_no=data.get("race_no", 1),
            date=data.get("date", ""),
            weather=data.get("weather", "晴"),
            wind_speed=data.get("wind_speed", 0),
            wind_direction=data.get("wind_direction", "無風"),
            wave_height=data.get("wave_height", 0),
            predictions=data.get("predictions", []),
            top_factors=data.get("top_factors", []),
            confidence=data.get("confidence", "C"),
            similar_races=data.get("similar_races")
        )
        
        commentary = await commentary_generator.generate_async(context)
        return {"commentary": commentary}
    except Exception as e:
        logger.error(f"Commentary generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync/async")
@log_api_request()
async def trigger_async_sync(
    background_tasks: BackgroundTasks,
    start_date: str,
    end_date: Optional[str] = None
):
    """Trigger async data collection"""
    if not end_date:
        end_date = start_date
    
    async def run_collection():
        async with AsyncRaceCollector() as collector:
            start = datetime.strptime(start_date, "%Y%m%d").date()
            end = datetime.strptime(end_date, "%Y%m%d").date()
            return await collector.collect_range(start, end)
    
    # Run in background
    background_tasks.add_task(asyncio.run, run_collection())
    
    return {
        "status": "started",
        "start_date": start_date,
        "end_date": end_date
    }


@router.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.0.0",
        "features": {
            "onnx_enabled": settings.use_onnx,
            "llm_provider": settings.llm_provider,
            "redis_enabled": True,
            "whale_detection": settings.enable_whale_detection
        }
    }
