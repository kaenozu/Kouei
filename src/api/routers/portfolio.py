"""Portfolio Router - Portfolio and simulation endpoints"""
from fastapi import APIRouter, Depends, Query, BackgroundTasks
from typing import Optional
import pandas as pd
import os
import json

from src.api.dependencies import (
    get_ledger, get_cache, get_dataframe, get_predictor
)
from src.api.schemas.common import BacktestRequest, SimulationSummary
from src.portfolio.ledger import PortfolioLedger
from src.simulation.simulator import get_simulation_history, simulate
from src.simulation.monte_carlo import MonteCarloSimulator
from src.cache.redis_client import RedisCache
from src.utils.logger import logger

router = APIRouter(prefix="/api", tags=["portfolio"])

DATA_PATH = "data/processed/race_data.csv"


@router.get("/portfolio")
async def get_portfolio(
    ledger: PortfolioLedger = Depends(get_ledger),
    cache: RedisCache = Depends(get_cache)
):
    """Get portfolio summary"""
    # Check cache
    cached = cache.get("portfolio:summary")
    if cached:
        return cached
    
    summary = ledger.get_summary()
    cache.set("portfolio:summary", summary, ttl=60)
    return summary


@router.get("/simulation")
async def get_simulation(
    threshold: float = Query(0.4, ge=0.1, le=0.9),
    cache: RedisCache = Depends(get_cache)
):
    """Get historical simulation results"""
    try:
        cache_key = f"simulation:{threshold}"
        
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        history = get_simulation_history(threshold=threshold)
        summary = simulate(threshold=threshold)
        
        result = {
            "history": history,
            "summary": summary
        }
        
        cache.set(cache_key, result, ttl=300)
        
        return result
    except Exception as e:
        logger.error(f"Simulation error: {e}")
        return {"error": str(e)}


@router.post("/backtest")
async def backtest_strategy(filters: BacktestRequest):
    """Run backtest with custom filters"""
    try:
        df = get_dataframe()
        if df.empty:
            return {"error": "Dataset not found"}
        
        # Apply filters
        if filters.stadium:
            df = df[df['jyo_cd'].astype(str).str.zfill(2) == filters.stadium.zfill(2)]
        
        # Filter to only completed races
        df = df[df['rank'].notna()]
        
        if df.empty:
            return {
                "roi": 0.0,
                "hit_rate": 0.0,
                "profit": 0,
                "total_bets": 0,
                "wins": 0
            }
        
        results = simulate(df=df, threshold=filters.min_prob)
        return results
    except Exception as e:
        logger.error(f"Backtest error: {e}")
        return {"error": str(e)}


@router.get("/monte-carlo/{strategy_name}")
async def run_monte_carlo(
    strategy_name: str,
    n_simulations: int = Query(1000, ge=100, le=10000),
    cache: RedisCache = Depends(get_cache)
):
    """Run Monte Carlo simulation for a strategy"""
    try:
        cache_key = f"monte-carlo:{strategy_name}:{n_simulations}"
        
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        df = get_dataframe()
        if df.empty:
            return {"error": "Dataset not found"}
        
        simulator = MonteCarloSimulator(df)
        
        # Load strategy
        strategies_path = "config/strategies.json"
        if os.path.exists(strategies_path):
            with open(strategies_path, 'r') as f:
                strategies = json.load(f)
            
            strategy = next((s for s in strategies if s['name'] == strategy_name), None)
            if not strategy:
                return {"error": "Strategy not found"}
            
            result = simulator.simulate_strategy(strategy.get('filters', {}), n_simulations)
            
            cache.set(cache_key, result, ttl=600)
            
            return result
        else:
            return {"error": "No strategies found"}
    except Exception as e:
        logger.error(f"Monte Carlo error: {e}")
        return {"error": str(e)}


@router.get("/strategies")
async def get_active_strategies():
    """Get list of active strategies"""
    path = "config/strategies.json"
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


@router.post("/strategy/discover")
async def trigger_strategy_discovery(background_tasks: BackgroundTasks):
    """Trigger strategy discovery in background"""
    from src.strategy.finder import find_strategies
    background_tasks.add_task(find_strategies)
    return {"status": "started", "message": "Strategy discovery started"}
