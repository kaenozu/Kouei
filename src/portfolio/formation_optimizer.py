"""Formation and Box Betting Optimizer with Kelly Criterion"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from itertools import permutations, combinations
import json

from src.config.settings import settings
from src.utils.logger import get_logger
from src.portfolio.kelly import calculate_kelly_fraction

logger = get_logger()


@dataclass
class BetRecommendation:
    """Recommended bet"""
    bet_type: str  # tansho, nirentan, sanrentan, nifuku, sanfuku
    combination: str  # e.g., "1-2-3" or "1-2" or "box:1,2,3"
    probability: float
    odds: float
    expected_value: float
    kelly_fraction: float
    recommended_amount: int
    risk_level: str  # low, medium, high


@dataclass
class FormationBet:
    """Formation bet structure"""
    heads: List[int]  # 1st place candidates
    seconds: List[int]  # 2nd place candidates  
    thirds: List[int]  # 3rd place candidates
    bet_type: str  # sanrentan, sanfuku
    total_combinations: int
    total_cost: int
    expected_return: float
    expected_value: float


class FormationOptimizer:
    """Optimize formation and box betting strategies"""
    
    BET_UNIT = 100  # Minimum bet in JPY
    
    def __init__(self, bankroll: int = 100000):
        self.bankroll = bankroll
    
    def calculate_joint_probability(
        self,
        predictions: List[Dict],
        combination: Tuple[int, ...]
    ) -> float:
        """Calculate joint probability for a combination"""
        # predictions: [{"boat_no": 1, "probability": 0.4}, ...]
        prob_map = {p['boat_no']: p['probability'] for p in predictions}
        
        # For exacta/trifecta, we need conditional probability
        # Simplified: P(A wins) * P(B 2nd | A wins) * P(C 3rd | A,B)
        # Approximation using raw probabilities with decay
        
        total_prob = sum(p['probability'] for p in predictions)
        remaining_prob = total_prob
        joint_prob = 1.0
        
        for i, boat in enumerate(combination):
            boat_prob = prob_map.get(boat, 0.01)
            
            # Conditional probability approximation
            if remaining_prob > 0:
                cond_prob = boat_prob / remaining_prob
                joint_prob *= min(cond_prob, 0.9)  # Cap at 90%
                remaining_prob -= boat_prob
            else:
                joint_prob *= 0.01
        
        return joint_prob
    
    def calculate_ev(
        self,
        probability: float,
        odds: float
    ) -> float:
        """Calculate Expected Value"""
        return probability * odds
    
    def optimize_tansho(
        self,
        predictions: List[Dict],
        odds: Dict[int, float]
    ) -> List[BetRecommendation]:
        """Optimize single win bets"""
        recommendations = []
        
        for pred in predictions:
            boat = pred['boat_no']
            prob = pred['probability']
            boat_odds = odds.get(boat, 1.0)
            
            ev = self.calculate_ev(prob, boat_odds)
            kelly = calculate_kelly_fraction(
                prob, boat_odds, settings.fractional_kelly
            )
            
            if ev > 1.0 and kelly > 0:  # Only positive EV bets
                amount = min(
                    int(self.bankroll * kelly / 100) * 100,
                    int(self.bankroll * settings.max_bet_percentage)
                )
                
                if amount >= settings.min_bet_amount:
                    recommendations.append(BetRecommendation(
                        bet_type="tansho",
                        combination=str(boat),
                        probability=prob,
                        odds=boat_odds,
                        expected_value=ev,
                        kelly_fraction=kelly,
                        recommended_amount=amount,
                        risk_level=self._get_risk_level(prob)
                    ))
        
        return sorted(recommendations, key=lambda x: x.expected_value, reverse=True)
    
    def optimize_exacta(
        self,
        predictions: List[Dict],
        odds: Dict[Tuple[int, int], float]
    ) -> List[BetRecommendation]:
        """Optimize exacta (2-rentan) bets"""
        recommendations = []
        boats = [p['boat_no'] for p in predictions]
        
        for combo in permutations(boats, 2):
            prob = self.calculate_joint_probability(predictions, combo)
            combo_odds = odds.get(combo, 1.0)
            
            if combo_odds <= 1.0:
                continue
            
            ev = self.calculate_ev(prob, combo_odds)
            kelly = calculate_kelly_fraction(
                prob, combo_odds, settings.fractional_kelly
            )
            
            if ev > 1.0 and kelly > 0.001:
                amount = min(
                    int(self.bankroll * kelly / 100) * 100,
                    int(self.bankroll * settings.max_bet_percentage * 0.5)
                )
                
                if amount >= settings.min_bet_amount:
                    recommendations.append(BetRecommendation(
                        bet_type="nirentan",
                        combination=f"{combo[0]}-{combo[1]}",
                        probability=prob,
                        odds=combo_odds,
                        expected_value=ev,
                        kelly_fraction=kelly,
                        recommended_amount=amount,
                        risk_level=self._get_risk_level(prob)
                    ))
        
        return sorted(recommendations, key=lambda x: x.expected_value, reverse=True)[:10]
    
    def optimize_trifecta(
        self,
        predictions: List[Dict],
        odds: Dict[Tuple[int, int, int], float]
    ) -> List[BetRecommendation]:
        """Optimize trifecta (3-rentan) bets"""
        recommendations = []
        boats = [p['boat_no'] for p in predictions]
        
        for combo in permutations(boats, 3):
            prob = self.calculate_joint_probability(predictions, combo)
            combo_odds = odds.get(combo, 1.0)
            
            if combo_odds <= 1.0:
                continue
            
            ev = self.calculate_ev(prob, combo_odds)
            kelly = calculate_kelly_fraction(
                prob, combo_odds, settings.fractional_kelly * 0.5  # More conservative
            )
            
            if ev > 1.2 and kelly > 0.0005:  # Higher threshold for trifecta
                amount = min(
                    int(self.bankroll * kelly / 100) * 100,
                    int(self.bankroll * settings.max_bet_percentage * 0.3)
                )
                
                if amount >= settings.min_bet_amount:
                    recommendations.append(BetRecommendation(
                        bet_type="sanrentan",
                        combination=f"{combo[0]}-{combo[1]}-{combo[2]}",
                        probability=prob,
                        odds=combo_odds,
                        expected_value=ev,
                        kelly_fraction=kelly,
                        recommended_amount=amount,
                        risk_level=self._get_risk_level(prob)
                    ))
        
        return sorted(recommendations, key=lambda x: x.expected_value, reverse=True)[:10]
    
    def optimize_formation(
        self,
        predictions: List[Dict],
        odds: Dict[Tuple, float],
        max_cost: int = 5000
    ) -> Optional[FormationBet]:
        """Optimize formation bet"""
        # Sort by probability
        sorted_preds = sorted(predictions, key=lambda x: x['probability'], reverse=True)
        boats = [p['boat_no'] for p in sorted_preds]
        
        # Try different formation sizes
        best_formation = None
        best_ev = 0
        
        # Formation patterns: heads x seconds x thirds
        patterns = [
            (1, 2, 3),  # 1-23-234 (6 combos)
            (1, 2, 4),  # 1-23-2345 (12 combos)
            (1, 3, 4),  # 1-234-2345 (24 combos)
            (2, 2, 3),  # 12-12-234 (8 combos)
            (2, 3, 4),  # 12-123-1234 (36 combos)
        ]
        
        for h_count, s_count, t_count in patterns:
            heads = boats[:h_count]
            seconds = boats[:s_count]
            thirds = boats[:t_count]
            
            # Generate all valid combinations
            combos = []
            for h in heads:
                for s in seconds:
                    if s == h:
                        continue
                    for t in thirds:
                        if t == h or t == s:
                            continue
                        combos.append((h, s, t))
            
            if not combos:
                continue
            
            total_cost = len(combos) * self.BET_UNIT
            if total_cost > max_cost:
                continue
            
            # Calculate expected return
            total_prob = 0
            total_expected = 0
            
            for combo in combos:
                prob = self.calculate_joint_probability(sorted_preds, combo)
                combo_odds = odds.get(combo, 10.0)  # Default odds
                total_prob += prob
                total_expected += prob * combo_odds * self.BET_UNIT
            
            ev = total_expected / total_cost if total_cost > 0 else 0
            
            if ev > best_ev:
                best_ev = ev
                best_formation = FormationBet(
                    heads=heads,
                    seconds=seconds,
                    thirds=thirds,
                    bet_type="sanrentan",
                    total_combinations=len(combos),
                    total_cost=total_cost,
                    expected_return=total_expected,
                    expected_value=ev
                )
        
        return best_formation
    
    def optimize_box(
        self,
        predictions: List[Dict],
        odds: Dict[Tuple, float],
        box_size: int = 3
    ) -> Optional[Dict]:
        """Optimize box bet (all permutations of selected boats)"""
        sorted_preds = sorted(predictions, key=lambda x: x['probability'], reverse=True)
        
        # Try different box combinations
        boats = [p['boat_no'] for p in sorted_preds]
        best_box = None
        best_ev = 0
        
        for box_boats in combinations(boats, box_size):
            combos = list(permutations(box_boats))
            total_cost = len(combos) * self.BET_UNIT
            
            total_expected = 0
            for combo in combos:
                prob = self.calculate_joint_probability(sorted_preds, combo)
                combo_odds = odds.get(combo, 10.0)
                total_expected += prob * combo_odds * self.BET_UNIT
            
            ev = total_expected / total_cost if total_cost > 0 else 0
            
            if ev > best_ev:
                best_ev = ev
                best_box = {
                    "boats": list(box_boats),
                    "total_combinations": len(combos),
                    "total_cost": total_cost,
                    "expected_return": total_expected,
                    "expected_value": ev,
                    "display": f"BOX {'-'.join(map(str, box_boats))}"
                }
        
        return best_box
    
    def get_optimal_strategy(
        self,
        predictions: List[Dict],
        tansho_odds: Dict[int, float],
        exacta_odds: Dict[Tuple[int, int], float],
        trifecta_odds: Dict[Tuple[int, int, int], float],
        budget: int = 10000
    ) -> Dict:
        """Get comprehensive optimal betting strategy"""
        self.bankroll = budget
        
        result = {
            "budget": budget,
            "recommendations": [],
            "total_bet": 0,
            "expected_return": 0
        }
        
        # 1. Tansho recommendations
        tansho_recs = self.optimize_tansho(predictions, tansho_odds)
        result["recommendations"].extend(tansho_recs[:2])
        
        # 2. Exacta recommendations
        exacta_recs = self.optimize_exacta(predictions, exacta_odds)
        result["recommendations"].extend(exacta_recs[:3])
        
        # 3. Trifecta recommendations
        trifecta_recs = self.optimize_trifecta(predictions, trifecta_odds)
        result["recommendations"].extend(trifecta_recs[:3])
        
        # 4. Formation recommendation
        formation = self.optimize_formation(predictions, trifecta_odds, max_cost=budget//3)
        if formation and formation.expected_value > 1.0:
            result["formation"] = {
                "heads": formation.heads,
                "seconds": formation.seconds,
                "thirds": formation.thirds,
                "combinations": formation.total_combinations,
                "cost": formation.total_cost,
                "expected_value": formation.expected_value
            }
        
        # 5. Box recommendation
        box = self.optimize_box(predictions, trifecta_odds)
        if box and box["expected_value"] > 1.0:
            result["box"] = box
        
        # Calculate totals
        result["total_bet"] = sum(r.recommended_amount for r in result["recommendations"])
        result["expected_return"] = sum(
            r.recommended_amount * r.expected_value for r in result["recommendations"]
        )
        
        return result
    
    def _get_risk_level(self, probability: float) -> str:
        """Determine risk level based on probability"""
        if probability > 0.3:
            return "low"
        elif probability > 0.15:
            return "medium"
        else:
            return "high"


if __name__ == "__main__":
    # Test
    optimizer = FormationOptimizer(bankroll=100000)
    
    predictions = [
        {"boat_no": 1, "probability": 0.40},
        {"boat_no": 3, "probability": 0.25},
        {"boat_no": 2, "probability": 0.15},
        {"boat_no": 4, "probability": 0.10},
        {"boat_no": 5, "probability": 0.06},
        {"boat_no": 6, "probability": 0.04},
    ]
    
    trifecta_odds = {
        (1, 3, 2): 8.5,
        (1, 2, 3): 12.0,
        (1, 3, 4): 15.0,
        (3, 1, 2): 25.0,
    }
    
    formation = optimizer.optimize_formation(predictions, trifecta_odds)
    if formation:
        print(f"Formation: {formation.heads}-{formation.seconds}-{formation.thirds}")
        print(f"Combos: {formation.total_combinations}, Cost: ¥{formation.total_cost}")
        print(f"EV: {formation.expected_value:.2f}")
