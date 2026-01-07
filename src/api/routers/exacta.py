"""Exacta (2連単) Prediction Router"""
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import pandas as pd

router = APIRouter(prefix="/api", tags=["exacta"])

VENUE_NAMES = {
    "01": "桐生", "02": "戸田", "03": "江戸川", "04": "平和島", "05": "多摩川",
    "06": "浜名湖", "07": "蒲郡", "08": "常滑", "09": "津", "10": "三国",
    "11": "びわこ", "12": "住之江", "13": "尼崎", "14": "鳴門", "15": "丸亀",
    "16": "児島", "17": "宮島", "18": "徳山", "19": "下関", "20": "若松",
    "21": "芦屋", "22": "福岡", "23": "唐津", "24": "大村"
}

# 2連単の平均配当（コース組み合わせ別、概算）
EXACTA_AVG_ODDS = {
    (1, 2): 4.5, (1, 3): 6.0, (1, 4): 8.0, (1, 5): 12.0, (1, 6): 18.0,
    (2, 1): 8.0, (2, 3): 15.0, (2, 4): 20.0, (2, 5): 30.0, (2, 6): 40.0,
    (3, 1): 10.0, (3, 2): 18.0, (3, 4): 25.0, (3, 5): 35.0, (3, 6): 45.0,
    (4, 1): 12.0, (4, 2): 22.0, (4, 3): 28.0, (4, 5): 40.0, (4, 6): 50.0,
    (5, 1): 18.0, (5, 2): 30.0, (5, 3): 38.0, (5, 4): 45.0, (5, 6): 55.0,
    (6, 1): 25.0, (6, 2): 40.0, (6, 3): 48.0, (6, 4): 55.0, (6, 5): 60.0,
}


class ExactaPrediction(BaseModel):
    date: str
    jyo_cd: str
    jyo_name: str
    race_no: int
    first: int
    second: int
    probability: float
    expected_odds: float
    ev: float
    confidence: str
    start_time: Optional[str] = None


class ExactaResponse(BaseModel):
    timestamp: str
    total_predictions: int
    predictions: List[ExactaPrediction]
    strategy: str


def calculate_exacta_probability(group: pd.DataFrame) -> List[dict]:
    """Calculate 2連単 probabilities for all combinations"""
    results = []
    boats = group['boat_no'].unique()
    
    for first in boats:
        for second in boats:
            if first == second:
                continue
            
            first_row = group[group['boat_no'] == first]
            second_row = group[group['boat_no'] == second]
            
            if len(first_row) == 0 or len(second_row) == 0:
                continue
            
            p_first = first_row.iloc[0]['pred_prob']
            p_second = second_row.iloc[0]['pred_prob']
            
            # 2連単確率 = P(1着) × P(2着|1着でない)
            # 簡易計算: P(1着) × P(2着) × 補正係数
            # 補正: 1着が決まった後の2着確率は上がる
            remaining_prob = 1 - p_first
            if remaining_prob > 0:
                p_second_given = p_second / remaining_prob
            else:
                p_second_given = p_second
            
            p_exacta = p_first * min(p_second_given, 0.8)  # 上限80%
            
            results.append({
                'first': int(first),
                'second': int(second),
                'probability': p_exacta,
                'p_first': p_first,
                'p_second': p_second
            })
    
    return results


@router.get("/exacta", response_model=ExactaResponse)
async def get_exacta_predictions(
    date: str = Query(None, description="Date YYYYMMDD"),
    min_prob: float = Query(0.15, description="Minimum probability"),
    min_ev: float = Query(1.0, description="Minimum expected value"),
    max_results: int = Query(20, description="Maximum results")
):
    """Get 2連単 (exacta) predictions with expected value"""
    from src.api.dependencies import get_predictor, get_dataframe
    from src.features.preprocessing import preprocess, FEATURES
    
    if date is None:
        date = datetime.now().strftime("%Y%m%d")
    
    model = get_predictor()
    df = get_dataframe()
    
    if df.empty or model is None:
        return ExactaResponse(
            timestamp=datetime.now().isoformat(),
            total_predictions=0,
            predictions=[],
            strategy="exacta_ev"
        )
    
    # Filter to target date
    df = df[df['date'].astype(str) == date].copy()
    
    if df.empty:
        return ExactaResponse(
            timestamp=datetime.now().isoformat(),
            total_predictions=0,
            predictions=[],
            strategy="exacta_ev"
        )
    
    # Preprocess and predict
    processed = preprocess(df, is_training=False)
    available_features = [f for f in FEATURES if f in processed.columns]
    X = processed[available_features]
    probs = model.predict(X)
    processed['pred_prob'] = probs
    
    # Calculate exacta probabilities for each race
    all_predictions = []
    
    for (d, jyo, race), group in processed.groupby(['date', 'jyo_cd', 'race_no']):
        exacta_probs = calculate_exacta_probability(group)
        
        # Get start time
        start_time = None
        if 'start_time' in group.columns:
            st = group['start_time'].iloc[0]
            if pd.notna(st):
                start_time = str(st)
        
        jyo_str = str(jyo).zfill(2)
        
        for ep in exacta_probs:
            if ep['probability'] < min_prob:
                continue
            
            # Expected odds
            expected_odds = EXACTA_AVG_ODDS.get((ep['first'], ep['second']), 15.0)
            ev = ep['probability'] * expected_odds
            
            if ev < min_ev:
                continue
            
            # Confidence
            if ep['probability'] >= 0.3:
                confidence = "S"
            elif ep['probability'] >= 0.2:
                confidence = "A"
            elif ep['probability'] >= 0.15:
                confidence = "B"
            else:
                confidence = "C"
            
            all_predictions.append(ExactaPrediction(
                date=str(d),
                jyo_cd=jyo_str,
                jyo_name=VENUE_NAMES.get(jyo_str, f"会場{jyo}"),
                race_no=int(race),
                first=ep['first'],
                second=ep['second'],
                probability=round(ep['probability'], 4),
                expected_odds=expected_odds,
                ev=round(ev, 2),
                confidence=confidence,
                start_time=start_time
            ))
    
    # Sort by EV descending
    all_predictions.sort(key=lambda x: x.ev, reverse=True)
    predictions = all_predictions[:max_results]
    
    return ExactaResponse(
        timestamp=datetime.now().isoformat(),
        total_predictions=len(predictions),
        predictions=predictions,
        strategy="exacta_ev"
    )


@router.get("/exacta/backtest")
async def backtest_exacta(
    min_prob: float = Query(0.15),
    min_ev: float = Query(1.0),
    days: int = Query(7)
):
    """Backtest exacta strategy"""
    from src.api.dependencies import get_predictor, get_dataframe
    from src.features.preprocessing import preprocess, FEATURES
    
    model = get_predictor()
    df = get_dataframe()
    
    if df.empty or model is None:
        return {"error": "No data available"}
    
    # Convert rank
    df['rank_num'] = pd.to_numeric(df['rank'], errors='coerce')
    df = df.dropna(subset=['rank_num'])
    
    # Preprocess
    processed = preprocess(df, is_training=False)
    available_features = [f for f in FEATURES if f in processed.columns]
    X = processed[available_features]
    probs = model.predict(X)
    processed['pred_prob'] = probs
    processed['rank_num'] = df['rank_num'].values
    
    # Simulate
    total_bets = 0
    total_wins = 0
    total_return = 0
    
    for (date, jyo, race), group in processed.groupby(['date', 'jyo_cd', 'race_no']):
        exacta_probs = calculate_exacta_probability(group)
        
        # Get actual results
        first_place = group[group['rank_num'] == 1]
        second_place = group[group['rank_num'] == 2]
        
        if len(first_place) == 0 or len(second_place) == 0:
            continue
        
        actual_first = int(first_place.iloc[0]['boat_no'])
        actual_second = int(second_place.iloc[0]['boat_no'])
        
        for ep in exacta_probs:
            if ep['probability'] < min_prob:
                continue
            
            expected_odds = EXACTA_AVG_ODDS.get((ep['first'], ep['second']), 15.0)
            ev = ep['probability'] * expected_odds
            
            if ev < min_ev:
                continue
            
            total_bets += 1
            
            if ep['first'] == actual_first and ep['second'] == actual_second:
                total_wins += 1
                total_return += expected_odds * 100
    
    hit_rate = total_wins / total_bets * 100 if total_bets > 0 else 0
    roi = (total_return - total_bets * 100) / (total_bets * 100) * 100 if total_bets > 0 else 0
    
    return {
        "strategy": "exacta_ev",
        "params": {"min_prob": min_prob, "min_ev": min_ev},
        "summary": {
            "total_bets": total_bets,
            "total_wins": total_wins,
            "hit_rate": round(hit_rate, 1),
            "total_return": total_return,
            "roi": round(roi, 1)
        }
    }
