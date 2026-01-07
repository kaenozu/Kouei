"""Prediction Service - Business logic for predictions"""
from typing import Optional, List, Dict, Tuple
import pandas as pd
import numpy as np
from dataclasses import dataclass

from src.model.predictor import Predictor
from src.features.preprocessing import preprocess, FEATURES
from src.utils.logger import logger


@dataclass
class PredictionResult:
    boat_no: int
    racer_name: str
    probability: float
    motor_rank: str
    racer_rank: str
    expected_value: Optional[float] = None


@dataclass
class RaceDevelopment:
    逃げ: float
    差し: float
    捷り: float
    捷り差し: float
    まくり: float


class PredictionService:
    """Service for race predictions"""
    
    def __init__(self, predictor: Predictor):
        self.predictor = predictor
    
    def predict_race(
        self,
        race_data: pd.DataFrame
    ) -> Tuple[List[PredictionResult], str, List[str]]:
        """
        Predict race outcomes
        
        Returns:
            - List of predictions sorted by probability
            - Confidence level (S/A/B/C)
            - AI insights
        """
        if race_data.empty:
            return [], "C", []
        
        # Preprocess
        processed = preprocess(race_data, is_training=False)
        X = processed[FEATURES]
        
        # Predict
        probs = self.predictor.predict(X)
        
        # Build results
        results = []
        for i, (idx, row) in enumerate(race_data.iterrows()):
            results.append(PredictionResult(
                boat_no=int(row['boat_no']),
                racer_name=str(row.get('racer_name', f"Boat {row['boat_no']}")) if pd.notna(row.get('racer_name')) else f"Boat {row['boat_no']}",
                probability=float(probs[i]),
                motor_rank=self._get_motor_rank(row.get('motor_2ren', 0)),
                racer_rank=self._get_racer_rank(row.get('racer_win_rate', 0))
            ))
        
        # Sort by probability
        results.sort(key=lambda x: x.probability, reverse=True)
        
        # Confidence
        top_prob = results[0].probability if results else 0
        confidence = self._get_confidence(top_prob)
        
        # Insights
        insights = self._generate_insights(X, results)
        
        return results, confidence, insights
    
    def predict_development(self, predictions: List[PredictionResult]) -> RaceDevelopment:
        """レース展開予測"""
        prob_map = {p.boat_no: p.probability for p in predictions}
        
        boat1 = prob_map.get(1, 0)
        boat2 = prob_map.get(2, 0)
        boat3 = prob_map.get(3, 0)
        boat4 = prob_map.get(4, 0)
        
        total = boat1 + boat2 + boat3 + boat4
        if total == 0:
            total = 1
        
        return RaceDevelopment(
            逃げ=boat1 / total * 100,
            差し=(boat2 + boat3) / total * 50,
            捷り=boat4 / total * 80,
            捷り差し=(boat3 + boat4) / total * 40,
            まくり=(boat4 + boat2) / total * 30
        )
    
    def generate_betting_tips(
        self,
        predictions: List[PredictionResult],
        odds: Dict = None
    ) -> Dict:
        """Generate betting tips based on predictions"""
        if len(predictions) < 3:
            return {"nirentan": [], "sanrentan": []}
        
        head = predictions[0].boat_no
        followers = [p.boat_no for p in predictions[1:4]]
        
        tips_2rentan = [f"{head}-{f}" for f in followers[:2]]
        tips_3rentan = [f"{head}-{followers[0]}-{f}" for f in followers[1:3]]
        
        return {
            "nirentan": [{"combo": c, "ev": self._calc_ev(c, odds, predictions)} for c in tips_2rentan],
            "sanrentan": [{"combo": c, "ev": self._calc_ev(c, odds, predictions)} for c in tips_3rentan]
        }
    
    def _get_motor_rank(self, motor_2ren: float) -> str:
        if motor_2ren > 40:
            return "A"
        elif motor_2ren > 30:
            return "B"
        return "C"
    
    def _get_racer_rank(self, win_rate: float) -> str:
        if win_rate > 6.5:
            return "A"
        elif win_rate > 5.0:
            return "B"
        return "C"
    
    def _get_confidence(self, top_prob: float) -> str:
        if top_prob > 0.5:
            return "S"
        elif top_prob > 0.4:
            return "A"
        elif top_prob > 0.3:
            return "B"
        return "C"
    
    def _generate_insights(self, X: pd.DataFrame, results: List[PredictionResult]) -> List[str]:
        """Generate AI insights from model"""
        try:
            contribs = self.predictor.predict(X, pred_contrib=True)
            if results:
                top_idx = next((i for i, r in enumerate(results) if r.boat_no == results[0].boat_no), 0)
                row_contribs = contribs[top_idx]
                feat_contribs = dict(zip(FEATURES, row_contribs[:-1]))
                sorted_feats = sorted(feat_contribs.items(), key=lambda x: abs(x[1]), reverse=True)
                
                insights = []
                feature_names_jp = {
                    "racer_win_rate": "勝率",
                    "motor_2ren": "モーター性能",
                    "exhibition_time": "展示タイム",
                }
                
                for feat, val in sorted_feats[:3]:
                    name_jp = feature_names_jp.get(feat, feat)
                    if val > 0:
                        insights.append(f"{name_jp}の強さ")
                    elif val < -0.2:
                        insights.append(f"{name_jp}の不安要素")
                
                return insights if insights else ["総合的なバランス"]
        except:
            pass
        return ["総合的なバランス"]
    
    def _calc_ev(self, combo: str, odds: Dict, predictions: List[PredictionResult]) -> float:
        """Calculate expected value"""
        if not odds:
            return 0.0
        
        parts = [int(p) for p in combo.split('-')]
        joint_prob = 1.0
        for p in parts:
            boat_prob = next((r.probability for r in predictions if r.boat_no == p), 0.1)
            joint_prob *= boat_prob
        
        odds_val = odds.get(tuple(parts), 0)
        return joint_prob * odds_val
