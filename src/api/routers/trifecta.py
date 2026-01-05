"""Trifecta (3連単) Prediction Router"""
from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import pandas as pd

router = APIRouter(prefix="/api", tags=["trifecta"])

VENUE_NAMES = {
    "01": "桐生", "02": "戸田", "03": "江戸川", "04": "平和島", "05": "多摩川",
    "06": "浜名湖", "07": "蒲郡", "08": "常滑", "09": "津", "10": "三国",
    "11": "びわこ", "12": "住之江", "13": "尼崎", "14": "鳴門", "15": "丸亀",
    "16": "児島", "17": "宮島", "18": "徳山", "19": "下関", "20": "若松",
    "21": "芦屋", "22": "福岡", "23": "唐津", "24": "大村"
}

# 3連単の平均配当（1着コース別、概算）
TRIFECTA_BASE_ODDS = {
    1: 25.0,   # 1号艇1着時の平均
    2: 60.0,   # 2号艇1着時
    3: 70.0,   # 3号艇1着時
    4: 80.0,   # 4号艇1着時
    5: 100.0,  # 5号艇1着時
    6: 120.0,  # 6号艇1着時
}

# 人気順での配当倍率（1番人気=1.0）
POPULARITY_MULTIPLIER = {
    1: 1.0, 2: 1.5, 3: 2.5, 4: 4.0, 5: 6.0, 6: 10.0,
    7: 15.0, 8: 20.0, 9: 30.0, 10: 50.0
}


class TrifectaPrediction(BaseModel):
    date: str
    jyo_cd: str
    jyo_name: str
    race_no: int
    first: int
    second: int
    third: int
    probability: float
    expected_odds: float
    ev: float
    confidence: str
    start_time: Optional[str] = None
    popularity_rank: Optional[int] = None


class TrifectaResponse(BaseModel):
    timestamp: str
    total_predictions: int
    predictions: List[TrifectaPrediction]
    strategy: str


def calculate_trifecta_probability(group: pd.DataFrame) -> List[dict]:
    """Calculate 3連単 probabilities for top combinations"""
    results = []
    
    # Sort by probability
    sorted_group = group.sort_values('pred_prob', ascending=False)
    boats = sorted_group['boat_no'].values[:6]  # Top 6
    probs = sorted_group['pred_prob'].values[:6]
    
    # Generate top combinations (limit to avoid explosion)
    combinations_checked = 0
    max_combinations = 50
    
    for i, first in enumerate(boats[:4]):  # Top 4 for first
        p1 = probs[i]
        
        for j, second in enumerate(boats):
            if second == first:
                continue
            p2 = probs[j]
            
            for k, third in enumerate(boats):
                if third == first or third == second:
                    continue
                p3 = probs[k]
                
                # 3連単確率計算
                # P(1着) × P(2着|1着以外) × P(3着|1,2着以外)
                remaining_after_1 = 1 - p1
                p2_given = p2 / remaining_after_1 if remaining_after_1 > 0 else p2
                
                remaining_after_2 = remaining_after_1 - p2
                p3_given = p3 / remaining_after_2 if remaining_after_2 > 0 else p3
                
                p_trifecta = p1 * min(p2_given, 0.7) * min(p3_given, 0.6)
                
                # 期待オッズ計算
                base_odds = TRIFECTA_BASE_ODDS.get(int(first), 50.0)
                # 2着3着の人気度で調整
                second_rank = list(boats).index(second) + 1 if second in boats else 6
                third_rank = list(boats).index(third) + 1 if third in boats else 6
                odds_mult = (POPULARITY_MULTIPLIER.get(second_rank, 5.0) + 
                            POPULARITY_MULTIPLIER.get(third_rank, 5.0)) / 2
                expected_odds = base_odds * odds_mult * 0.5  # 調整係数
                
                results.append({
                    'first': int(first),
                    'second': int(second),
                    'third': int(third),
                    'probability': p_trifecta,
                    'expected_odds': expected_odds,
                    'ev': p_trifecta * expected_odds,
                    'popularity_rank': combinations_checked + 1
                })
                
                combinations_checked += 1
                if combinations_checked >= max_combinations:
                    break
            if combinations_checked >= max_combinations:
                break
        if combinations_checked >= max_combinations:
            break
    
    # Sort by EV
    results.sort(key=lambda x: x['ev'], reverse=True)
    return results[:20]  # Top 20


@router.get("/trifecta", response_model=TrifectaResponse)
async def get_trifecta_predictions(
    date: str = Query(None, description="Date YYYYMMDD"),
    min_prob: float = Query(0.05, description="Minimum probability"),
    min_ev: float = Query(1.5, description="Minimum expected value"),
    max_results: int = Query(20, description="Maximum results")
):
    """Get 3連単 (trifecta) predictions with expected value"""
    from src.api.dependencies import get_predictor, get_dataframe
    from src.features.preprocessing import preprocess, FEATURES
    
    if date is None:
        date = datetime.now().strftime("%Y%m%d")
    
    model = get_predictor()
    df = get_dataframe()
    
    if df.empty or model is None:
        return TrifectaResponse(
            timestamp=datetime.now().isoformat(),
            total_predictions=0,
            predictions=[],
            strategy="trifecta_ev"
        )
    
    # Filter to target date
    df = df[df['date'].astype(str) == date].copy()
    
    if df.empty:
        return TrifectaResponse(
            timestamp=datetime.now().isoformat(),
            total_predictions=0,
            predictions=[],
            strategy="trifecta_ev"
        )
    
    # Preprocess and predict
    processed = preprocess(df, is_training=False)
    available_features = [f for f in FEATURES if f in processed.columns]
    X = processed[available_features]
    probs = model.predict(X)
    processed['pred_prob'] = probs
    
    # Calculate trifecta probabilities for each race
    all_predictions = []
    
    for (d, jyo, race), group in processed.groupby(['date', 'jyo_cd', 'race_no']):
        trifecta_probs = calculate_trifecta_probability(group)
        
        # Get start time
        start_time = None
        if 'start_time' in group.columns:
            st = group['start_time'].iloc[0]
            if pd.notna(st):
                start_time = str(st)
        
        jyo_str = str(jyo).zfill(2)
        
        for tp in trifecta_probs:
            if tp['probability'] < min_prob:
                continue
            if tp['ev'] < min_ev:
                continue
            
            # Confidence
            if tp['probability'] >= 0.15:
                confidence = "S"
            elif tp['probability'] >= 0.10:
                confidence = "A"
            elif tp['probability'] >= 0.07:
                confidence = "B"
            else:
                confidence = "C"
            
            all_predictions.append(TrifectaPrediction(
                date=str(d),
                jyo_cd=jyo_str,
                jyo_name=VENUE_NAMES.get(jyo_str, f"会場{jyo}"),
                race_no=int(race),
                first=tp['first'],
                second=tp['second'],
                third=tp['third'],
                probability=round(tp['probability'], 4),
                expected_odds=round(tp['expected_odds'], 1),
                ev=round(tp['ev'], 2),
                confidence=confidence,
                start_time=start_time,
                popularity_rank=tp.get('popularity_rank')
            ))
    
    # Sort by EV descending
    all_predictions.sort(key=lambda x: x.ev, reverse=True)
    predictions = all_predictions[:max_results]
    
    return TrifectaResponse(
        timestamp=datetime.now().isoformat(),
        total_predictions=len(predictions),
        predictions=predictions,
        strategy="trifecta_ev"
    )


@router.get("/trifecta/backtest")
async def backtest_trifecta(
    min_prob: float = Query(0.05),
    min_ev: float = Query(1.5),
    top_n: int = Query(3, description="Top N predictions per race")
):
    """Backtest trifecta strategy"""
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
        trifecta_probs = calculate_trifecta_probability(group)
        
        # Get actual results
        first_place = group[group['rank_num'] == 1]
        second_place = group[group['rank_num'] == 2]
        third_place = group[group['rank_num'] == 3]
        
        if len(first_place) == 0 or len(second_place) == 0 or len(third_place) == 0:
            continue
        
        actual_first = int(first_place.iloc[0]['boat_no'])
        actual_second = int(second_place.iloc[0]['boat_no'])
        actual_third = int(third_place.iloc[0]['boat_no'])
        
        # Check top N predictions
        bets_this_race = 0
        for tp in trifecta_probs[:top_n]:
            if tp['probability'] < min_prob:
                continue
            if tp['ev'] < min_ev:
                continue
            
            total_bets += 1
            bets_this_race += 1
            
            if (tp['first'] == actual_first and 
                tp['second'] == actual_second and 
                tp['third'] == actual_third):
                total_wins += 1
                total_return += tp['expected_odds'] * 100
    
    hit_rate = total_wins / total_bets * 100 if total_bets > 0 else 0
    roi = (total_return - total_bets * 100) / (total_bets * 100) * 100 if total_bets > 0 else 0
    
    return {
        "strategy": "trifecta_ev",
        "params": {"min_prob": min_prob, "min_ev": min_ev, "top_n": top_n},
        "summary": {
            "total_bets": total_bets,
            "total_wins": total_wins,
            "hit_rate": round(hit_rate, 2),
            "total_return": round(total_return, 0),
            "roi": round(roi, 1)
        }
    }
