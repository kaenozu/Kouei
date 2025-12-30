"""Weather and Tide Time Series Prediction"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import json
import os

from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger()


class WeatherPredictor:
    """Predict weather conditions at race time"""
    
    # Wind direction patterns (simplified)
    WIND_DIRECTION_MAP = {
        0: "無風", 1: "北", 2: "北東", 3: "東", 4: "南東",
        5: "南", 6: "南西", 7: "西", 8: "北西"
    }
    
    # Stadium-specific wind impact
    STADIUM_WIND_IMPACT = {
        "01": {"strong_wind_threshold": 4, "direction_impact": "north_unfavorable"},
        "02": {"strong_wind_threshold": 3, "direction_impact": "west_unfavorable"},
        "03": {"strong_wind_threshold": 4, "direction_impact": "all_impact"},  # 江戸川
        "04": {"strong_wind_threshold": 4, "direction_impact": "south_unfavorable"},
        "05": {"strong_wind_threshold": 5, "direction_impact": "minimal"},
        # ... other stadiums
    }
    
    def __init__(self, data_path: str = None):
        self.data_path = data_path or settings.processed_data_path
        self.historical_data: Optional[pd.DataFrame] = None
    
    def load_historical(self):
        """Load historical weather data"""
        if self.historical_data is None:
            if os.path.exists(self.data_path):
                df = pd.read_csv(self.data_path)
                # Keep unique weather readings per race
                self.historical_data = df.drop_duplicates(
                    subset=['date', 'jyo_cd', 'race_no']
                )[['date', 'jyo_cd', 'race_no', 'wind_speed', 'wind_direction', 
                   'wave_height', 'temperature', 'water_temperature', 'weather']].copy()
                logger.info(f"Loaded {len(self.historical_data)} weather records")
    
    def get_historical_pattern(
        self,
        stadium: str,
        month: int,
        hour: int
    ) -> Dict:
        """Get historical weather patterns for similar conditions"""
        self.load_historical()
        
        if self.historical_data is None or self.historical_data.empty:
            return {}
        
        # Filter by stadium
        data = self.historical_data[
            self.historical_data['jyo_cd'].astype(str).str.zfill(2) == stadium.zfill(2)
        ].copy()
        
        # Extract month (assuming date format is YYYYMMDD)
        data['month'] = pd.to_datetime(data['date'].astype(str), format='%Y%m%d').dt.month
        data = data[data['month'] == month]
        
        if data.empty:
            return {}
        
        return {
            "avg_wind_speed": float(data['wind_speed'].mean()),
            "std_wind_speed": float(data['wind_speed'].std()),
            "max_wind_speed": float(data['wind_speed'].max()),
            "avg_wave_height": float(data['wave_height'].mean()),
            "most_common_direction": int(data['wind_direction'].mode().iloc[0]) if len(data['wind_direction'].mode()) > 0 else 0,
            "avg_temperature": float(data['temperature'].mean()),
            "sample_size": len(data)
        }
    
    def predict_race_conditions(
        self,
        stadium: str,
        race_time: datetime,
        current_conditions: Dict
    ) -> Dict:
        """Predict conditions at race time based on current data and patterns"""
        hour = race_time.hour
        month = race_time.month
        
        # Get historical baseline
        historical = self.get_historical_pattern(stadium, month, hour)
        
        # Simple prediction: blend current with historical tendency
        # More sophisticated: could use ARIMA or simple regression
        
        current_wind = current_conditions.get('wind_speed', 0)
        current_wave = current_conditions.get('wave_height', 0)
        
        # Afternoon wind tends to pick up
        wind_adjustment = 0
        if 13 <= hour <= 16:
            wind_adjustment = 0.5  # Afternoon pickup
        elif hour >= 17:
            wind_adjustment = -0.3  # Evening calm
        
        predicted = {
            "wind_speed": max(0, current_wind + wind_adjustment),
            "wind_direction": current_conditions.get('wind_direction', 0),
            "wave_height": current_wave,
            "confidence": "high" if historical.get('sample_size', 0) > 50 else "medium"
        }
        
        # Add trend analysis
        if historical:
            # If current is much higher than average, likely to persist
            if current_wind > historical['avg_wind_speed'] + historical['std_wind_speed']:
                predicted['trend'] = "strong_wind_continuing"
            elif current_wind < historical['avg_wind_speed'] - historical['std_wind_speed']:
                predicted['trend'] = "calm_conditions"
            else:
                predicted['trend'] = "normal"
        
        return predicted
    
    def analyze_wind_impact(
        self,
        stadium: str,
        wind_speed: float,
        wind_direction: int
    ) -> Dict:
        """Analyze how wind conditions impact race outcomes"""
        impact = {
            "severity": "normal",
            "in_escape_impact": 0,
            "overturn_risk": 0,
            "recommended_strategy": "標準購入"
        }
        
        stadium_config = self.STADIUM_WIND_IMPACT.get(stadium.zfill(2), {})
        threshold = stadium_config.get('strong_wind_threshold', 5)
        
        if wind_speed >= threshold:
            impact['severity'] = "strong"
            impact['in_escape_impact'] = -0.15  # 1号艇のイン逃げ成功率低下
            impact['overturn_risk'] = 0.2
            impact['recommended_strategy'] = "荒れ展開を想定した広め購入"
        elif wind_speed >= threshold - 1:
            impact['severity'] = "moderate"
            impact['in_escape_impact'] = -0.05
            impact['recommended_strategy'] = "差し・まくりも考慮"
        
        # Direction-specific impact
        direction_name = self.WIND_DIRECTION_MAP.get(wind_direction, "")
        if stadium_config.get('direction_impact') == 'north_unfavorable' and '北' in direction_name:
            impact['in_escape_impact'] -= 0.05
            impact['notes'] = "北風時は1マークの旋回が難しくなる傾向"
        
        return impact
    
    def get_tide_prediction(
        self,
        stadium: str,
        race_time: datetime
    ) -> Dict:
        """Get tide prediction for race time"""
        # Simplified tide prediction
        # In production, integrate with tide API
        
        # Lunar cycle approximation
        lunar_day = (race_time.toordinal() % 29.5) / 29.5 * 2 * np.pi
        
        # Hour-based tide (semi-diurnal)
        hour_cycle = (race_time.hour / 12.0) * np.pi
        
        # Combined tide level (-1 to 1)
        tide_level = np.sin(lunar_day) * 0.5 + np.sin(hour_cycle) * 0.5
        
        return {
            "tide_level": float(tide_level),
            "tide_status": "満潮" if tide_level > 0.3 else "干潮" if tide_level < -0.3 else "中潮",
            "impact_on_race": self._get_tide_impact(stadium, tide_level)
        }
    
    def _get_tide_impact(self, stadium: str, tide_level: float) -> str:
        """Analyze tide impact on race"""
        # Some stadiums are more affected by tide
        tide_sensitive = ["03", "13", "14", "19"]  # 江戸川、尼崎、鳴門、下関
        
        if stadium.zfill(2) in tide_sensitive:
            if tide_level > 0.3:
                return "満潮時は水面が上がりターンが流れやすい"
            elif tide_level < -0.3:
                return "干潮時は水面低下でスピードが出やすい"
        
        return "通常の潮位"
    
    def get_comprehensive_forecast(
        self,
        stadium: str,
        race_time: datetime,
        current_conditions: Dict
    ) -> Dict:
        """Get comprehensive weather forecast and impact analysis"""
        weather = self.predict_race_conditions(stadium, race_time, current_conditions)
        wind_impact = self.analyze_wind_impact(
            stadium,
            weather['wind_speed'],
            weather['wind_direction']
        )
        tide = self.get_tide_prediction(stadium, race_time)
        
        # Overall race condition assessment
        conditions_score = 1.0
        if wind_impact['severity'] == 'strong':
            conditions_score -= 0.3
        if tide['tide_status'] == '干潮':
            conditions_score -= 0.1
        
        return {
            "weather": weather,
            "wind_impact": wind_impact,
            "tide": tide,
            "overall_assessment": {
                "stability_score": conditions_score,
                "recommendation": self._get_overall_recommendation(conditions_score)
            }
        }
    
    def _get_overall_recommendation(self, score: float) -> str:
        if score >= 0.8:
            return "安定したレース展開が予想されます。実力通りの結果になりやすい。"
        elif score >= 0.6:
            return "若干の波乱の可能性。押さえめの購入が無難。"
        else:
            return "荒れる可能性が高い。穴狙いも検討の余地あり。"


if __name__ == "__main__":
    predictor = WeatherPredictor()
    
    # Test forecast
    forecast = predictor.get_comprehensive_forecast(
        stadium="03",
        race_time=datetime.now() + timedelta(hours=1),
        current_conditions={
            "wind_speed": 4.5,
            "wind_direction": 3,
            "wave_height": 5
        }
    )
    
    print(json.dumps(forecast, indent=2, ensure_ascii=False))
