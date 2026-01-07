from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import numpy as np
from sentence_transformers import SentenceTransformer
from ..database import get_db
from ..models.analysis import Database

router = APIRouter(prefix="/api/advanced", tags=["advanced"])

# レース類似性検索（ベクトルDB）
@router.get("/similar-races/{race_id}")
async def get_similar_races(race_id: str, db: Session = Depends(get_db)):
    """
    レース類似性検索 - ベクトル類似度
    """
    try:
        db_manager = Database(db)
        race = db_manager.get_race(race_id)
        if not race:
            raise HTTPException(status_code=404, detail="Race not found")
        
        # レース特徴量ベクトル化
        model = SentenceTransformer('all-MiniLM-L6-v2')
        race_features = f"{race['stadium']} {race['weather']} {race['wind']} {race['wave_height']}"
        race_vector = model.encode(race_features)
        
        # 過去レースとの類似度計算
        past_races = db_manager.get_past_races(days=365)
        similarities = []
        
        for past_race in past_races:
            past_features = f"{past_race['stadium']} {past_race['weather']} {past_race['wind']} {past_race['wave_height']}"
            past_vector = model.encode(past_features)
            
            similarity = np.dot(race_vector, past_vector) / (np.linalg.norm(race_vector) * np.linalg.norm(past_vector))
            if similarity > 0.7:  # 類似度閾値
                similarities.append({
                    "race": past_race,
                    "similarity": float(similarity)
                })
        
        return {"similar_races": sorted(similarities, key=lambda x: x["similarity"], reverse=True)[:10]}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 勝敗パターン分析
@router.get("/win-patterns/{racer_id}")
async def get_win_patterns(racer_id: str, days: int = 90, db: Session = Depends(get_db)):
    """
    選手の勝敗パターン分析
    """
    try:
        db_manager = Database(db)
        races = db_manager.get_racer_races(racer_id, days)
        
        patterns = {
            "win_rate_by_position": {},  # コース別勝率
            "weather_performance": {},   # 天候別成績
            "time_trend": [],            # 時系列成績
            "favorite_conditions": []    # 得意条件
        }
        
        # コース別勝率分析
        for position in range(1, 7):
            position_races = [r for r in races if r.get("position") == position]
            wins = [r for r in position_races if r.get("result") == 1]
            patterns["win_rate_by_position"][str(position)] = len(wins) / len(position_races) if position_races else 0
        
        # 天候別成績分析
        weather_conditions = set(r.get("weather", "") for r in races)
        for weather in weather_conditions:
            weather_races = [r for r in races if r.get("weather") == weather]
            wins = [r for r in weather_races if r.get("result") == 1]
            patterns["weather_performance"][weather] = len(wins) / len(weather_races) if weather_races else 0
        
        # 得意条件抽出
        best_conditions = []
        for weather, win_rate in patterns["weather_performance"].items():
            if win_rate > 0.6:  # 60%以上の勝率
                best_conditions.append({"condition": weather, "win_rate": win_rate})
        
        patterns["favorite_conditions"] = sorted(best_conditions, key=lambda x: x["win_rate"], reverse=True)
        
        return patterns
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 投資回収率最適化
@router.post("/optimize-roi")
async def optimize_roi(budget: int, risk_tolerance: float, db: Session = Depends(get_db)):
    """
    投資回収率(ROI)の最適化提案
    """
    try:
        db_manager = Database(db)
        today_races = db_manager.get_today_races()
        
        optimization_results = []
        remaining_budget = budget
        
        for race in today_races:
            # 予測取得
            prediction = await db_manager.get_race_prediction(race["id"])
            
            if prediction and prediction["confidence"] > 0.7:  # 高信頼度のみ
                # ケリー基準で最適ベット額計算
                edge = prediction["win_probability"] * 2.0 - 1  # 2.0倍払戻し想定
                kelly_fraction = edge / (2.0 - 1)  # ケリー比
                
                # リスク許容度を考慮
                optimal_bet = kelly_fraction * remaining_budget * risk_tolerance
                
                if optimal_bet > 0 and optimal_bet <= remaining_budget * 0.2:  # 1レース最大20%
                    optimization_results.append({
                        "race_id": race["id"],
                        "race": race,
                        "prediction": prediction,
                        "optimal_bet": max(100, int(optimal_bet)),  # 最低100円
                        "expected_value": prediction["win_probability"] * 2.0 * optimal_bet - optimal_bet,
                        "kelly_fraction": kelly_fraction
                    })
                    
                    remaining_budget -= optimization_results[-1]["optimal_bet"]
        
        # 投資効率ソート
        optimization_results.sort(key=lambda x: x["kelly_fraction"], reverse=True)
        
        return {
            "optimization_plan": optimization_results,
            "total_budget": budget,
            "allocated_budget": budget - remaining_budget,
            "expected_roi": sum(r["expected_value"] for r in optimization_results) / budget if optimization_results else 0
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# リスク管理指標
@router.get("/risk-metrics")
async def get_risk_metrics(days: int = 30, db: Session = Depends(get_db)):
    """
    リスク管理指標の計算
    """
    try:
        db_manager = Database(db)
        recent_races = db_manager.get_recent_races(days)
        predictions = db_manager.get_prediction_history(days)
        
        metrics = {
            "prediction_accuracy": 0,
            "volatility": 0,
            "max_drawdown": 0,
            "sharpe_ratio": 0,
            "risk_adjusted_return": 0
        }
        
        if predictions:
            # 予測精度計算
            correct = sum(1 for p in predictions if p["predicted_winner"] == p["actual_winner"])
            metrics["prediction_accuracy"] = correct / len(predictions)
            
            # リターン系列計算
            returns = [p.get("return", 0) for p in predictions]
            if returns:
                metrics["volatility"] = np.std(returns) / np.mean(returns) if np.mean(returns) != 0 else 0
                
                # 最大ドローダウン計算
                cumulative = np.cumsum(returns)
                peak = np.maximum.accumulate(cumulative)
                drawdown = (peak - cumulative) / peak
                metrics["max_drawdown"] = np.max(drawdown)
                
                # シャープレシオ計算
                if metrics["volatility"] != 0:
                    metrics["sharpe_ratio"] = np.mean(returns) / np.std(returns) * np.sqrt(365)
        
        return metrics
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
