"""Enhanced Backtest Router - Comprehensive backtesting functionality"""
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from collections import defaultdict

router = APIRouter(prefix="/api/backtest", tags=["backtest"])

def safe_float(val, default=0.0):
    """Convert to float, handling NaN/inf"""
    if pd.isna(val) or val != val or val == float('inf') or val == float('-inf'):
        return default
    return float(val)

VENUE_NAMES = {
    "01": "桐生", "02": "戸田", "03": "江戸川", "04": "平和島", "05": "多摩川",
    "06": "浜名湖", "07": "蒲郡", "08": "常滑", "09": "津", "10": "三国",
    "11": "びわこ", "12": "住之江", "13": "尼崎", "14": "鳴門", "15": "丸亀",
    "16": "児島", "17": "宮島", "18": "徳山", "19": "下関", "20": "若松",
    "21": "芦屋", "22": "福岡", "23": "唐津", "24": "大村"
}


class BacktestResult(BaseModel):
    strategy: str
    params: Dict[str, Any]
    period: Dict[str, Any]  # Changed from Dict[str, str] to allow int values
    summary: Dict[str, Any]
    daily_results: Optional[List[Dict[str, Any]]] = None
    venue_results: Optional[Dict[str, Any]] = None
    confidence_breakdown: Optional[Dict[str, Any]] = None


class MultiStrategyBacktest(BaseModel):
    timestamp: str
    strategies: List[BacktestResult]
    best_strategy: str
    overall_summary: Dict[str, Any]


def get_base_data():
    """Get preprocessed data with predictions"""
    from src.api.dependencies import get_predictor, get_dataframe
    from src.features.preprocessing import preprocess, FEATURES
    
    model = get_predictor()
    df = get_dataframe()
    
    if df.empty or model is None:
        return None, None
    
    df['rank_num'] = pd.to_numeric(df['rank'], errors='coerce')
    df = df.dropna(subset=['rank_num'])
    
    processed = preprocess(df, is_training=False)
    available_features = [f for f in FEATURES if f in processed.columns]
    X = processed[available_features]
    probs = model.predict(X)
    processed['pred_prob'] = probs
    processed['rank_num'] = df['rank_num'].values
    
    return processed, df


@router.get("/comprehensive", response_model=BacktestResult)
async def comprehensive_backtest(
    strategy: str = Query("win", description="Strategy: win, exacta, trifecta, wide, place"),
    start_date: str = Query(None, description="Start date YYYYMMDD"),
    end_date: str = Query(None, description="End date YYYYMMDD"),
    min_confidence: str = Query("C", description="Minimum confidence: S, A, B, C"),
    bet_amount: int = Query(100, description="Bet amount per race")
):
    """Comprehensive backtest with detailed breakdown"""
    processed, df = get_base_data()
    
    if processed is None:
        return BacktestResult(
            strategy=strategy,
            params={},
            period={},
            summary={"error": "No data available"}
        )
    
    # Filter by date range
    if start_date:
        processed = processed[processed['date'].astype(str) >= start_date]
    if end_date:
        processed = processed[processed['date'].astype(str) <= end_date]
    
    dates = sorted(processed['date'].unique())
    
    # Initialize tracking
    daily_results = defaultdict(lambda: {"bets": 0, "wins": 0, "return": 0})
    venue_results = defaultdict(lambda: {"bets": 0, "wins": 0, "return": 0})
    confidence_results = {"S": {"bets": 0, "wins": 0, "return": 0},
                          "A": {"bets": 0, "wins": 0, "return": 0},
                          "B": {"bets": 0, "wins": 0, "return": 0},
                          "C": {"bets": 0, "wins": 0, "return": 0}}
    
    total_bets = 0
    total_wins = 0
    total_return = 0
    
    confidence_order = {"S": 4, "A": 3, "B": 2, "C": 1}
    min_conf_val = confidence_order.get(min_confidence, 1)
    
    for (date, jyo, race), group in processed.groupby(['date', 'jyo_cd', 'race_no']):
        if strategy == "win":
            result = _backtest_win(group, bet_amount)
        elif strategy == "exacta":
            result = _backtest_exacta(group, bet_amount)
        elif strategy == "trifecta":
            result = _backtest_trifecta(group, bet_amount)
        elif strategy == "wide":
            result = _backtest_wide(group, bet_amount)
        elif strategy == "place":
            result = _backtest_place(group, bet_amount)
        else:
            result = _backtest_win(group, bet_amount)
        
        if not result:
            continue
        
        conf = result.get("confidence", "C")
        conf_val = confidence_order.get(conf, 1)
        
        if conf_val < min_conf_val:
            continue
        
        total_bets += 1
        total_return += safe_float(result["return"])
        if result["hit"]:
            total_wins += 1
        
        # Track by date
        date_str = str(date)
        daily_results[date_str]["bets"] += 1
        daily_results[date_str]["return"] += safe_float(result["return"])
        if result["hit"]:
            daily_results[date_str]["wins"] += 1
        
        # Track by venue
        jyo_str = str(jyo).zfill(2)
        venue_name = VENUE_NAMES.get(jyo_str, jyo_str)
        venue_results[venue_name]["bets"] += 1
        venue_results[venue_name]["return"] += safe_float(result["return"])
        if result["hit"]:
            venue_results[venue_name]["wins"] += 1
        
        # Track by confidence
        confidence_results[conf]["bets"] += 1
        confidence_results[conf]["return"] += safe_float(result["return"])
        if result["hit"]:
            confidence_results[conf]["wins"] += 1
    
    # Calculate summary
    total_invested = total_bets * bet_amount
    hit_rate = total_wins / total_bets * 100 if total_bets > 0 else 0
    roi = (total_return - total_invested) / total_invested * 100 if total_invested > 0 else 0
    
    # Calculate daily ROI
    daily_list = []
    for d in sorted(daily_results.keys()):
        dr = daily_results[d]
        invested = dr["bets"] * bet_amount
        d_roi = (dr["return"] - invested) / invested * 100 if invested > 0 else 0
        daily_list.append({
            "date": d,
            "bets": dr["bets"],
            "wins": dr["wins"],
            "hit_rate": round(dr["wins"] / dr["bets"] * 100 if dr["bets"] > 0 else 0, 1),
            "return": round(dr["return"], 0),
            "roi": round(d_roi, 1)
        })
    
    # Calculate venue stats
    venue_stats = {}
    for v, vr in venue_results.items():
        invested = vr["bets"] * bet_amount
        v_roi = (vr["return"] - invested) / invested * 100 if invested > 0 else 0
        venue_stats[v] = {
            "bets": vr["bets"],
            "wins": vr["wins"],
            "hit_rate": round(vr["wins"] / vr["bets"] * 100 if vr["bets"] > 0 else 0, 1),
            "roi": round(v_roi, 1)
        }
    
    # Calculate confidence breakdown
    conf_breakdown = {}
    for c, cr in confidence_results.items():
        invested = cr["bets"] * bet_amount
        c_roi = (cr["return"] - invested) / invested * 100 if invested > 0 else 0
        conf_breakdown[c] = {
            "bets": cr["bets"],
            "wins": cr["wins"],
            "hit_rate": round(cr["wins"] / cr["bets"] * 100 if cr["bets"] > 0 else 0, 1),
            "roi": round(c_roi, 1)
        }
    
    return BacktestResult(
        strategy=strategy,
        params={
            "min_confidence": min_confidence,
            "bet_amount": bet_amount
        },
        period={
            "start": str(dates[0]) if dates else "",
            "end": str(dates[-1]) if dates else "",
            "days": len(dates)
        },
        summary={
            "total_bets": total_bets,
            "total_wins": total_wins,
            "hit_rate": round(hit_rate, 2),
            "total_invested": total_invested,
            "total_return": round(total_return, 0),
            "profit": round(total_return - total_invested, 0),
            "roi": round(roi, 1)
        },
        daily_results=daily_list,
        venue_results=venue_stats,
        confidence_breakdown=conf_breakdown
    )


@router.get("/compare", response_model=MultiStrategyBacktest)
async def compare_strategies(
    start_date: str = Query(None),
    end_date: str = Query(None),
    bet_amount: int = Query(100)
):
    """Compare all betting strategies"""
    strategies = ["win", "exacta", "trifecta", "wide", "place"]
    results = []
    
    for strat in strategies:
        result = await comprehensive_backtest(
            strategy=strat,
            start_date=start_date,
            end_date=end_date,
            min_confidence="C",
            bet_amount=bet_amount
        )
        results.append(result)
    
    # Find best strategy by ROI
    best = max(results, key=lambda x: x.summary.get("roi", -100))
    
    # Overall summary
    total_bets = sum(r.summary.get("total_bets", 0) for r in results)
    total_return = sum(r.summary.get("total_return", 0) for r in results)
    total_invested = sum(r.summary.get("total_invested", 0) for r in results)
    
    return MultiStrategyBacktest(
        timestamp=datetime.now().isoformat(),
        strategies=results,
        best_strategy=best.strategy,
        overall_summary={
            "total_strategies": len(strategies),
            "total_bets_all": total_bets,
            "total_return_all": round(total_return, 0),
            "combined_roi": round((total_return - total_invested) / total_invested * 100 if total_invested > 0 else 0, 1)
        }
    )


@router.get("/optimal-params")
async def find_optimal_params(
    strategy: str = Query("win"),
    start_date: str = Query(None),
    end_date: str = Query(None)
):
    """Find optimal parameters for a strategy"""
    processed, df = get_base_data()
    
    if processed is None:
        return {"error": "No data available"}
    
    if start_date:
        processed = processed[processed['date'].astype(str) >= start_date]
    if end_date:
        processed = processed[processed['date'].astype(str) <= end_date]
    
    # Grid search over confidence levels
    results = []
    
    for min_conf in ["S", "A", "B", "C"]:
        res = await comprehensive_backtest(
            strategy=strategy,
            start_date=start_date,
            end_date=end_date,
            min_confidence=min_conf,
            bet_amount=100
        )
        results.append({
            "min_confidence": min_conf,
            "bets": res.summary.get("total_bets", 0),
            "hit_rate": res.summary.get("hit_rate", 0),
            "roi": res.summary.get("roi", -100)
        })
    
    # Find optimal by ROI (with minimum bets threshold)
    valid_results = [r for r in results if r["bets"] >= 10]
    if valid_results:
        optimal = max(valid_results, key=lambda x: x["roi"])
    else:
        optimal = results[0] if results else None
    
    return {
        "strategy": strategy,
        "all_results": results,
        "optimal": optimal
    }


def _backtest_win(group: pd.DataFrame, bet_amount: int) -> Optional[Dict]:
    """Backtest single win prediction"""
    if len(group) < 2:
        return None
    
    sorted_group = group.sort_values('pred_prob', ascending=False)
    top = sorted_group.iloc[0]
    
    top_prob = top['pred_prob']
    if top_prob >= 0.5:
        conf = "S"
    elif top_prob >= 0.4:
        conf = "A"
    elif top_prob >= 0.3:
        conf = "B"
    else:
        conf = "C"
    
    actual_winner = group[group['rank_num'] == 1]
    if len(actual_winner) == 0:
        return None
    
    hit = int(top['boat_no']) == int(actual_winner.iloc[0]['boat_no'])
    
    # Estimate odds based on course
    COURSE_AVG_ODDS = {1: 2.5, 2: 6.0, 3: 7.0, 4: 8.0, 5: 12.0, 6: 15.0}
    odds = COURSE_AVG_ODDS.get(int(top['boat_no']), 5.0)
    
    return {
        "hit": hit,
        "return": odds * bet_amount if hit else 0,
        "confidence": conf
    }


def _backtest_exacta(group: pd.DataFrame, bet_amount: int) -> Optional[Dict]:
    """Backtest 2連単"""
    if len(group) < 2:
        return None
    
    sorted_group = group.sort_values('pred_prob', ascending=False)
    first = int(sorted_group.iloc[0]['boat_no'])
    second = int(sorted_group.iloc[1]['boat_no'])
    
    p1 = sorted_group.iloc[0]['pred_prob']
    p2 = sorted_group.iloc[1]['pred_prob']
    prob = p1 * p2 * 2
    
    if prob >= 0.15:
        conf = "S"
    elif prob >= 0.10:
        conf = "A"
    elif prob >= 0.05:
        conf = "B"
    else:
        conf = "C"
    
    actual_1st = group[group['rank_num'] == 1]
    actual_2nd = group[group['rank_num'] == 2]
    
    if len(actual_1st) == 0 or len(actual_2nd) == 0:
        return None
    
    hit = (first == int(actual_1st.iloc[0]['boat_no']) and 
           second == int(actual_2nd.iloc[0]['boat_no']))
    
    EXACTA_AVG_ODDS = {
        (1, 2): 4.5, (1, 3): 6.0, (1, 4): 8.0,
        (2, 1): 8.0, (2, 3): 15.0, (3, 1): 10.0
    }
    odds = EXACTA_AVG_ODDS.get((first, second), 15.0)
    
    return {
        "hit": hit,
        "return": odds * bet_amount if hit else 0,
        "confidence": conf
    }


def _backtest_trifecta(group: pd.DataFrame, bet_amount: int) -> Optional[Dict]:
    """Backtest 3連単"""
    if len(group) < 3:
        return None
    
    sorted_group = group.sort_values('pred_prob', ascending=False)
    first = int(sorted_group.iloc[0]['boat_no'])
    second = int(sorted_group.iloc[1]['boat_no'])
    third = int(sorted_group.iloc[2]['boat_no'])
    
    p1 = sorted_group.iloc[0]['pred_prob']
    p2 = sorted_group.iloc[1]['pred_prob']
    p3 = sorted_group.iloc[2]['pred_prob']
    prob = p1 * p2 * p3 * 6
    
    if prob >= 0.10:
        conf = "S"
    elif prob >= 0.05:
        conf = "A"
    elif prob >= 0.02:
        conf = "B"
    else:
        conf = "C"
    
    actual_1st = group[group['rank_num'] == 1]
    actual_2nd = group[group['rank_num'] == 2]
    actual_3rd = group[group['rank_num'] == 3]
    
    if len(actual_1st) == 0 or len(actual_2nd) == 0 or len(actual_3rd) == 0:
        return None
    
    hit = (first == int(actual_1st.iloc[0]['boat_no']) and 
           second == int(actual_2nd.iloc[0]['boat_no']) and
           third == int(actual_3rd.iloc[0]['boat_no']))
    
    TRIFECTA_BASE_ODDS = {1: 25.0, 2: 60.0, 3: 70.0, 4: 80.0, 5: 100.0, 6: 120.0}
    odds = TRIFECTA_BASE_ODDS.get(first, 50.0)
    
    return {
        "hit": hit,
        "return": odds * bet_amount if hit else 0,
        "confidence": conf
    }


def _backtest_wide(group: pd.DataFrame, bet_amount: int) -> Optional[Dict]:
    """Backtest ワイド"""
    if len(group) < 2:
        return None
    
    sorted_group = group.sort_values('pred_prob', ascending=False)
    boat1 = int(sorted_group.iloc[0]['boat_no'])
    boat2 = int(sorted_group.iloc[1]['boat_no'])
    
    p1 = sorted_group.iloc[0]['pred_prob']
    p2 = sorted_group.iloc[1]['pred_prob']
    prob = min(p1 * 2.5, 0.9) * min(p2 * 2.5, 0.9) * 0.85
    
    if prob >= 0.5:
        conf = "S"
    elif prob >= 0.4:
        conf = "A"
    elif prob >= 0.3:
        conf = "B"
    else:
        conf = "C"
    
    top3 = set(group[group['rank_num'] <= 3]['boat_no'].astype(int).tolist())
    
    if len(top3) < 3:
        return None
    
    hit = boat1 in top3 and boat2 in top3
    
    WIDE_AVG_ODDS = {(1, 2): 2.0, (1, 3): 2.5, (1, 4): 3.5, (2, 3): 5.0}
    key = (min(boat1, boat2), max(boat1, boat2))
    odds = WIDE_AVG_ODDS.get(key, 4.0)
    
    return {
        "hit": hit,
        "return": odds * bet_amount if hit else 0,
        "confidence": conf
    }


def _backtest_place(group: pd.DataFrame, bet_amount: int) -> Optional[Dict]:
    """Backtest 複勝"""
    if len(group) < 1:
        return None
    
    sorted_group = group.sort_values('pred_prob', ascending=False)
    top = sorted_group.iloc[0]
    boat = int(top['boat_no'])
    
    prob = min(top['pred_prob'] * 2.5, 0.95)
    
    if prob >= 0.75:
        conf = "S"
    elif prob >= 0.65:
        conf = "A"
    elif prob >= 0.55:
        conf = "B"
    else:
        conf = "C"
    
    top3 = set(group[group['rank_num'] <= 3]['boat_no'].astype(int).tolist())
    
    if len(top3) < 3:
        return None
    
    hit = boat in top3
    
    PLACE_AVG_ODDS = {1: 1.2, 2: 2.5, 3: 3.0, 4: 4.0, 5: 5.5, 6: 7.0}
    odds = PLACE_AVG_ODDS.get(boat, 3.0)
    
    return {
        "hit": hit,
        "return": odds * bet_amount if hit else 0,
        "confidence": conf
    }
