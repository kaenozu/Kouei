"""Racer-Motor-Course Compatibility Matrix Analysis"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json
import os

from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger()


@dataclass
class CompatibilityScore:
    """Compatibility analysis result"""
    racer_id: str
    motor_no: str
    course: int  # 1-6
    stadium: str
    score: float  # -1.0 to 1.0
    win_rate: float
    sample_size: int
    confidence: str  # S/A/B/C


class CompatibilityAnalyzer:
    """Analyze compatibility between racers, motors, and courses"""
    
    CACHE_PATH = "data/cache/compatibility_matrix.json"
    
    def __init__(self, data_path: str = None):
        self.data_path = data_path or settings.processed_data_path
        self.df: Optional[pd.DataFrame] = None
        self._cache: Dict = {}
    
    def load_data(self):
        """Load race data"""
        if self.df is None:
            if os.path.exists(self.data_path):
                self.df = pd.read_csv(self.data_path)
                logger.info(f"Loaded {len(self.df)} rows for compatibility analysis")
            else:
                logger.warning("Data file not found")
                self.df = pd.DataFrame()
    
    def _calculate_win_rate(self, subset: pd.DataFrame) -> Tuple[float, int]:
        """Calculate win rate and sample size for a subset"""
        if len(subset) == 0:
            return 0.0, 0
        
        wins = (subset['rank'] == 1).sum()
        total = len(subset)
        return wins / total if total > 0 else 0.0, total
    
    def _get_confidence(self, sample_size: int) -> str:
        """Determine confidence level based on sample size"""
        if sample_size >= 50:
            return "S"
        elif sample_size >= 20:
            return "A"
        elif sample_size >= 10:
            return "B"
        else:
            return "C"
    
    def analyze_racer_course(self, racer_id: str, stadium: str = None) -> Dict[int, CompatibilityScore]:
        """Analyze racer's performance by course position (1-6)"""
        self.load_data()
        
        if self.df.empty:
            return {}
        
        # Filter by racer
        racer_data = self.df[self.df['racer_id'].astype(str) == str(racer_id)]
        
        if stadium:
            racer_data = racer_data[racer_data['jyo_cd'].astype(str).str.zfill(2) == stadium.zfill(2)]
        
        results = {}
        
        # Overall baseline
        overall_win_rate, _ = self._calculate_win_rate(racer_data)
        
        for course in range(1, 7):
            course_data = racer_data[racer_data['boat_no'] == course]
            win_rate, sample_size = self._calculate_win_rate(course_data)
            
            # Score: how much better/worse than baseline
            score = win_rate - overall_win_rate if overall_win_rate > 0 else 0
            score = np.clip(score * 5, -1, 1)  # Normalize
            
            results[course] = CompatibilityScore(
                racer_id=racer_id,
                motor_no="",
                course=course,
                stadium=stadium or "all",
                score=float(score),
                win_rate=float(win_rate),
                sample_size=sample_size,
                confidence=self._get_confidence(sample_size)
            )
        
        return results
    
    def analyze_racer_motor(self, racer_id: str, stadium: str) -> Dict[str, float]:
        """Analyze racer's performance with different motors at a stadium"""
        self.load_data()
        
        if self.df.empty:
            return {}
        
        # Filter by racer and stadium
        data = self.df[
            (self.df['racer_id'].astype(str) == str(racer_id)) &
            (self.df['jyo_cd'].astype(str).str.zfill(2) == stadium.zfill(2))
        ]
        
        if 'motor_no' not in data.columns or data.empty:
            return {}
        
        results = {}
        overall_win_rate, _ = self._calculate_win_rate(data)
        
        for motor_no in data['motor_no'].unique():
            if pd.isna(motor_no):
                continue
            
            motor_data = data[data['motor_no'] == motor_no]
            win_rate, sample_size = self._calculate_win_rate(motor_data)
            
            if sample_size >= 3:  # Minimum threshold
                score = win_rate - overall_win_rate if overall_win_rate > 0 else win_rate
                results[str(motor_no)] = {
                    "score": float(np.clip(score * 5, -1, 1)),
                    "win_rate": float(win_rate),
                    "sample_size": sample_size
                }
        
        return results
    
    def analyze_motor_stadium(self, motor_no: str, stadium: str) -> Dict:
        """Analyze motor's overall performance at a stadium"""
        self.load_data()
        
        if self.df.empty or 'motor_no' not in self.df.columns:
            return {}
        
        motor_data = self.df[
            (self.df['motor_no'].astype(str) == str(motor_no)) &
            (self.df['jyo_cd'].astype(str).str.zfill(2) == stadium.zfill(2))
        ]
        
        win_rate, sample_size = self._calculate_win_rate(motor_data)
        
        # Compare with stadium average
        stadium_data = self.df[self.df['jyo_cd'].astype(str).str.zfill(2) == stadium.zfill(2)]
        stadium_avg, _ = self._calculate_win_rate(stadium_data)
        
        return {
            "motor_no": motor_no,
            "stadium": stadium,
            "win_rate": float(win_rate),
            "stadium_average": float(stadium_avg),
            "score": float(np.clip((win_rate - stadium_avg) * 5, -1, 1)),
            "sample_size": sample_size,
            "confidence": self._get_confidence(sample_size)
        }
    
    def get_full_compatibility_matrix(self, racer_id: str, motor_no: str, stadium: str, course: int) -> Dict:
        """Get comprehensive compatibility analysis"""
        self.load_data()
        
        results = {
            "racer_id": racer_id,
            "motor_no": motor_no,
            "stadium": stadium,
            "course": course,
            "analysis": {}
        }
        
        # 1. Racer-Course compatibility
        racer_course = self.analyze_racer_course(racer_id, stadium)
        if course in racer_course:
            results["analysis"]["racer_course"] = {
                "score": racer_course[course].score,
                "win_rate": racer_course[course].win_rate,
                "sample_size": racer_course[course].sample_size
            }
        
        # 2. Motor-Stadium performance
        motor_stats = self.analyze_motor_stadium(motor_no, stadium)
        results["analysis"]["motor_stadium"] = motor_stats
        
        # 3. Racer-Motor at stadium (if enough data)
        racer_motor = self.analyze_racer_motor(racer_id, stadium)
        if motor_no in racer_motor:
            results["analysis"]["racer_motor"] = racer_motor[motor_no]
        
        # 4. Combined score
        scores = []
        weights = []
        
        if "racer_course" in results["analysis"]:
            scores.append(results["analysis"]["racer_course"]["score"])
            weights.append(1.0)
        
        if motor_stats and "score" in motor_stats:
            scores.append(motor_stats["score"])
            weights.append(0.8)
        
        if "racer_motor" in results["analysis"]:
            scores.append(results["analysis"]["racer_motor"]["score"])
            weights.append(1.2)  # Higher weight for direct combination
        
        if scores:
            combined = sum(s * w for s, w in zip(scores, weights)) / sum(weights)
            results["combined_score"] = float(combined)
            results["recommendation"] = self._get_recommendation(combined)
        else:
            results["combined_score"] = 0.0
            results["recommendation"] = "データ不足"
        
        return results
    
    def _get_recommendation(self, score: float) -> str:
        """Get recommendation based on combined score"""
        if score > 0.5:
            return "非常に有利な組み合わせ"
        elif score > 0.2:
            return "やや有利"
        elif score > -0.2:
            return "標準的"
        elif score > -0.5:
            return "やや不利"
        else:
            return "不利な組み合わせ"
    
    def build_stadium_matrix(self, stadium: str) -> pd.DataFrame:
        """Build course-wise performance matrix for a stadium"""
        self.load_data()
        
        if self.df.empty:
            return pd.DataFrame()
        
        stadium_data = self.df[self.df['jyo_cd'].astype(str).str.zfill(2) == stadium.zfill(2)]
        
        # Calculate win rate by course
        matrix_data = []
        for course in range(1, 7):
            course_data = stadium_data[stadium_data['boat_no'] == course]
            win_rate, sample = self._calculate_win_rate(course_data)
            
            # Calculate 2nd/3rd place rates too
            second_rate = (course_data['rank'] == 2).sum() / len(course_data) if len(course_data) > 0 else 0
            third_rate = (course_data['rank'] == 3).sum() / len(course_data) if len(course_data) > 0 else 0
            
            matrix_data.append({
                "course": course,
                "win_rate": win_rate,
                "2nd_rate": second_rate,
                "3rd_rate": third_rate,
                "in_top3_rate": win_rate + second_rate + third_rate,
                "sample_size": sample
            })
        
        return pd.DataFrame(matrix_data)
    
    def save_cache(self):
        """Save analysis cache to file"""
        os.makedirs(os.path.dirname(self.CACHE_PATH), exist_ok=True)
        with open(self.CACHE_PATH, 'w', encoding='utf-8') as f:
            json.dump(self._cache, f, ensure_ascii=False, indent=2)
    
    def load_cache(self):
        """Load analysis cache from file"""
        if os.path.exists(self.CACHE_PATH):
            with open(self.CACHE_PATH, 'r', encoding='utf-8') as f:
                self._cache = json.load(f)


# Singleton
_analyzer: Optional[CompatibilityAnalyzer] = None


def get_compatibility_analyzer() -> CompatibilityAnalyzer:
    global _analyzer
    if _analyzer is None:
        _analyzer = CompatibilityAnalyzer()
    return _analyzer


if __name__ == "__main__":
    analyzer = get_compatibility_analyzer()
    
    # Example: Analyze racer course compatibility
    racer_courses = analyzer.analyze_racer_course("4444", "02")
    for course, score in racer_courses.items():
        print(f"Course {course}: {score.win_rate:.1%} win rate, score={score.score:.2f}")
