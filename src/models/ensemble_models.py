"""
アンサンブルモデル拡張 - 季節別・天候別特化モデル
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Any
from datetime import datetime
import joblib
import os
from src.utils.logger import logger

class SeasonalEnsemble:
    """季節別モデルエンサンブル"""
    
    def __init__(self, models_dir="models/seasonal"):
        self.models_dir = models_dir
        self.models = {}
        self.season_models = {
            "spring": "model_spring.joblib",
            "summer": "model_summer.joblib", 
            "autumn": "model_autumn.joblib",
            "winter": "model_winter.joblib"
        }
        self.weather_models = {
            "sunny": "model_sunny.joblib",
            "cloudy": "model_cloudy.joblib",
            "rainy": "model_rainy.joblib",
            "windy": "model_windy.joblib"
        }
        self.load_models()
    
    def get_season(self, date_str: str) -> str:
        """日付から季節を判定"""
        month = datetime.strptime(date_str, "%Y-%m-%d").month
        
        if month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        elif month in [9, 10, 11]:
            return "autumn"
        else:
            return "winter"
    
    def classify_weather(self, weather: str, wind: float) -> str:
        """天候条件を分類"""
        weather_lower = weather.lower()
        
        if "雨" in weather_lower or weather_lower == "rainy":
            return "rainy"
        elif wind > 5.0:
            return "windy"
        elif "晴" in weather_lower or weather_lower == "sunny":
            return "sunny"
        else:
            return "cloudy"
    
    def load_models(self):
        """すべてのモデルを読み込み"""
        # 基本モデル
        base_path = "models/catboost_model.joblib"
        if os.path.exists(base_path):
            self.models["base_model"] = joblib.load(base_path)
            logger.info("Loaded base model")
        
        # 季節モデル
        for season, filename in self.season_models.items():
            path = os.path.join(self.models_dir, filename)
            if os.path.exists(path):
                self.models[f"season_{season}"] = joblib.load(path)
                logger.info(f"Loaded seasonal model: {season}")
        
        # 天候モデル
        for weather, filename in self.weather_models.items():
            path = os.path.join(self.models_dir, filename)
            if os.path.exists(path):
                self.models[f"weather_{weather}"] = joblib.load(path)
                logger.info(f"Loaded weather model: {weather}")
    
    def predict(self, features: Dict[str, Any]) -> Dict[str, float]:
        """アンサンブル予測"""
        predictions = {}
        weights = {}
        
        date_str = features.get("date", datetime.now().strftime("%Y-%m-%d"))
        weather = features.get("weather", "")
        wind = features.get("wind_speed", 0)
        
        season = self.get_season(date_str)
        weather_type = self.classify_weather(weather, wind)
        
        # 基本モデル予測
        base_model = self.models.get("base_model")
        if base_model:
            try:
                base_pred = base_model.predict_proba([features])[0][1]
                predictions["base"] = base_pred
                weights["base"] = 0.4
            except:
                predictions["base"] = 0.5
                weights["base"] = 0.4
        
        # 季節モデル予測
        season_key = f"season_{season}"
        season_model = self.models.get(season_key)
        if season_model:
            try:
                season_pred = season_model.predict_proba([features])[0][1]
                predictions["seasonal"] = season_pred
                weights["seasonal"] = 0.3
            except:
                predictions["seasonal"] = 0.5
                weights["seasonal"] = 0.3
        
        # 天候モデル予測
        weather_key = f"weather_{weather_type}"
        weather_model = self.models.get(weather_key)
        if weather_model:
            try:
                weather_pred = weather_model.predict_proba([features])[0][1]
                predictions["weather"] = weather_pred
                weights["weather"] = 0.3
            except:
                predictions["weather"] = 0.5
                weights["weather"] = 0.3
        
        # 重み付きアンサンブル
        if predictions:
            ensemble_pred = sum(pred * weights[key] for key, pred in predictions.items())
            ensemble_pred = max(0.01, min(0.99, ensemble_pred))  # 0.01-0.99にクリップ
            
            return {
                "probability": ensemble_pred,
                "predictions": predictions,
                "weights": weights,
                "season": season,
                "weather_type": weather_type,
                "confidence": self._calculate_confidence(predictions)
            }
        
        # フォールバック
        return {"probability": 0.5, "confidence": 0.1}
    
    def _calculate_confidence(self, predictions: Dict[str, float]) -> float:
        """予測の信頼度を計算"""
        if len(predictions) <= 1:
            return 0.1
        
        # 予測の分散から信頼度を計算
        probs = list(predictions.values())
        std_dev = np.std(probs)
        
        # 分散が小さいほど信頼度高い
        confidence = max(0.1, 1.0 - std_dev)
        return confidence

class RacerConditionAnalyzer:
    """選手コンディション分析器"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    def analyze_condition(self, racer_id: str, days: int = 30) -> Dict[str, Any]:
        """選手のコンディションを分析"""
        # 最近のレース成績取得
        try:
            recent_races = self.db.get_racer_recent_races(racer_id, days)
        except:
            recent_races = []
        
        if not recent_races:
            return {"condition": "unknown", "score": 0.5}
        
        # 各種指標計算
        win_rate = len([r for r in recent_races if r.get("result") == 1]) / len(recent_races)
        avg_finishing = np.mean([r.get("result", 4) for r in recent_races])
        
        # 直近5レースのトレンド
        recent_5 = recent_races[:5]
        trend = np.mean([3 - r.get("result", 4) for r in recent_5])  # 3を最高スコアとする
        
        # コンディションスコア計算
        condition_score = (win_rate * 0.4) + ((3 - avg_finishing) / 3 * 0.3) + (trend / 3 * 0.3)
        
        # コンディション判定
        if condition_score > 0.7:
            condition = "excellent"
        elif condition_score > 0.5:
            condition = "good"
        elif condition_score > 0.3:
            condition = "normal"
        else:
            condition = "poor"
        
        return {
            "condition": condition,
            "score": max(0, min(1, condition_score)),
            "win_rate": win_rate,
            "avg_finishing": avg_finishing,
            "trend": trend,
            "recent_races": len(recent_races)
        }

class WaveWindAnalyzer:
    """波浪・風向分析器"""
    
    def __init__(self):
        self.wave_thresholds = {
            "calm": 0.5,    # 0.5m以下
            "light": 1.5,   # 1.5m以下
            "moderate": 2.5, # 2.5m以下
            "rough": 5.0   # 5.0m以下
        }
    
    def analyze_conditions(self, wave_height: float, wind_speed: float, wind_direction: str) -> Dict[str, Any]:
        """波浪・風向条件を分析"""
        # 波浪状態判定
        if wave_height <= self.wave_thresholds["calm"]:
            wave_condition = "calm"
        elif wave_height <= self.wave_thresholds["light"]:
            wave_condition = "light"
        elif wave_height <= self.wave_thresholds["moderate"]:
            wave_condition = "moderate"
        else:
            wave_condition = "rough"
        
        # 風の強さ判定
        if wind_speed <= 2:
            wind_condition = "calm"
        elif wind_speed <= 5:
            wind_condition = "light"
        elif wind_speed <= 8:
            wind_condition = "moderate"
        else:
            wind_condition = "strong"
        
        # コース別有利不利判定
        course_advantage = self._calculate_course_advantage(wave_condition, wind_direction)
        
        return {
            "wave_condition": wave_condition,
            "wind_condition": wind_condition,
            "course_advantage": course_advantage,
            "overall_favorability": self._calculate_overall_favorability(wave_condition, wind_condition),
            "risk_level": self._calculate_risk_level(wave_condition, wind_condition)
        }
    
    def _calculate_course_advantage(self, wave: str, wind: str) -> Dict[str, float]:
        """コース別有利不利を計算"""
        advantage = {str(i): 1.0 for i in range(1, 7)}  # デフォルトは中立
        
        # 波浪の影響
        if wave == "rough":
            advantage["1"] *= 1.1  # 内モコ優位
            advantage["2"] *= 1.05
            advantage["6"] *= 0.9   # 外モコ不利
        elif wave == "calm":
            advantage["4"] *= 1.05  # センター有利
        
        # 風向きの影響（簡略化）
        if "back" in wind.lower():  # 追い風
            advantage["3"] *= 1.05
            advantage["4"] *= 1.05
        
        return advantage
    
    def _calculate_overall_favorability(self, wave: str, wind: str) -> float:
        """全体の好不調を0-1で評価"""
        wave_score = {"calm": 0.9, "light": 0.8, "moderate": 0.6, "rough": 0.4}[wave]
        wind_score = {"calm": 0.9, "light": 0.8, "moderate": 0.7, "strong": 0.5}[wind]
        
        return (wave_score + wind_score) / 2
    
    def _calculate_risk_level(self, wave: str, wind: str) -> str:
        """リスクレベルを判定"""
        if wave == "rough" or wind == "strong":
            return "high"
        elif wave == "moderate" or wind == "moderate":
            return "medium"
        else:
            return "low"
