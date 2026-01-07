"""Wide (ワイド) and Place (複勝) Prediction Router"""
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import pandas as pd
import numpy as np

router = APIRouter(prefix="/api", tags=["wide"])

VENUE_NAMES = {
    "01": "桐生", "02": "戸田", "03": "江戸川", "04": "平和島", "05": "多摩川",
    "06": "浜名湖", "07": "蒲郡", "08": "常滑", "09": "津", "10": "三国",
    "11": "びわこ", "12": "住之江", "13": "尼崎", "14": "鳴門", "15": "丸亀",
    "16": "児島", "17": "宮島", "18": "徳山", "19": "下関", "20": "若松",
    "21": "芦屋", "22": "福岡", "23": "唐津", "24": "大村"
}

WIDE_AVG_ODDS = {
    (1, 2): 2.0, (1, 3): 2.5, (1, 4): 3.5, (1, 5): 5.0, (1, 6): 7.0,
    (2, 3): 5.0, (2, 4): 6.0, (2, 5): 8.0, (2, 6): 12.0,
    (3, 4): 7.0, (3, 5): 10.0, (3, 6): 15.0,
    (4, 5): 12.0, (4, 6): 18.0,
    (5, 6): 25.0,
}

PLACE_AVG_ODDS = {1: 1.2, 2: 2.5, 3: 3.0, 4: 4.0, 5: 5.5, 6: 7.0}


class WidePrediction(BaseModel):
    date: str
    jyo_cd: str
    jyo_name: str
    race_no: int
    boat1: int
    boat2: int
    probability: float
    expected_odds: float
    ev: float
    confidence: str
    start_time: Optional[str] = None


class PlacePrediction(BaseModel):
    date: str
    jyo_cd: str
    jyo_name: str
    race_no: int
    boat_no: int
    racer_name: Optional[str] = None
    probability: float
    expected_odds: float
    ev: float
    confidence: str
    start_time: Optional[str] = None


class WideResponse(BaseModel):
    timestamp: str
    total_predictions: int
    predictions: List[WidePrediction]
    strategy: str


class PlaceResponse(BaseModel):
    timestamp: str
    total_predictions: int
    predictions: List[PlacePrediction]
    strategy: str


def calculate_wide_probability(group: pd.DataFrame) -> List[dict]:
    """Calculate ワイド probabilities"""
    results = []
    boats = sorted(group['boat_no'].unique())
    COURSE_TOP3_RATE = {1: 0.72, 2: 0.58, 3: 0.55, 4: 0.50, 5: 0.40, 6: 0.35}
    
    for i, boat1 in enumerate(boats):
        for boat2 in boats[i+1:]:
            row1 = group[group['boat_no'] == boat1]
            row2 = group[group['boat_no'] == boat2]
            
            if len(row1) == 0 or len(row2) == 0:
                continue
            
            p1_win = row1.iloc[0]['pred_prob']
            p2_win = row2.iloc[0]['pred_prob']
            
            base1 = COURSE_TOP3_RATE.get(int(boat1), 0.5)
            base2 = COURSE_TOP3_RATE.get(int(boat2), 0.5)
            
            p1_top3 = min(0.9, p1_win * 2.5 + base1 * 0.3)
            p2_top3 = min(0.9, p2_win * 2.5 + base2 * 0.3)
            
            p_wide = p1_top3 * p2_top3 * 0.85
            
            results.append({
                'boat1': int(boat1),
                'boat2': int(boat2),
                'probability': p_wide
            })
    
    return results


def calculate_place_probability(group: pd.DataFrame) -> List[dict]:
    """Calculate 複勝 probabilities"""
    results = []
    COURSE_TOP3_RATE = {1: 0.72, 2: 0.58, 3: 0.55, 4: 0.50, 5: 0.40, 6: 0.35}
    
    for _, row in group.iterrows():
        boat_no = int(row['boat_no'])
        p_win = row['pred_prob']
        base_rate = COURSE_TOP3_RATE.get(boat_no, 0.5)
        p_top3 = min(0.95, p_win * 2.5 + base_rate * 0.3)
        
        racer_name = row.get('racer_name', None)
        if pd.isna(racer_name):
            racer_name = None
        
        results.append({
            'boat_no': boat_no,
            'racer_name': racer_name,
            'probability': p_top3
        })
    
    return results


@router.get("/wide", response_model=WideResponse)
async def get_wide_predictions(
    date: str = Query(None),
    min_prob: float = Query(0.3),
    min_ev: float = Query(1.0),
    max_results: int = Query(30)
):
    """Get ワイド predictions"""
    from src.api.dependencies import get_predictor, get_dataframe
    from src.features.preprocessing import preprocess, FEATURES
    
    if date is None:
        date = datetime.now().strftime("%Y%m%d")
    
    model = get_predictor()
    df = get_dataframe()
    
    if df.empty or model is None:
        return WideResponse(timestamp=datetime.now().isoformat(), total_predictions=0, predictions=[], strategy="wide_ev")
    
    df = df[df['date'].astype(str) == date].copy()
    
    if df.empty:
        return WideResponse(timestamp=datetime.now().isoformat(), total_predictions=0, predictions=[], strategy="wide_ev")
    
    processed = preprocess(df, is_training=False)
    available_features = [f for f in FEATURES if f in processed.columns]
    X = processed[available_features]
    probs = model.predict(X)
    processed['pred_prob'] = probs
    
    all_predictions = []
    
    for (d, jyo, race), group in processed.groupby(['date', 'jyo_cd', 'race_no']):
        wide_probs = calculate_wide_probability(group)
        
        start_time = group['start_time'].iloc[0] if 'start_time' in group.columns and pd.notna(group['start_time'].iloc[0]) else None
        jyo_str = str(jyo).zfill(2)
        
        for wp in wide_probs:
            if wp['probability'] < min_prob:
                continue
            
            key = (min(wp['boat1'], wp['boat2']), max(wp['boat1'], wp['boat2']))
            expected_odds = WIDE_AVG_ODDS.get(key, 5.0)
            ev = wp['probability'] * expected_odds
            
            if ev < min_ev:
                continue
            
            conf = "S" if wp['probability'] >= 0.5 else "A" if wp['probability'] >= 0.4 else "B" if wp['probability'] >= 0.3 else "C"
            
            all_predictions.append(WidePrediction(
                date=str(d), jyo_cd=jyo_str, jyo_name=VENUE_NAMES.get(jyo_str, f"会場{jyo}"),
                race_no=int(race), boat1=wp['boat1'], boat2=wp['boat2'],
                probability=round(wp['probability'], 4), expected_odds=expected_odds,
                ev=round(ev, 2), confidence=conf, start_time=str(start_time) if start_time else None
            ))
    
    all_predictions.sort(key=lambda x: x.ev, reverse=True)
    return WideResponse(timestamp=datetime.now().isoformat(), total_predictions=len(all_predictions[:max_results]), predictions=all_predictions[:max_results], strategy="wide_ev")


@router.get("/place", response_model=PlaceResponse)
async def get_place_predictions(
    date: str = Query(None),
    min_prob: float = Query(0.5),
    min_ev: float = Query(1.0),
    max_results: int = Query(30)
):
    """Get 複勝 predictions"""
    from src.api.dependencies import get_predictor, get_dataframe
    from src.features.preprocessing import preprocess, FEATURES
    
    if date is None:
        date = datetime.now().strftime("%Y%m%d")
    
    model = get_predictor()
    df = get_dataframe()
    
    if df.empty or model is None:
        return PlaceResponse(timestamp=datetime.now().isoformat(), total_predictions=0, predictions=[], strategy="place_ev")
    
    df = df[df['date'].astype(str) == date].copy()
    
    if df.empty:
        return PlaceResponse(timestamp=datetime.now().isoformat(), total_predictions=0, predictions=[], strategy="place_ev")
    
    processed = preprocess(df, is_training=False)
    available_features = [f for f in FEATURES if f in processed.columns]
    X = processed[available_features]
    probs = model.predict(X)
    processed['pred_prob'] = probs
    
    if 'racer_name' in df.columns:
        processed['racer_name'] = df['racer_name'].values
    
    all_predictions = []
    
    for (d, jyo, race), group in processed.groupby(['date', 'jyo_cd', 'race_no']):
        place_probs = calculate_place_probability(group)
        
        start_time = group['start_time'].iloc[0] if 'start_time' in group.columns and pd.notna(group['start_time'].iloc[0]) else None
        jyo_str = str(jyo).zfill(2)
        
        for pp in place_probs:
            if pp['probability'] < min_prob:
                continue
            
            expected_odds = PLACE_AVG_ODDS.get(pp['boat_no'], 3.0)
            ev = pp['probability'] * expected_odds
            
            if ev < min_ev:
                continue
            
            conf = "S" if pp['probability'] >= 0.75 else "A" if pp['probability'] >= 0.65 else "B" if pp['probability'] >= 0.55 else "C"
            
            all_predictions.append(PlacePrediction(
                date=str(d), jyo_cd=jyo_str, jyo_name=VENUE_NAMES.get(jyo_str, f"会場{jyo}"),
                race_no=int(race), boat_no=pp['boat_no'], racer_name=pp['racer_name'],
                probability=round(pp['probability'], 4), expected_odds=expected_odds,
                ev=round(ev, 2), confidence=conf, start_time=str(start_time) if start_time else None
            ))
    
    all_predictions.sort(key=lambda x: x.ev, reverse=True)
    return PlaceResponse(timestamp=datetime.now().isoformat(), total_predictions=len(all_predictions[:max_results]), predictions=all_predictions[:max_results], strategy="place_ev")


@router.get("/wide/backtest")
async def backtest_wide(min_prob: float = Query(0.3), min_ev: float = Query(1.0), max_races: int = Query(500)):
    """Backtest ワイド strategy (sampled for speed)"""
    from src.api.dependencies import get_predictor, get_dataframe
    from src.features.preprocessing import preprocess, FEATURES
    
    model = get_predictor()
    df = get_dataframe()
    
    if df.empty or model is None:
        return {"error": "No data available"}
    
    df['rank_num'] = pd.to_numeric(df['rank'], errors='coerce')
    df = df.dropna(subset=['rank_num'])
    
    # Sample races for faster backtest
    race_keys = df[['date', 'jyo_cd', 'race_no']].drop_duplicates()
    if len(race_keys) > max_races:
        race_keys = race_keys.sample(n=max_races, random_state=42)
    
    df = df.merge(race_keys, on=['date', 'jyo_cd', 'race_no'])
    
    processed = preprocess(df, is_training=False)
    available_features = [f for f in FEATURES if f in processed.columns]
    X = processed[available_features]
    probs = model.predict(X)
    processed['pred_prob'] = probs
    processed['rank_num'] = df['rank_num'].values
    
    total_bets = 0
    total_wins = 0
    total_return = 0
    
    for (date, jyo, race), group in processed.groupby(['date', 'jyo_cd', 'race_no']):
        wide_probs = calculate_wide_probability(group)
        top3 = set(group[group['rank_num'] <= 3]['boat_no'].astype(int).tolist())
        
        if len(top3) < 3:
            continue
        
        # Only bet on top 3 predictions per race
        sorted_probs = sorted(wide_probs, key=lambda x: x['probability'], reverse=True)[:3]
        
        for wp in sorted_probs:
            if wp['probability'] < min_prob:
                continue
            
            key = (min(wp['boat1'], wp['boat2']), max(wp['boat1'], wp['boat2']))
            expected_odds = WIDE_AVG_ODDS.get(key, 5.0)
            ev = wp['probability'] * expected_odds
            
            if ev < min_ev:
                continue
            
            total_bets += 1
            
            if wp['boat1'] in top3 and wp['boat2'] in top3:
                total_wins += 1
                total_return += expected_odds * 100
    
    hit_rate = total_wins / total_bets * 100 if total_bets > 0 else 0
    roi = (total_return - total_bets * 100) / (total_bets * 100) * 100 if total_bets > 0 else 0
    
    return {
        "strategy": "wide_ev",
        "params": {"min_prob": min_prob, "min_ev": min_ev, "sampled_races": len(race_keys)},
        "summary": {
            "total_bets": total_bets,
            "total_wins": total_wins,
            "hit_rate": round(hit_rate, 1),
            "total_return": round(total_return, 0),
            "roi": round(roi, 1)
        }
    }


@router.get("/place/backtest")
async def backtest_place(min_prob: float = Query(0.5), min_ev: float = Query(1.0), max_races: int = Query(500)):
    """Backtest 複勝 strategy (sampled for speed)"""
    from src.api.dependencies import get_predictor, get_dataframe
    from src.features.preprocessing import preprocess, FEATURES
    
    model = get_predictor()
    df = get_dataframe()
    
    if df.empty or model is None:
        return {"error": "No data available"}
    
    df['rank_num'] = pd.to_numeric(df['rank'], errors='coerce')
    df = df.dropna(subset=['rank_num'])
    
    # Sample races
    race_keys = df[['date', 'jyo_cd', 'race_no']].drop_duplicates()
    if len(race_keys) > max_races:
        race_keys = race_keys.sample(n=max_races, random_state=42)
    
    df = df.merge(race_keys, on=['date', 'jyo_cd', 'race_no'])
    
    processed = preprocess(df, is_training=False)
    available_features = [f for f in FEATURES if f in processed.columns]
    X = processed[available_features]
    probs = model.predict(X)
    processed['pred_prob'] = probs
    processed['rank_num'] = df['rank_num'].values
    
    total_bets = 0
    total_wins = 0
    total_return = 0
    
    for (date, jyo, race), group in processed.groupby(['date', 'jyo_cd', 'race_no']):
        place_probs = calculate_place_probability(group)
        top3 = set(group[group['rank_num'] <= 3]['boat_no'].astype(int).tolist())
        
        if len(top3) < 3:
            continue
        
        # Only bet on top prediction per race
        sorted_probs = sorted(place_probs, key=lambda x: x['probability'], reverse=True)[:1]
        
        for pp in sorted_probs:
            if pp['probability'] < min_prob:
                continue
            
            expected_odds = PLACE_AVG_ODDS.get(pp['boat_no'], 3.0)
            ev = pp['probability'] * expected_odds
            
            if ev < min_ev:
                continue
            
            total_bets += 1
            
            if pp['boat_no'] in top3:
                total_wins += 1
                total_return += expected_odds * 100
    
    hit_rate = total_wins / total_bets * 100 if total_bets > 0 else 0
    roi = (total_return - total_bets * 100) / (total_bets * 100) * 100 if total_bets > 0 else 0
    
    return {
        "strategy": "place_ev",
        "params": {"min_prob": min_prob, "min_ev": min_ev, "sampled_races": len(race_keys)},
        "summary": {
            "total_bets": total_bets,
            "total_wins": total_wins,
            "hit_rate": round(hit_rate, 1),
            "total_return": round(total_return, 0),
            "roi": round(roi, 1)
        }
    }
