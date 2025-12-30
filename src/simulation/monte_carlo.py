import pandas as pd
import numpy as np
from typing import Dict, List
import random

class MonteCarloSimulator:
    def __init__(self, historical_data: pd.DataFrame):
        """
        historical_data: DataFrame with race results
        Must have: date, jyo_cd, race_no, boat_no, rank, tansho
        """
        self.data = historical_data
        self.races = self._prepare_races()

    def _prepare_races(self):
        """Group by race_id"""
        if 'race_id' not in self.data.columns:
            self.data['race_id'] = (
                self.data['date'].astype(str) + '_' +
                self.data['jyo_cd'].astype(str) + '_' +
                self.data['race_no'].astype(str)
            )
        return self.data.groupby('race_id')

    def simulate_strategy(self, strategy_filter: Dict, n_simulations: int = 10000, bet_amount: int = 100):
        """
        Run Monte Carlo simulation for a strategy.
        
        strategy_filter: dict with keys like 'jyo_cd', 'min_prob', etc.
        Returns: dict with mean_roi, ci_95, win_rate, total_profit
        """
        # Filter races matching strategy
        filtered_races = self._filter_races(strategy_filter)
        
        if len(filtered_races) < 10:
            return {
                'error': 'Not enough races matching strategy',
                'n_races': len(filtered_races)
            }
        
        results = []
        
        for _ in range(n_simulations):
            # Sample races (with replacement for bootstrap)
            sample_size = min(len(filtered_races), 100)  # Simulate 100 bets
            sampled = random.choices(filtered_races, k=sample_size)
            
            total_bet = bet_amount * sample_size
            total_return = 0
            wins = 0
            
            for race_data in sampled:
                # Assume we bet on boat with highest prob (simplified)
                # In real scenario, use actual prediction logic
                winner = race_data[race_data['rank'] == 1]
                if not winner.empty:
                    # Did we bet on winner? (Simplified: assume we bet on boat 1)
                    if winner.iloc[0]['boat_no'] == 1:
                        wins += 1
                        total_return += winner.iloc[0].get('tansho', 0)
            
            profit = total_return - total_bet
            roi = (total_return / total_bet * 100) if total_bet > 0 else 0
            
            results.append({
                'profit': profit,
                'roi': roi,
                'win_rate': wins / sample_size * 100
            })
        
        # Calculate statistics
        profits = [r['profit'] for r in results]
        rois = [r['roi'] for r in results]
        win_rates = [r['win_rate'] for r in results]
        
        return {
            'n_simulations': n_simulations,
            'n_races_available': len(filtered_races),
            'mean_profit': np.mean(profits),
            'mean_roi': np.mean(rois),
            'mean_win_rate': np.mean(win_rates),
            'ci_95_profit': (np.percentile(profits, 2.5), np.percentile(profits, 97.5)),
            'ci_95_roi': (np.percentile(rois, 2.5), np.percentile(rois, 97.5)),
            'probability_profitable': sum(1 for p in profits if p > 0) / n_simulations * 100
        }

    def _filter_races(self, strategy_filter: Dict) -> List:
        """Filter races matching strategy criteria"""
        matched = []
        
        for race_id, group in self.races:
            # Check jyo
            if 'jyo_cd' in strategy_filter:
                if group['jyo_cd'].iloc[0] != strategy_filter['jyo_cd']:
                    continue
            
            # Check wind
            if 'wind_min' in strategy_filter and 'wind_speed' in group.columns:
                ws = group['wind_speed'].iloc[0]
                if ws < strategy_filter.get('wind_min', 0):
                    continue
                if ws > strategy_filter.get('wind_max', 100):
                    continue
            
            matched.append(group)
        
        return matched

if __name__ == "__main__":
    # Test
    print("Monte Carlo Simulator Ready")
