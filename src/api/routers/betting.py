"""Betting Router - Betting optimization endpoints"""
from fastapi import APIRouter, Depends, Query
from typing import Optional, List, Dict
import pandas as pd
import numpy as np

from src.api.dependencies import get_predictor, get_dataframe, get_cache
from src.api.schemas.common import BettingOptimizeRequest, BetType
from src.features.preprocessing import preprocess, FEATURES
from src.portfolio.kelly import calculate_kelly_fraction
from src.portfolio.formation_optimizer import FormationOptimizer
from src.collector.downloader import Downloader
from src.parser.odds_parser import OddsParser
from src.cache.redis_client import RedisCache
from src.utils.logger import logger

router = APIRouter(prefix="/api", tags=["betting"])


@router.get("/odds")
async def get_odds(
    date: str = Query(..., pattern=r"^\d{8}$"),
    jyo: str = Query(..., pattern=r"^\d{1,2}$"),
    race: int = Query(..., ge=1, le=12),
    cache: RedisCache = Depends(get_cache)
):
    """Get real-time odds"""
    try:
        jyo_str = jyo.zfill(2)
        cache_key = f"odds:{date}:{jyo_str}:{race}"
        
        # Short cache for odds (1 minute)
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        downloader = Downloader()
        
        url2 = downloader.get_odds2n_url(date, jyo_str, race)
        url3 = downloader.get_odds3t_url(date, jyo_str, race)
        
        html2 = downloader.download_page(url2, max_age=60)
        html3 = downloader.download_page(url3, max_age=60)
        
        result = {
            "nirentan": OddsParser.parse_2rentan(html2) if html2 else {},
            "sanrentan": OddsParser.parse_3rentan(html3) if html3 else {}
        }
        
        cache.set(cache_key, result, ttl=60)
        
        return result
    except Exception as e:
        logger.error(f"Get odds error: {e}")
        return {"error": str(e)}


@router.post("/betting/optimize")
async def optimize_betting(request: BettingOptimizeRequest):
    """
    買い目最適化
    Kelly基準と期待値に基づき最適な資金配分を提案
    """
    try:
        jyo_str = request.jyo.zfill(2)
        
        # Get predictions
        model = get_predictor()
        df = get_dataframe()
        
        if df.empty:
            return {"error": "Dataset not found"}
        
        df['jyo_cd'] = df['jyo_cd'].astype(str).str.zfill(2)
        df['date'] = df['date'].astype(str)
        
        race_data = df[
            (df['date'] == request.date) & 
            (df['jyo_cd'] == jyo_str) & 
            (df['race_no'] == request.race)
        ]
        
        if race_data.empty:
            return {"error": "Race data not found"}
        
        # Preprocess and predict
        race_processed = preprocess(race_data, is_training=False)
        X = race_processed[FEATURES]
        probs = model.predict(X)
        
        # Get odds
        downloader = Downloader()
        
        if request.bet_type in [BetType.NIRENTAN, BetType.NIRENUFUKU]:
            url = downloader.get_odds2n_url(request.date, jyo_str, request.race)
            html = downloader.download_page(url, max_age=60)
            odds = OddsParser.parse_2rentan(html) if html else {}
        else:
            url = downloader.get_odds3t_url(request.date, jyo_str, request.race)
            html = downloader.download_page(url, max_age=60)
            odds = OddsParser.parse_3rentan(html) if html else {}
        
        # Calculate optimal bets
        recommendations = _calculate_optimal_bets(
            probs=probs,
            race_data=race_data,
            odds=odds,
            budget=request.budget,
            bet_type=request.bet_type,
            kelly_fraction=request.kelly_fraction
        )
        
        return {
            "status": "success",
            "budget": request.budget,
            "bet_type": request.bet_type.value,
            "recommendations": recommendations,
            "total_bet": sum(r['amount'] for r in recommendations),
            "expected_return": sum(r['expected_return'] for r in recommendations)
        }
        
    except Exception as e:
        logger.error(f"Betting optimize error: {e}")
        return {"error": str(e)}


@router.post("/betting/formation")
async def optimize_formation(
    date: str,
    jyo: str,
    race: int,
    budget: float = 10000,
    formation_type: str = "box"  # box, formation, flow
):
    """
    フォーメーション/ボックス最適化
    """
    try:
        jyo_str = jyo.zfill(2)
        
        model = get_predictor()
        df = get_dataframe()
        
        if df.empty:
            return {"error": "Dataset not found"}
        
        df['jyo_cd'] = df['jyo_cd'].astype(str).str.zfill(2)
        df['date'] = df['date'].astype(str)
        
        race_data = df[
            (df['date'] == date) & 
            (df['jyo_cd'] == jyo_str) & 
            (df['race_no'] == race)
        ]
        
        if race_data.empty:
            return {"error": "Race data not found"}
        
        # Predict
        race_processed = preprocess(race_data, is_training=False)
        X = race_processed[FEATURES]
        probs = model.predict(X)
        
        # Sort by probability
        boat_probs = list(zip(race_data['boat_no'].tolist(), probs))
        boat_probs.sort(key=lambda x: x[1], reverse=True)
        
        # Get top boats
        top_boats = [int(bp[0]) for bp in boat_probs[:4]]
        
        if formation_type == "box":
            # 3艇ボックス（上位3艇）
            combos = _generate_box_combos(top_boats[:3])
        elif formation_type == "formation":
            # フォーメーション（1着固定）
            head = top_boats[0]
            combos = _generate_formation_combos(head, top_boats[1:4])
        else:  # flow
            # 流し（1-2着固定）
            combos = _generate_flow_combos(top_boats[:2], top_boats[2:4])
        
        # Calculate amounts per combo
        amount_per_combo = budget / len(combos) if combos else 0
        
        return {
            "status": "success",
            "formation_type": formation_type,
            "top_boats": top_boats,
            "combos": combos,
            "amount_per_combo": int(amount_per_combo / 100) * 100,  # Round to 100 yen
            "total_combos": len(combos),
            "total_bet": int(amount_per_combo / 100) * 100 * len(combos)
        }
        
    except Exception as e:
        logger.error(f"Formation optimize error: {e}")
        return {"error": str(e)}


def _calculate_optimal_bets(
    probs: np.ndarray,
    race_data: pd.DataFrame,
    odds: dict,
    budget: float,
    bet_type: BetType,
    kelly_fraction: float
) -> List[Dict]:
    """Calculate optimal bet amounts using Kelly criterion"""
    
    recommendations = []
    boat_nos = race_data['boat_no'].tolist()
    
    # Create probability mapping
    prob_map = {int(boat_nos[i]): probs[i] for i in range(len(probs))}
    
    # Calculate EV for each combo
    for combo_tuple, odds_value in odds.items():
        if odds_value <= 0:
            continue
        
        # Calculate joint probability
        if bet_type in [BetType.NIRENTAN, BetType.NIRENUFUKU]:
            if len(combo_tuple) != 2:
                continue
            joint_prob = prob_map.get(combo_tuple[0], 0) * prob_map.get(combo_tuple[1], 0) * 0.5
        else:  # 3rentan
            if len(combo_tuple) != 3:
                continue
            joint_prob = (
                prob_map.get(combo_tuple[0], 0) * 
                prob_map.get(combo_tuple[1], 0) * 
                prob_map.get(combo_tuple[2], 0) * 0.2
            )
        
        # Expected Value
        ev = joint_prob * odds_value
        
        # Only recommend if EV > 1 (positive expectation)
        if ev > 1.0:
            # Kelly fraction
            kelly_bet = calculate_kelly_fraction(joint_prob, odds_value) * kelly_fraction
            recommended_amount = int(budget * kelly_bet / 100) * 100  # Round to 100
            
            if recommended_amount >= 100:
                combo_str = "-".join(map(str, combo_tuple))
                recommendations.append({
                    "combo": combo_str,
                    "odds": odds_value,
                    "probability": joint_prob,
                    "ev": ev,
                    "amount": recommended_amount,
                    "expected_return": recommended_amount * ev
                })
    
    # Sort by EV and limit to top 10
    recommendations.sort(key=lambda x: x['ev'], reverse=True)
    return recommendations[:10]


def _generate_box_combos(boats: List[int]) -> List[str]:
    """Generate all 3-boat box combinations"""
    from itertools import permutations
    combos = []
    for perm in permutations(boats, 3):
        combos.append("-".join(map(str, perm)))
    return combos


def _generate_formation_combos(head: int, followers: List[int]) -> List[str]:
    """Generate formation combinations with fixed head"""
    from itertools import permutations
    combos = []
    for perm in permutations(followers, 2):
        combos.append(f"{head}-{perm[0]}-{perm[1]}")
    return combos


def _generate_flow_combos(heads: List[int], followers: List[int]) -> List[str]:
    """Generate flow combinations with fixed 1-2"""
    combos = []
    for follower in followers:
        combos.append(f"{heads[0]}-{heads[1]}-{follower}")
    return combos
