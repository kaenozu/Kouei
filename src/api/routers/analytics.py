"""Analytics Router - Performance tracking and visualization"""
from fastapi import APIRouter, Depends, Query
from datetime import datetime, timedelta
import pandas as pd
import os
from typing import Optional
from collections import defaultdict

from src.api.dependencies import get_predictor, get_cache
from src.model.predictor import Predictor
from src.cache.redis_client import RedisCache
from src.utils.logger import logger

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

DATA_PATH = "data/processed/race_data.csv"


@router.get("/accuracy")
async def get_prediction_accuracy(
    days: int = Query(7, ge=1, le=30),
    predictor: Predictor = Depends(get_predictor),
    cache: RedisCache = Depends(get_cache)
):
    """Get prediction accuracy over recent days"""
    cache_key = f"analytics:accuracy:{days}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    if not os.path.exists(DATA_PATH):
        return {"error": "No data available"}
    
    df = pd.read_csv(DATA_PATH)
    df['date'] = pd.to_datetime(df['date'].astype(str), format='%Y%m%d')
    
    # Use max date in data as reference
    max_date = df['date'].max()
    cutoff = max_date - timedelta(days=days)
    recent = df[df['date'] >= cutoff]
    
    if len(recent) == 0:
        return {"error": "No recent data", "days": days}
    
    # Filter out rows with no result (NaN rank)
    recent = recent[recent['rank'].notna()]
    recent = recent[~recent['rank'].isin(['', 'nan', 'NaN'])]
    
    if len(recent) == 0:
        return {"error": "No completed races in period", "days": days}
    
    # Add target column if not exists (rank == '1' means win)
    if 'target' not in recent.columns:
        recent = recent.copy()
        recent['target'] = (recent['rank'].astype(str) == '1').astype(int)
    
    # Group by date for daily accuracy
    daily_stats = []
    for date, group in recent.groupby(recent['date'].dt.strftime('%Y-%m-%d')):
        # 1着予測（boat_no == 1 の選手が実際に1着になったか）
        boat1_data = group[group['boat_no'] == 1]
        if len(boat1_data) > 0:
            hit_rate = boat1_data['target'].mean()
        else:
            hit_rate = 0
        
        daily_stats.append({
            "date": date,
            "total_races": len(group) // 6,  # 6 boats per race
            "hit_rate": round(hit_rate * 100, 1)
        })
    
    # Overall stats
    total_races = len(recent) // 6
    boat1_overall = recent[recent['boat_no'] == 1]
    overall_hit_rate = boat1_overall['target'].mean() * 100 if len(boat1_overall) > 0 else 0
    
    result = {
        "period_days": days,
        "total_races": total_races,
        "overall_hit_rate": round(overall_hit_rate, 1),
        "daily_stats": sorted(daily_stats, key=lambda x: x['date'])
    }
    
    cache.set(cache_key, result, ttl=1800)  # 30 min cache
    return result


@router.get("/roi")
async def get_roi_stats(
    days: int = Query(7, ge=1, le=30),
    bet_amount: int = Query(100, ge=100, le=10000),
    cache: RedisCache = Depends(get_cache)
):
    """Calculate simulated ROI based on historical predictions"""
    cache_key = f"analytics:roi:{days}:{bet_amount}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    if not os.path.exists(DATA_PATH):
        return {"error": "No data available"}
    
    df = pd.read_csv(DATA_PATH)
    df['date'] = pd.to_datetime(df['date'].astype(str), format='%Y%m%d')
    
    # Use max date in data as reference
    max_date = df['date'].max()
    cutoff = max_date - timedelta(days=days)
    recent = df[df['date'] >= cutoff]
    
    if len(recent) == 0:
        return {"error": "No recent data"}
    
    # Filter out rows with no result
    recent = recent[recent['rank'].notna()]
    recent = recent[~recent['rank'].isin(['', 'nan', 'NaN'])]
    
    if len(recent) == 0:
        return {"error": "No completed races"}
    
    # Add target column if not exists
    if 'target' not in recent.columns:
        recent = recent.copy()
        recent['target'] = (recent['rank'].astype(str) == '1').astype(int)
    
    # Simple simulation: bet on boat_no=1 for each race
    total_bet = 0
    total_return = 0
    wins = 0
    losses = 0
    
    daily_pnl = defaultdict(lambda: {"bet": 0, "return": 0, "pnl": 0})
    
    boat1_data = recent[recent['boat_no'] == 1]
    for _, row in boat1_data.iterrows():
        date_str = row['date'].strftime('%Y-%m-%d')
        total_bet += bet_amount
        daily_pnl[date_str]["bet"] += bet_amount
        
        # Use actual tansho odds if available, else default 2.5x
        if row['target'] == 1:
            odds = row.get('tansho', 0)
            if odds and odds > 0:
                win_amount = bet_amount * (odds / 100)  # tansho is in yen per 100 yen
            else:
                win_amount = bet_amount * 2.5  # default
            total_return += win_amount
            daily_pnl[date_str]["return"] += win_amount
            wins += 1
        else:
            losses += 1
        
        daily_pnl[date_str]["pnl"] = daily_pnl[date_str]["return"] - daily_pnl[date_str]["bet"]
    
    roi = ((total_return - total_bet) / total_bet * 100) if total_bet > 0 else 0
    
    result = {
        "period_days": days,
        "bet_amount": bet_amount,
        "total_races": wins + losses,
        "wins": wins,
        "losses": losses,
        "win_rate": round(wins / (wins + losses) * 100, 1) if (wins + losses) > 0 else 0,
        "total_bet": total_bet,
        "total_return": round(total_return, 0),
        "net_profit": round(total_return - total_bet, 0),
        "roi": round(roi, 1),
        "daily_pnl": [
            {"date": k, **v} 
            for k, v in sorted(daily_pnl.items())
        ]
    }
    
    cache.set(cache_key, result, ttl=1800)
    return result


@router.get("/venue-stats")
async def get_venue_stats(
    cache: RedisCache = Depends(get_cache)
):
    """Get accuracy by venue"""
    cache_key = "analytics:venue_stats"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    if not os.path.exists(DATA_PATH):
        return {"error": "No data available"}
    
    df = pd.read_csv(DATA_PATH)
    
    # Add target column if not exists
    if 'target' not in df.columns:
        df = df.copy()
        df['target'] = (df['rank'].astype(str) == '1').astype(int)
    
    venue_stats = []
    for jyo, group in df.groupby('jyo_cd'):
        boat1 = group[group['boat_no'] == 1]
        hit_rate = boat1['target'].mean() * 100 if len(boat1) > 0 else 0
        venue_stats.append({
            "venue_code": int(jyo),
            "total_races": len(group) // 6,
            "hit_rate": round(hit_rate, 1)
        })
    
    result = {
        "venue_stats": sorted(venue_stats, key=lambda x: -x['hit_rate'])
    }
    
    cache.set(cache_key, result, ttl=3600)
    return result


@router.get("/leaderboard")
async def get_racer_leaderboard(
    limit: int = Query(20, ge=5, le=100),
    cache: RedisCache = Depends(get_cache)
):
    """Get top performing racers"""
    cache_key = f"analytics:leaderboard:{limit}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    if not os.path.exists(DATA_PATH):
        return {"error": "No data available"}
    
    df = pd.read_csv(DATA_PATH)
    
    # Add target column if not exists
    if 'target' not in df.columns:
        df = df.copy()
        df['target'] = (df['rank'].astype(str) == '1').astype(int)
    
    # Group by racer_id
    racer_stats = df.groupby('racer_id').agg({
        'target': ['mean', 'count'],
        'racer_win_rate': 'first',
        'exhibition_time': 'mean',
        'racer_name': 'first'
    }).reset_index()
    
    racer_stats.columns = ['racer_id', 'actual_hit_rate', 'races', 'win_rate', 'avg_exhibition', 'name']
    racer_stats = racer_stats[racer_stats['races'] >= 10]  # Min 10 races
    racer_stats = racer_stats.sort_values('actual_hit_rate', ascending=False).head(limit)
    
    result = {
        "leaderboard": [
            {
                "rank": idx + 1,
                "racer_id": int(row['racer_id']) if pd.notna(row['racer_id']) else 0,
                "name": str(row['name']) if pd.notna(row['name']) else "",
                "win_rate": round(row['win_rate'], 2) if pd.notna(row['win_rate']) else 0,
                "actual_hit_rate": round(row['actual_hit_rate'] * 100, 1),
                "races": int(row['races']),
                "avg_exhibition": round(row['avg_exhibition'], 2) if pd.notna(row['avg_exhibition']) else 0
            }
            for idx, (_, row) in enumerate(racer_stats.iterrows())
        ]
    }
    
    cache.set(cache_key, result, ttl=3600)
    return result


@router.get("/backtest/high-prob")
async def backtest_high_probability_strategy(
    threshold: float = Query(0.7, ge=0.5, le=0.9),
    days: int = Query(7, ge=1, le=30)
):
    """
    Backtest high probability strategy
    Shows ROI for betting only on races above probability threshold
    """
    import os
    import pandas as pd
    from datetime import datetime, timedelta
    from src.features.preprocessing import preprocess, FEATURES
    from src.model.predictor import Predictor
    
    DATA_PATH = "data/processed/race_data.csv"
    if not os.path.exists(DATA_PATH):
        return {"error": "No data available"}
    
    df = pd.read_csv(DATA_PATH)
    df = preprocess(df, is_training=True)
    
    # Filter to recent days
    unique_dates = sorted(df['date'].unique())
    test_dates = unique_dates[-days:] if len(unique_dates) >= days else unique_dates
    test_df = df[df['date'].isin(test_dates)].copy()
    
    if len(test_df) == 0:
        return {"error": "No test data available"}
    
    # Predict
    predictor = Predictor()
    X = test_df[FEATURES]
    test_df['pred'] = predictor.predict(X)
    
    # Aggregate by race
    results = []
    for (date, jyo, race), group in test_df.groupby(['date', 'jyo_cd', 'race_no']):
        top = group.sort_values('pred', ascending=False).iloc[0]
        winner = group[group['target'] == 1]
        actual_tansho = winner['tansho'].iloc[0] if len(winner) > 0 else 0
        
        results.append({
            'date': int(date),
            'jyo': str(jyo),
            'race': int(race),
            'top_prob': float(top['pred']),
            'top_boat': int(top['boat_no']),
            'hit': 1 if top['target'] == 1 else 0,
            'tansho': float(actual_tansho) if top['target'] == 1 else 0
        })
    
    results_df = pd.DataFrame(results)
    
    # Filter by threshold
    filtered = results_df[results_df['top_prob'] >= threshold]
    
    if len(filtered) == 0:
        return {
            "threshold": threshold,
            "days": days,
            "total_races": 0,
            "message": "No races above threshold"
        }
    
    hits = int(filtered['hit'].sum())
    total = len(filtered)
    hit_rate = hits / total * 100
    
    total_bet = total * 100
    total_return = filtered['tansho'].sum() * 10
    roi = (total_return - total_bet) / total_bet * 100 if total_bet > 0 else 0
    profit = total_return - total_bet
    
    # Daily breakdown
    daily_stats = []
    for date in sorted(filtered['date'].unique()):
        day_df = filtered[filtered['date'] == date]
        day_hits = int(day_df['hit'].sum())
        day_total = len(day_df)
        day_return = day_df['tansho'].sum() * 10
        day_bet = day_total * 100
        
        daily_stats.append({
            "date": str(date),
            "races": day_total,
            "hits": day_hits,
            "hit_rate": round(day_hits / day_total * 100, 1) if day_total > 0 else 0,
            "bet": int(day_bet),
            "return": int(day_return),
            "profit": int(day_return - day_bet)
        })
    
    return {
        "threshold": threshold,
        "days": days,
        "period": f"{min(filtered['date'])} - {max(filtered['date'])}",
        "total_races": total,
        "hits": hits,
        "hit_rate": round(hit_rate, 1),
        "total_bet": int(total_bet),
        "total_return": int(total_return),
        "profit": int(profit),
        "roi": round(roi, 1),
        "daily_stats": daily_stats
    }
