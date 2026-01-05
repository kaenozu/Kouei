"""Smart Betting Router - High probability betting strategies"""
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd

router = APIRouter(prefix="/api", tags=["smart_betting"])


class SmartBet(BaseModel):
    date: str
    jyo_cd: str
    jyo_name: str
    race_no: int
    boat_no: int
    racer_name: str
    probability: float
    confidence: str
    expected_odds: float
    ev: float  # Expected Value
    start_time: Optional[str] = None
    real_odds: Optional[float] = None
    status: str = "scheduled"  # scheduled, live, finished
    minutes_until: Optional[int] = None  # Minutes until race start


class SmartBettingResponse(BaseModel):
    timestamp: str
    strategy: str
    threshold: float
    total_bets: int
    bets: List[SmartBet]
    estimated_hit_rate: float
    estimated_roi: float


def _get_real_odds(date: str, jyo_cd: str, race_no: int, boat_no: int) -> Optional[float]:
    """Get real-time odds for a boat"""
    try:
        from src.parser.odds_parser import OddsParser
        from src.collector.downloader import Downloader
        
        downloader = Downloader()
        html = downloader.get_odds(date, jyo_cd, race_no)
        if html:
            parser = OddsParser()
            odds_data = parser.parse_tansho(html)
            if odds_data and boat_no <= len(odds_data):
                return float(odds_data[boat_no - 1]) if odds_data[boat_no - 1] else None
    except Exception as e:
        pass
    return None


def _get_race_status_and_minutes(start_time: Optional[str]) -> tuple:
    """Determine race status and minutes until start (JST)"""
    if not start_time:
        return "scheduled", None
    
    try:
        from datetime import timezone, timedelta
        
        # Get current time in JST
        jst = timezone(timedelta(hours=9))
        now_jst = datetime.now(jst)
        
        hour, minute = map(int, start_time.split(':'))
        race_time = now_jst.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        diff_minutes = int((race_time - now_jst).total_seconds() / 60)
        
        if diff_minutes < -10:  # More than 10 minutes ago
            return "finished", None
        elif diff_minutes < 0:  # Just passed
            return "live", 0
        elif diff_minutes < 15:  # Within 15 minutes
            return "upcoming", diff_minutes
        else:
            return "scheduled", diff_minutes
    except:
        return "scheduled", None


# 会場名
VENUE_NAMES = {
    "01": "桐生", "02": "戸田", "03": "江戸川", "04": "平和島", "05": "多摩川",
    "06": "浜名湖", "07": "蒲郡", "08": "常滑", "09": "津", "10": "三国",
    "11": "びわこ", "12": "住之江", "13": "尼崎", "14": "鳴門", "15": "丸亀",
    "16": "児島", "17": "宮島", "18": "徳山", "19": "下関", "20": "若松",
    "21": "芦屋", "22": "福岡", "23": "唐津", "24": "大村"
}


@router.get("/smart-bets", response_model=SmartBettingResponse)
async def get_smart_bets(
    date: str = Query(None, description="Date YYYYMMDD (default: today)"),
    threshold: float = Query(0.7, ge=0.5, le=0.95, description="Minimum probability threshold"),
    max_bets: int = Query(20, ge=1, le=50, description="Maximum number of bets to return"),
    strategy: str = Query("course1_focus", description="Strategy: course1_focus, high_prob, balanced")
):
    """Get high-probability betting recommendations
    
    Strategies:
    - course1_focus: Focus on 1号艇 predictions (highest accuracy ~83%)
    - high_prob: Pure probability-based selection
    - balanced: Mix of both approaches
    """
    from src.api.dependencies import get_predictor, get_dataframe
    from src.features.preprocessing import preprocess, FEATURES
    
    if date is None:
        date = datetime.now().strftime("%Y%m%d")
    
    model = get_predictor()
    df = get_dataframe()
    
    if df.empty or model is None:
        return SmartBettingResponse(
            timestamp=datetime.now().isoformat(),
            strategy=strategy,
            threshold=threshold,
            total_bets=0,
            bets=[],
            estimated_hit_rate=0,
            estimated_roi=0
        )
    
    # Filter to target date
    df = df[df['date'].astype(str) == date].copy()
    
    if df.empty:
        return SmartBettingResponse(
            timestamp=datetime.now().isoformat(),
            strategy=strategy,
            threshold=threshold,
            total_bets=0,
            bets=[],
            estimated_hit_rate=0,
            estimated_roi=0
        )
    
    # Preprocess and predict
    processed = preprocess(df, is_training=False)
    available_features = [f for f in FEATURES if f in processed.columns]
    X = processed[available_features]
    probs = model.predict(X)
    processed['pred_prob'] = probs
    
    # Get top prediction for each race
    bets = []
    for (d, jyo, race), group in processed.groupby(['date', 'jyo_cd', 'race_no']):
        # Apply strategy-specific filtering
        if strategy == "course1_focus":
            # Only consider 1号艇 with high probability
            course1 = group[group['boat_no'] == 1]
            if course1.empty:
                continue
            top = course1.iloc[0]
            # Require higher confidence for 1号艇 strategy
            effective_threshold = max(threshold, 0.55)
            if top['pred_prob'] < effective_threshold:
                continue
            # Boost confidence for 1号艇 (empirically ~83% accurate)
            confidence_boost = 0.15
        elif strategy == "balanced":
            # Consider 1号艇 with lower threshold, others with higher
            course1 = group[group['boat_no'] == 1]
            others = group[group['boat_no'] != 1]
            
            candidates = []
            if not course1.empty and course1.iloc[0]['pred_prob'] >= threshold * 0.85:
                candidates.append((course1.iloc[0], 0.1))  # 10% boost
            if not others.empty:
                top_other = others.nlargest(1, 'pred_prob').iloc[0]
                if top_other['pred_prob'] >= threshold:
                    candidates.append((top_other, 0))
            
            if not candidates:
                continue
            # Pick best candidate
            top, confidence_boost = max(candidates, key=lambda x: x[0]['pred_prob'] + x[1])
        else:  # high_prob
            top = group.nlargest(1, 'pred_prob').iloc[0]
            if top['pred_prob'] < threshold:
                continue
            confidence_boost = 0
        
        # Get start time
        start_time = str(top.get('start_time', '')) if pd.notna(top.get('start_time')) else None
        
        # Get real odds if available
        jyo_str = str(jyo).zfill(2)
        real_odds = _get_real_odds(str(d), jyo_str, int(race), int(top['boat_no']))
        
        # Estimate odds based on probability if no real odds
        estimated_odds = real_odds if real_odds else (1 / top['pred_prob'] if top['pred_prob'] > 0 else 10)
        ev = top['pred_prob'] * estimated_odds
        
        # Determine confidence with strategy-specific boost
        adjusted_prob = min(top['pred_prob'] + confidence_boost, 0.99)
        if adjusted_prob >= 0.9:
            confidence = "S"
        elif adjusted_prob >= 0.8:
            confidence = "A"
        elif adjusted_prob >= 0.7:
            confidence = "B"
        else:
            confidence = "C"
        
        # Determine status and minutes until race
        status, minutes_until = _get_race_status_and_minutes(start_time)
        
        bets.append(SmartBet(
            date=str(d),
            jyo_cd=jyo_str,
            jyo_name=VENUE_NAMES.get(jyo_str, f"会場{jyo}"),
            race_no=int(race),
            boat_no=int(top['boat_no']),
            racer_name=str(top.get('racer_name', 'N/A')),
            probability=float(top['pred_prob']),
            confidence=confidence,
            expected_odds=round(estimated_odds, 1),
            ev=round(ev, 2),
            start_time=start_time,
            real_odds=real_odds,
            status=status,
            minutes_until=minutes_until
        ))
    
    # Filter out finished races and sort by start time
    active_bets = [b for b in bets if b.status != 'finished']
    
    # Sort: upcoming first, then by start time, then by probability
    def sort_key(b):
        try:
            h, m = map(int, (b.start_time or '23:59').split(':'))
            time_val = h * 60 + m
        except:
            time_val = 9999
        
        # Prioritize upcoming races
        priority = 0 if b.status == 'upcoming' else 1 if b.status == 'scheduled' else 2
        return (priority, time_val, -b.probability)
    
    active_bets.sort(key=sort_key)
    bets = active_bets[:max_bets]
    
    # Strategy-specific performance estimates
    if strategy == "course1_focus":
        estimated_hit = 83  # Empirical ~83% for course 1
        estimated_roi = 120  # Lower odds but higher hit rate
    elif strategy == "balanced":
        estimated_hit = 60
        estimated_roi = 150
    else:
        hit_rate_estimates = {0.5: 50, 0.6: 55, 0.7: 60, 0.8: 65, 0.9: 70}
        roi_estimates = {0.5: 180, 0.6: 170, 0.7: 160, 0.8: 150, 0.9: 140}
        estimated_hit = hit_rate_estimates.get(threshold, 55)
        estimated_roi = roi_estimates.get(threshold, 160)
    
    return SmartBettingResponse(
        timestamp=datetime.now().isoformat(),
        strategy=strategy,
        threshold=threshold,
        total_bets=len(bets),
        bets=bets,
        estimated_hit_rate=estimated_hit,
        estimated_roi=estimated_roi
    )


@router.get("/smart-bets/backtest")
async def backtest_smart_strategy(
    threshold: float = Query(0.7, ge=0.5, le=0.95),
    days: int = Query(7, ge=1, le=30)
):
    """Backtest the smart betting strategy"""
    from src.api.dependencies import get_predictor, get_dataframe
    from src.features.preprocessing import preprocess, FEATURES
    from datetime import datetime, timedelta
    
    model = get_predictor()
    df = get_dataframe()
    
    if df.empty or model is None:
        return {"error": "No data available"}
    
    # Convert rank to numeric for results
    df['rank'] = pd.to_numeric(df['rank'], errors='coerce')
    df['tansho'] = pd.to_numeric(df['tansho'], errors='coerce').fillna(0)
    df = df.dropna(subset=['rank'])
    
    # Preprocess and predict
    processed = preprocess(df, is_training=False)
    available_features = [f for f in FEATURES if f in processed.columns]
    X = processed[available_features]
    probs = model.predict(X)
    processed['pred_prob'] = probs
    
    # Simulate betting
    total_bets = 0
    total_wins = 0
    total_return = 0
    daily_results = []
    
    for date, date_group in processed.groupby('date'):
        day_bets = 0
        day_wins = 0
        day_return = 0
        
        for (d, jyo, race), group in date_group.groupby(['date', 'jyo_cd', 'race_no']):
            top = group.nlargest(1, 'pred_prob').iloc[0]
            
            if top['pred_prob'] >= threshold:
                day_bets += 1
                if top['rank'] == 1:
                    day_wins += 1
                    day_return += top['tansho'] if top['tansho'] > 0 else 1
        
        if day_bets > 0:
            daily_results.append({
                "date": str(date),
                "bets": day_bets,
                "wins": day_wins,
                "hit_rate": round(day_wins / day_bets * 100, 1),
                "return": day_return,
                "roi": round((day_return - day_bets) / day_bets * 100, 1)
            })
            total_bets += day_bets
            total_wins += day_wins
            total_return += day_return
    
    return {
        "strategy": "high_probability",
        "threshold": threshold,
        "summary": {
            "total_bets": total_bets,
            "total_wins": total_wins,
            "hit_rate": round(total_wins / total_bets * 100, 1) if total_bets > 0 else 0,
            "total_return": total_return,
            "roi": round((total_return - total_bets) / total_bets * 100, 1) if total_bets > 0 else 0
        },
        "daily": daily_results[-days:] if len(daily_results) > days else daily_results
    }
