"""Optimized Backtest Router with Caching and Parallel Processing"""
from fastapi import APIRouter, Query, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import hashlib
import json
import os
import asyncio
from functools import lru_cache

router = APIRouter(prefix="/api/backtest/v2", tags=["backtest-optimized"])

# In-memory cache for backtest results
_backtest_cache = {}
CACHE_TTL = 3600  # 1 hour

VENUE_NAMES = {
    "01": "桐生", "02": "戸田", "03": "江戸川", "04": "平和島", "05": "多摩川",
    "06": "浜名湖", "07": "蒲郡", "08": "常滑", "09": "津", "10": "三国",
    "11": "びわこ", "12": "住之江", "13": "尼崎", "14": "鳴門", "15": "丸亀",
    "16": "児島", "17": "宮島", "18": "徳山", "19": "下関", "20": "若松",
    "21": "芦屋", "22": "福岡", "23": "唐津", "24": "大村"
}

# Average odds by bet type (estimated)
AVG_ODDS = {
    'win': {1: 2.5, 2: 6.0, 3: 7.0, 4: 8.0, 5: 12.0, 6: 15.0},
    'exacta': 15.0,
    'trifecta': 80.0,
    'wide': 5.0,
    'place': 1.5
}


def safe_float(val, default=0.0):
    """Convert to float, handling NaN/inf"""
    if pd.isna(val) or val != val or val == float('inf') or val == float('-inf'):
        return default
    return float(val)


def get_cache_key(strategy: str, start_date: str, end_date: str, min_confidence: str, bet_amount: int) -> str:
    """Generate cache key for backtest parameters"""
    params = f"{strategy}_{start_date}_{end_date}_{min_confidence}_{bet_amount}"
    return hashlib.md5(params.encode()).hexdigest()


def get_cached_result(cache_key: str) -> Optional[Dict]:
    """Get cached backtest result if not expired"""
    if cache_key in _backtest_cache:
        result, timestamp = _backtest_cache[cache_key]
        if datetime.now().timestamp() - timestamp < CACHE_TTL:
            return result
        else:
            del _backtest_cache[cache_key]
    return None


def set_cached_result(cache_key: str, result: Dict):
    """Cache backtest result"""
    _backtest_cache[cache_key] = (result, datetime.now().timestamp())


@lru_cache(maxsize=1)
def get_preprocessed_data():
    """Get preprocessed data with caching"""
    from src.api.dependencies import get_predictor, get_dataframe
    from src.features.preprocessing import preprocess, FEATURES
    
    model = get_predictor()
    df = get_dataframe()
    
    if df.empty or model is None:
        return None, None
    
    df['rank_num'] = pd.to_numeric(df['rank'], errors='coerce')
    df = df.dropna(subset=['rank_num'])
    
    processed = preprocess(df)
    
    # Add predictions
    available_features = [f for f in FEATURES if f in processed.columns]
    X = processed[available_features].fillna(0)
    processed['pred_prob'] = model.predict(X)
    
    return processed, df


def backtest_race_batch(races_data: List[tuple], strategy: str, bet_amount: int) -> List[Dict]:
    """Backtest a batch of races in parallel"""
    results = []
    
    for race_key, group in races_data:
        date, jyo, race_no = race_key
        result = backtest_single_race(group, strategy, bet_amount)
        if result:
            result['date'] = str(date)
            result['venue'] = str(jyo).zfill(2)
            result['race_no'] = race_no
            results.append(result)
    
    return results


def backtest_single_race(group: pd.DataFrame, strategy: str, bet_amount: int) -> Optional[Dict]:
    """Backtest a single race"""
    if len(group) < 2:
        return None
    
    sorted_group = group.sort_values('pred_prob', ascending=False)
    top_prob = sorted_group.iloc[0]['pred_prob']
    
    # Determine confidence
    if strategy == 'win':
        thresholds = {'S': 0.5, 'A': 0.4, 'B': 0.3}
    elif strategy == 'exacta':
        thresholds = {'S': 0.15, 'A': 0.10, 'B': 0.05}
    elif strategy == 'trifecta':
        thresholds = {'S': 0.05, 'A': 0.03, 'B': 0.02}
    else:
        thresholds = {'S': 0.4, 'A': 0.3, 'B': 0.2}
    
    prob = top_prob
    if strategy == 'exacta':
        prob = top_prob * sorted_group.iloc[1]['pred_prob'] * 2
    elif strategy == 'trifecta':
        prob = top_prob * sorted_group.iloc[1]['pred_prob'] * sorted_group.iloc[2]['pred_prob'] * 6
    
    if prob >= thresholds['S']:
        conf = 'S'
    elif prob >= thresholds['A']:
        conf = 'A'
    elif prob >= thresholds['B']:
        conf = 'B'
    else:
        conf = 'C'
    
    # Check actual result
    actual_ranks = group.set_index('boat_no')['rank_num'].to_dict()
    
    hit = False
    odds = 5.0
    
    if strategy == 'win':
        pred_boat = int(sorted_group.iloc[0]['boat_no'])
        actual_1st = [b for b, r in actual_ranks.items() if r == 1]
        if actual_1st:
            hit = pred_boat == actual_1st[0]
            odds = AVG_ODDS['win'].get(pred_boat, 5.0)
    
    elif strategy == 'exacta':
        pred_1st = int(sorted_group.iloc[0]['boat_no'])
        pred_2nd = int(sorted_group.iloc[1]['boat_no'])
        actual_1st = [b for b, r in actual_ranks.items() if r == 1]
        actual_2nd = [b for b, r in actual_ranks.items() if r == 2]
        if actual_1st and actual_2nd:
            hit = (pred_1st == actual_1st[0] and pred_2nd == actual_2nd[0])
            odds = AVG_ODDS['exacta']
    
    elif strategy == 'trifecta':
        pred_1st = int(sorted_group.iloc[0]['boat_no'])
        pred_2nd = int(sorted_group.iloc[1]['boat_no'])
        pred_3rd = int(sorted_group.iloc[2]['boat_no'])
        actual_1st = [b for b, r in actual_ranks.items() if r == 1]
        actual_2nd = [b for b, r in actual_ranks.items() if r == 2]
        actual_3rd = [b for b, r in actual_ranks.items() if r == 3]
        if actual_1st and actual_2nd and actual_3rd:
            hit = (pred_1st == actual_1st[0] and pred_2nd == actual_2nd[0] and pred_3rd == actual_3rd[0])
            odds = AVG_ODDS['trifecta']
    
    elif strategy == 'wide':
        pred_boats = [int(sorted_group.iloc[0]['boat_no']), int(sorted_group.iloc[1]['boat_no'])]
        top3_boats = [b for b, r in actual_ranks.items() if r <= 3]
        hit = all(b in top3_boats for b in pred_boats)
        odds = AVG_ODDS['wide']
    
    elif strategy == 'place':
        pred_boat = int(sorted_group.iloc[0]['boat_no'])
        top3_boats = [b for b, r in actual_ranks.items() if r <= 3]
        hit = pred_boat in top3_boats
        odds = AVG_ODDS['place']
    
    return {
        'hit': hit,
        'return': safe_float(odds * bet_amount if hit else 0),
        'confidence': conf
    }


class FastBacktestResult(BaseModel):
    strategy: str
    period: Dict[str, Any]
    summary: Dict[str, Any]
    by_confidence: Dict[str, Dict[str, Any]]
    by_venue: Optional[Dict[str, Dict[str, Any]]] = None
    daily: Optional[List[Dict[str, Any]]] = None
    cached: bool = False
    execution_time_ms: float


@router.get("/fast/{strategy}")
async def fast_backtest(
    strategy: str,
    start_date: str = Query(None),
    end_date: str = Query(None),
    min_confidence: str = Query("C"),
    bet_amount: int = Query(100),
    include_daily: bool = Query(False),
    include_venue: bool = Query(True)
) -> FastBacktestResult:
    """Fast backtest with caching and optimization"""
    import time
    start_time = time.time()
    
    # Check cache
    cache_key = get_cache_key(strategy, start_date or "", end_date or "", min_confidence, bet_amount)
    cached = get_cached_result(cache_key)
    if cached:
        cached['cached'] = True
        cached['execution_time_ms'] = (time.time() - start_time) * 1000
        return FastBacktestResult(**cached)
    
    # Get data
    processed, _ = get_preprocessed_data()
    if processed is None:
        return FastBacktestResult(
            strategy=strategy,
            period={},
            summary={"error": "No data"},
            by_confidence={},
            cached=False,
            execution_time_ms=(time.time() - start_time) * 1000
        )
    
    # Filter by date
    if start_date:
        processed = processed[processed['date'].astype(str) >= start_date]
    if end_date:
        processed = processed[processed['date'].astype(str) <= end_date]
    
    if len(processed) == 0:
        return FastBacktestResult(
            strategy=strategy,
            period={},
            summary={"error": "No data in range"},
            by_confidence={},
            cached=False,
            execution_time_ms=(time.time() - start_time) * 1000
        )
    
    # Group races
    grouped = list(processed.groupby(['date', 'jyo_cd', 'race_no']))
    
    # Parallel processing for large datasets
    if len(grouped) > 100:
        batch_size = max(50, len(grouped) // 4)
        batches = [grouped[i:i+batch_size] for i in range(0, len(grouped), batch_size)]
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(backtest_race_batch, batch, strategy, bet_amount) for batch in batches]
            all_results = []
            for future in futures:
                all_results.extend(future.result())
    else:
        all_results = backtest_race_batch(grouped, strategy, bet_amount)
    
    # Filter by confidence
    conf_order = {'S': 4, 'A': 3, 'B': 2, 'C': 1}
    min_conf_val = conf_order.get(min_confidence, 1)
    filtered_results = [r for r in all_results if conf_order.get(r['confidence'], 1) >= min_conf_val]
    
    # Aggregate results
    total_bets = len(filtered_results)
    total_wins = sum(1 for r in filtered_results if r['hit'])
    total_return = sum(r['return'] for r in filtered_results)
    total_invested = total_bets * bet_amount
    
    hit_rate = total_wins / total_bets * 100 if total_bets > 0 else 0
    roi = (total_return - total_invested) / total_invested * 100 if total_invested > 0 else 0
    
    # By confidence
    by_conf = {}
    for conf in ['S', 'A', 'B', 'C']:
        conf_results = [r for r in filtered_results if r['confidence'] == conf]
        if conf_results:
            c_bets = len(conf_results)
            c_wins = sum(1 for r in conf_results if r['hit'])
            c_return = sum(r['return'] for r in conf_results)
            c_invested = c_bets * bet_amount
            by_conf[conf] = {
                'bets': c_bets,
                'wins': c_wins,
                'hit_rate': round(c_wins / c_bets * 100, 1) if c_bets > 0 else 0,
                'roi': round((c_return - c_invested) / c_invested * 100, 1) if c_invested > 0 else 0
            }
    
    # By venue
    by_venue = None
    if include_venue:
        by_venue = {}
        venue_results = defaultdict(list)
        for r in filtered_results:
            venue_results[r['venue']].append(r)
        
        for venue, vr in venue_results.items():
            v_bets = len(vr)
            v_wins = sum(1 for r in vr if r['hit'])
            v_return = sum(r['return'] for r in vr)
            v_invested = v_bets * bet_amount
            by_venue[VENUE_NAMES.get(venue, venue)] = {
                'bets': v_bets,
                'wins': v_wins,
                'hit_rate': round(v_wins / v_bets * 100, 1) if v_bets > 0 else 0,
                'roi': round((v_return - v_invested) / v_invested * 100, 1) if v_invested > 0 else 0
            }
    
    # Daily results
    daily = None
    if include_daily:
        daily_results = defaultdict(list)
        for r in filtered_results:
            daily_results[r['date']].append(r)
        
        daily = []
        for date in sorted(daily_results.keys()):
            dr = daily_results[date]
            d_bets = len(dr)
            d_wins = sum(1 for r in dr if r['hit'])
            d_return = sum(r['return'] for r in dr)
            d_invested = d_bets * bet_amount
            daily.append({
                'date': date,
                'bets': d_bets,
                'wins': d_wins,
                'hit_rate': round(d_wins / d_bets * 100, 1) if d_bets > 0 else 0,
                'roi': round((d_return - d_invested) / d_invested * 100, 1) if d_invested > 0 else 0
            })
    
    dates = sorted(processed['date'].unique())
    result = {
        'strategy': strategy,
        'period': {
            'start': str(dates[0]) if dates else "",
            'end': str(dates[-1]) if dates else "",
            'days': len(dates)
        },
        'summary': {
            'total_bets': total_bets,
            'total_wins': total_wins,
            'hit_rate': round(hit_rate, 1),
            'total_invested': total_invested,
            'total_return': round(total_return, 0),
            'profit': round(total_return - total_invested, 0),
            'roi': round(roi, 1)
        },
        'by_confidence': by_conf,
        'by_venue': by_venue,
        'daily': daily,
        'cached': False,
        'execution_time_ms': (time.time() - start_time) * 1000
    }
    
    # Cache result
    set_cached_result(cache_key, result)
    
    return FastBacktestResult(**result)


@router.get("/compare-all")
async def compare_all_strategies(
    start_date: str = Query(None),
    end_date: str = Query(None),
    min_confidence: str = Query("C"),
    bet_amount: int = Query(100)
):
    """Compare all strategies with parallel execution"""
    import time
    start_time = time.time()
    
    strategies = ['win', 'exacta', 'trifecta', 'wide', 'place']
    
    # Run all backtests concurrently
    results = {}
    for strategy in strategies:
        result = await fast_backtest(
            strategy=strategy,
            start_date=start_date,
            end_date=end_date,
            min_confidence=min_confidence,
            bet_amount=bet_amount,
            include_daily=False,
            include_venue=False
        )
        results[strategy] = result.dict()
    
    # Find best strategy
    best_strategy = max(results.items(), key=lambda x: x[1]['summary'].get('roi', -999))[0]
    
    # Overall summary
    total_bets = sum(r['summary'].get('total_bets', 0) for r in results.values())
    total_return = sum(r['summary'].get('total_return', 0) for r in results.values())
    total_invested = sum(r['summary'].get('total_invested', 0) for r in results.values())
    
    return {
        'timestamp': datetime.now().isoformat(),
        'execution_time_ms': (time.time() - start_time) * 1000,
        'strategies': results,
        'best_strategy': best_strategy,
        'overall': {
            'total_strategies': len(strategies),
            'total_bets': total_bets,
            'total_return': round(total_return, 0),
            'combined_roi': round((total_return - total_invested) / total_invested * 100, 1) if total_invested > 0 else 0
        }
    }


@router.delete("/cache")
async def clear_cache():
    """Clear backtest cache"""
    global _backtest_cache
    count = len(_backtest_cache)
    _backtest_cache = {}
    get_preprocessed_data.cache_clear()
    return {"cleared": count, "status": "ok"}
