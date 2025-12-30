"""Tests for Betting Optimization"""
import pytest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestKellyCalculation:
    """Test Kelly criterion calculations"""
    
    def test_kelly_positive_ev(self):
        from src.portfolio.kelly import calculate_kelly_fraction
        
        # Probability 50%, Odds 3.0 -> Kelly = (2*0.5 - 0.5) / 2 = 0.25
        # With half-Kelly default: 0.25 * 0.5 = 0.125
        fraction = calculate_kelly_fraction(0.5, 3.0)
        assert 0.1 <= fraction <= 0.15  # Half-Kelly applied
    
    def test_kelly_negative_ev(self):
        from src.portfolio.kelly import calculate_kelly_fraction
        
        # Probability 20%, Odds 3.0 -> EV = 0.6, Kelly should be 0 or negative
        fraction = calculate_kelly_fraction(0.2, 3.0)
        assert fraction <= 0
    
    def test_kelly_edge_cases(self):
        from src.portfolio.kelly import calculate_kelly_fraction
        
        # Zero probability
        assert calculate_kelly_fraction(0, 5.0) <= 0
        
        # 100% probability (should return high fraction but capped)
        fraction = calculate_kelly_fraction(1.0, 2.0)
        assert fraction > 0


class TestFormationGeneration:
    """Test betting formation generation"""
    
    def test_box_combos(self):
        from src.api.routers.betting import _generate_box_combos
        
        combos = _generate_box_combos([1, 2, 3])
        
        # 3 boats box = 3! = 6 combinations
        assert len(combos) == 6
        assert "1-2-3" in combos
        assert "3-2-1" in combos
    
    def test_formation_combos(self):
        from src.api.routers.betting import _generate_formation_combos
        
        combos = _generate_formation_combos(1, [2, 3, 4])
        
        # Head fixed, 2 followers from 3 = 3 * 2 = 6 combinations
        assert len(combos) == 6
        assert all(c.startswith("1-") for c in combos)
    
    def test_flow_combos(self):
        from src.api.routers.betting import _generate_flow_combos
        
        combos = _generate_flow_combos([1, 2], [3, 4])
        
        # 1-2 fixed, 2 followers
        assert len(combos) == 2
        assert "1-2-3" in combos
        assert "1-2-4" in combos


class TestPortfolioLedger:
    """Test portfolio ledger"""
    
    def test_ledger_initialization(self):
        from src.portfolio.ledger import PortfolioLedger
        
        ledger = PortfolioLedger()
        assert ledger is not None
    
    def test_get_summary(self):
        from src.portfolio.ledger import PortfolioLedger
        
        ledger = PortfolioLedger()
        summary = ledger.get_summary()
        
        assert "balance" in summary
        assert "roi" in summary
        assert "win_rate" in summary
        assert "transactions" in summary


class TestMonteCarloSimulation:
    """Test Monte Carlo simulation"""
    
    def test_simulator_initialization(self):
        import pandas as pd
        from src.simulation.monte_carlo import MonteCarloSimulator
        
        df = pd.DataFrame({
            'date': ['20240101'] * 6,
            'jyo_cd': ['02'] * 6,
            'race_no': [1] * 6,
            'boat_no': [1, 2, 3, 4, 5, 6],
            'rank': [1, 2, 3, 4, 5, 6],
        })
        
        simulator = MonteCarloSimulator(df)
        assert simulator is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
