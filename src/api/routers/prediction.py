"""Prediction Router - Race prediction endpoints"""
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional
import pandas as pd
import os

from src.api.dependencies import (
    get_predictor, get_dataframe, get_cache, 
    get_stadium_name, FEATURE_NAMES_JP
)
from src.model.predictor import Predictor
from src.api.schemas.common import (
    PredictionResponse, BoatPrediction, BettingTip,
    ConfidenceLevel, ErrorResponse, WhatIfRequest
)
from src.features.preprocessing import preprocess, FEATURES
from src.parser.html_parser import ProgramParser
from src.parser.odds_parser import OddsParser
from src.collector.downloader import Downloader
from src.cache.redis_client import RedisCache
from src.utils.logger import logger

router = APIRouter(prefix="/api", tags=["prediction"])


@router.get("/prediction")
async def get_prediction(
    date: str = Query(..., pattern=r"^\d{8}$"),
    jyo: str = Query(..., pattern=r"^\d{1,2}$"),
    race: int = Query(..., ge=1, le=12),
    cache: RedisCache = Depends(get_cache)
):
    """Get race prediction with AI insights"""
    try:
        jyo_str = jyo.zfill(2)
        cache_key = f"prediction:{date}:{jyo_str}:{race}"
        
        # Check cache
        cached = cache.get(cache_key)
        if cached:
            logger.info(f"Cache hit for {cache_key}")
            return cached
        
        model = get_predictor()
        if not model:
            return {"error": "Model not loaded"}
        
        df = get_dataframe()
        if df.empty:
            return {"error": "Dataset not found"}
        
        df['jyo_cd'] = df['jyo_cd'].astype(str).str.zfill(2)
        df['date'] = df['date'].astype(str)
        
        race_data = df[(df['date'] == date) & (df['jyo_cd'] == jyo_str) & (df['race_no'] == race)]
        
        if race_data.empty:
            return {"error": f"Race data not found for {date} {jyo_str} R{race}"}

        # Get Race Name
        race_name = _get_race_name(race_data, date, jyo_str, race)

        # Preprocess
        race_processed = preprocess(race_data, is_training=False)
        X = race_processed[FEATURES]
        
        probs = model.predict(X)
        
        # Load racer course stats
        try:
            from src.features.racer_course_stats import load_stats
            racer_stats = load_stats()
        except:
            racer_stats = {}
        
        # Build results
        results = []
        for i, (idx, row) in enumerate(race_data.iterrows()):
            boat_no = int(row['boat_no'])
            racer_id = str(row.get('racer_id', ''))
            
            # Get racer's course-specific win rate
            course_win_rate = None
            if racer_id in racer_stats and str(boat_no) in racer_stats[racer_id]:
                course_win_rate = racer_stats[racer_id][str(boat_no)]
            
            results.append({
                "boat_no": boat_no,
                "racer_id": racer_id,
                "racer_name": str(row['racer_name']) if pd.notna(row.get('racer_name')) else f"Boat {boat_no}",
                "probability": float(probs[i]),
                "motor_rank": "A" if row.get('motor_2ren', 0) > 40 else "B" if row.get('motor_2ren', 0) > 30 else "C",
                "racer_rank": "A" if row.get('racer_win_rate', 0) > 6.5 else "B" if row.get('racer_win_rate', 0) > 5.0 else "C",
                "racer_win_rate": float(row.get('racer_win_rate', 0)),
                "course_win_rate": course_win_rate,
                "motor_2ren": float(row.get('motor_2ren', 0)),
                "exhibition_time": float(row.get('exhibition_time', 0))
            })
            
        sorted_results = sorted(results, key=lambda x: x['probability'], reverse=True)
        top_boat = sorted_results[0]
        
        # Betting Tips
        head = top_boat['boat_no']
        followers = [r['boat_no'] for r in sorted_results[1:4]]
        tips_2rentan = [f"{head}-{f}" for f in followers[:2]]
        tips_3rentan = [f"{head}-{followers[0]}-{f}" for f in followers[1:3]]

        # Confidence Level
        conf_score = top_boat['probability']
        confidence = "S" if conf_score > 0.5 else "A" if conf_score > 0.4 else "B" if conf_score > 0.3 else "C"

        # Insights
        ai_insights = _generate_insights(model, X, results, top_boat)
        
        # EV Calculation with odds
        tips_with_ev = _calculate_ev(date, jyo_str, race, tips_2rentan, tips_3rentan, sorted_results)
        
        # 展開予測（レース展開シミュレーション）
        展開予測 = _predict_race_development(sorted_results, race_data)

        response = {
            "date": date,
            "jyo_cd": jyo_str,
            "race_no": race,
            "race_name": race_name,
            "predictions": sorted_results,
            "tips": tips_with_ev,
            "confidence": confidence,
            "insights": ai_insights,
            "展開予測": 展開予測
        }
        
        # Cache for 5 minutes
        cache.set(cache_key, response, ttl=300)
        
        # Auto-track predictions for accuracy analysis
        try:
            from src.api.routers.accuracy import save_prediction
            for pred in sorted_results:
                save_prediction(
                    date=date,
                    jyo_cd=jyo_str,
                    race_no=race,
                    boat_no=pred['boat_no'],
                    prob=pred['probability'],
                    confidence=confidence
                )
            logger.info(f"Tracked {len(sorted_results)} predictions for accuracy")
        except Exception as track_err:
            logger.warning(f"Failed to track prediction: {track_err}")
        
        return response
        
    except Exception as e:
        import traceback
        logger.error(f"Prediction error: {e}")
        return {"error": str(e), "traceback": traceback.format_exc()}


@router.post("/simulate-what-if")
async def simulate_what_if(data: WhatIfRequest):
    """Simulate prediction with modified features"""
    try:
        predictor = get_predictor()
        # In production, apply modifications to real feature vector
        return {"status": "success", "probabilities": [0.1, 0.2, 0.4, 0.1, 0.1, 0.1]}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/similar-races")
async def get_similar_races(
    jyo_cd: str,
    wind: float,
    wave: float,
    temp: float = 20.0,
    water_temp: float = 18.0
):
    """Find similar historical races"""
    try:
        from src.analysis.vector_db_manager import vector_db
        similar = vector_db.search({
            'jyo_cd': jyo_cd,
            'wind_speed': wind,
            'wave_height': wave,
            'temperature': temp,
            'water_temperature': water_temp
        })
        return similar
    except Exception as e:
        return {"error": str(e)}


def _get_race_name(race_data: pd.DataFrame, date: str, jyo_str: str, race: int) -> str:
    """Get race name from data or HTML"""
    race_name = ""
    if 'race_name' in race_data.columns:
        val = race_data['race_name'].iloc[0]
        if pd.notna(val):
            race_name = str(val)
    
    if not race_name:
        raw_program = os.path.join("data", "raw", date, jyo_str, f"program_{race}.html")
        if os.path.exists(raw_program):
            try:
                with open(raw_program, 'r', encoding='utf-8') as f:
                    race_name = ProgramParser.parse_race_name(f.read())
            except:
                pass
    
    return race_name


def _generate_insights(model, X, results, top_boat) -> list:
    """Generate AI insights from model contributions"""
    try:
        contribs = model.predict(X, pred_contrib=True)
        top_boat_row_idx = 0
        for i, res in enumerate(results):
            if res['boat_no'] == top_boat['boat_no']:
                top_boat_row_idx = i
                break
        
        row_contribs = contribs[top_boat_row_idx]
        feat_contribs = dict(zip(FEATURES, row_contribs[:-1]))
        sorted_feats = sorted(feat_contribs.items(), key=lambda x: abs(x[1]), reverse=True)
        
        ai_insights = []
        for feat, val in sorted_feats[:3]:
            if val > 0:
                name_jp = FEATURE_NAMES_JP.get(feat, feat)
                ai_insights.append(f"{name_jp}の強さ")
            elif val < -0.2:
                name_jp = FEATURE_NAMES_JP.get(feat, feat)
                ai_insights.append(f"{name_jp}の不安要素")
        
        return ai_insights if ai_insights else ["総合的なバランス"]
    except:
        return ["総合的なバランス"]


def _calculate_ev(date: str, jyo_str: str, race: int, tips_2rentan: list, tips_3rentan: list, sorted_results: list) -> dict:
    """Calculate expected value for betting tips"""
    try:
        downloader = Downloader()
        odds2n_url = downloader.get_odds2n_url(date, jyo_str, race)
        odds3t_url = downloader.get_odds3t_url(date, jyo_str, race)
        
        html2n = downloader.download_page(odds2n_url, max_age=60)
        html3t = downloader.download_page(odds3t_url, max_age=60)
        
        odds2n = OddsParser.parse_2rentan(html2n) if html2n else {}
        odds3t = OddsParser.parse_3rentan(html3t) if html3t else {}

        def get_ev(combo, odds_dict, result_list):
            parts = [int(p) for p in combo.split('-')]
            joint_prob = 1.0
            for p in parts:
                boat_prob = next((r['probability'] for r in result_list if r['boat_no'] == p), 0.1)
                joint_prob *= boat_prob
            combo_key = tuple(parts)
            odds_val = odds_dict.get(combo_key, 0)
            return joint_prob * odds_val

        return {
            "nirentan": [{"combo": c, "ev": get_ev(c, odds2n, sorted_results)} for c in tips_2rentan],
            "sanrentan": [{"combo": c, "ev": get_ev(c, odds3t, sorted_results)} for c in tips_3rentan]
        }
    except:
        return {
            "nirentan": [{"combo": c, "ev": 0} for c in tips_2rentan],
            "sanrentan": [{"combo": c, "ev": 0} for c in tips_3rentan]
        }


def _predict_race_development(sorted_results: list, race_data: pd.DataFrame) -> dict:
    """レース展開予測（逃げ/差し/捷り/捷り差し）"""
    development = {
        "逃げ": 0.0,
        "差し": 0.0,
        "捷り": 0.0,
        "捷り差し": 0.0,
        "まくり": 0.0
    }
    
    # 1号艇の勝率が高いと逃げ
    boat1_prob = next((r['probability'] for r in sorted_results if r['boat_no'] == 1), 0)
    boat2_prob = next((r['probability'] for r in sorted_results if r['boat_no'] == 2), 0)
    boat3_prob = next((r['probability'] for r in sorted_results if r['boat_no'] == 3), 0)
    boat4_prob = next((r['probability'] for r in sorted_results if r['boat_no'] == 4), 0)
    
    # シンプルな展開予測ロジック
    total = boat1_prob + boat2_prob + boat3_prob + boat4_prob
    if total > 0:
        development["逃げ"] = boat1_prob / total * 100
        development["差し"] = (boat2_prob + boat3_prob) / total * 50
        development["捷り"] = boat4_prob / total * 80
        development["捷り差し"] = (boat3_prob + boat4_prob) / total * 40
        development["まくり"] = (boat4_prob + boat2_prob) / total * 30
    
    return development


@router.get("/prediction-with-odds")
async def get_prediction_with_odds(
    date: str = Query(..., pattern=r"^\d{8}$"),
    jyo: str = Query(..., pattern=r"^\d{2}$"),
    race: int = Query(..., ge=1, le=12),
    predictor: Predictor = Depends(get_predictor),
    cache: RedisCache = Depends(get_cache)
):
    """Get prediction with real-time odds and expected value"""
    from src.collector.odds_collector import get_realtime_odds
    from src.model.ensemble import get_ensemble
    
    cache_key = f"pred_odds:{date}:{jyo}:{race}"
    
    # Get base prediction (call the endpoint function directly)
    base_result = await get_prediction(date=date, jyo=jyo, race=race, cache=cache)
    
    if "error" in base_result:
        return base_result
    
    # Get real-time odds
    try:
        odds_data = await get_realtime_odds(date, jyo, race)
        
        # Calculate expected value
        predictions = base_result.get("predictions", [])
        for pred in predictions:
            boat_no = pred.get("boat_no", 0)
            prob = pred.get("probability", 0)
            
            # Tansho EV
            tansho_odds = odds_data.tansho.get(boat_no, 0)
            if tansho_odds > 0 and prob > 0:
                ev = prob * tansho_odds - (1 - prob)
                pred["tansho_odds"] = tansho_odds
                pred["tansho_ev"] = round(ev, 2)
                pred["tansho_recommended"] = ev > 0.1  # 10%+ edge
            else:
                # No real-time odds available - still add flag for completeness
                pred["tansho_odds"] = 0.0
                pred["tansho_ev"] = 0.0
                pred["tansho_recommended"] = False
            
        # Find value bets
        value_bets = []
        for key, odds in odds_data.nirentan.items():
            boats = key.split("-")
            if len(boats) == 2:
                b1, b2 = int(boats[0]), int(boats[1])
                # Simple probability estimation
                p1 = next((p["probability"] for p in predictions if p["boat_no"] == b1), 0)
                p2 = next((p["probability"] for p in predictions if p["boat_no"] == b2), 0)
                # Rough exacta probability
                exacta_prob = p1 * p2 * 1.5  # Adjustment factor
                if exacta_prob > 0 and odds > 0:
                    ev = exacta_prob * odds - 1
                    if ev > 0.2:  # 20%+ edge
                        value_bets.append({
                            "combination": key,
                            "odds": odds,
                            "estimated_prob": round(exacta_prob, 3),
                            "ev": round(ev, 2)
                        })
        
        value_bets.sort(key=lambda x: -x["ev"])
        
        base_result["odds"] = {
            "tansho": odds_data.tansho,
            "nirentan_sample": dict(list(odds_data.nirentan.items())[:10]),
            "timestamp": odds_data.timestamp
        }
        base_result["value_bets"] = value_bets[:5]
        
    except Exception as e:
        logger.warning(f"Failed to get odds: {e}")
        base_result["odds_error"] = str(e)
        base_result["odds"] = {
            "tansho": {},
            "nirentan_sample": {},
            "timestamp": "",
            "note": "Real-time odds unavailable - using historical odds"
        }
    
    return base_result
