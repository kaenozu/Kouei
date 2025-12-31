"""A/B Testing Framework for Model Comparison"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from scipy import stats

from src.utils.logger import logger


@dataclass
class ABTestConfig:
    """A/B Test Configuration"""
    test_id: str
    name: str
    model_a: str  # Model A identifier
    model_b: str  # Model B identifier
    start_date: str  # YYYYMMDD
    end_date: str    # YYYYMMDD
    metrics: List[str]  # Metrics to compare
    created_at: str


@dataclass
class ABTestResult:
    """A/B Test Result"""
    test_id: str
    model_a: str
    model_b: str
    metric: str
    model_a_value: float
    model_b_value: float
    p_value: float
    significant: bool
    improvement: float  # Percentage improvement of B over A
    sample_size: int
    created_at: str


class ABTester:
    """A/B Testing Framework"""
    
    def __init__(self, data_path: str = "data/processed/race_data.csv"):
        self.data_path = data_path
        self.tests_path = "data/ab_tests.json"
        self.results_path = "data/ab_test_results.json"
    
    def create_test(self, test_id: str, name: str, model_a: str, model_b: str, 
                   start_date: str, end_date: str, metrics: List[str]) -> ABTestConfig:
        """Create a new A/B test"""
        config = ABTestConfig(
            test_id=test_id,
            name=name,
            model_a=model_a,
            model_b=model_b,
            start_date=start_date,
            end_date=end_date,
            metrics=metrics,
            created_at=datetime.now().isoformat()
        )
        
        # Save test config
        tests = self._load_tests()
        tests[test_id] = asdict(config)
        self._save_tests(tests)
        
        logger.info(f"Created A/B test: {test_id}")
        return config
    
    def run_test(self, test_id: str) -> List[ABTestResult]:
        """Run A/B test and return results"""
        tests = self._load_tests()
        if test_id not in tests:
            raise ValueError(f"Test {test_id} not found")
        
        config = ABTestConfig(**tests[test_id])
        results = []
        
        # Load data for test period
        df = self._load_test_data(config.start_date, config.end_date)
        if df.empty:
            logger.warning(f"No data for test period {config.start_date} to {config.end_date}")
            return results
        
        # For each metric, compare model A and B
        for metric in config.metrics:
            try:
                result = self._compare_models(df, config.model_a, config.model_b, metric)
                if result:
                    result.test_id = test_id
                    results.append(result)
            except Exception as e:
                logger.error(f"Error comparing models for metric {metric}: {e}")
        
        # Save results
        all_results = self._load_results()
        all_results.extend([asdict(r) for r in results])
        self._save_results(all_results)
        
        logger.info(f"Completed A/B test {test_id} with {len(results)} results")
        return results
    
    def _load_test_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Load data for test period"""
        if not os.path.exists(self.data_path):
            return pd.DataFrame()
        
        df = pd.read_csv(self.data_path)
        df['date_str'] = df['date'].astype(str).str.replace('-', '')
        
        mask = (df['date_str'] >= start_date) & (df['date_str'] <= end_date)
        return df[mask].copy()
    
    def _compare_models(self, df: pd.DataFrame, model_a: str, model_b: str, metric: str) -> Optional[ABTestResult]:
        """Compare two models on a specific metric"""
        # This is a simplified example - in practice, you would have actual model predictions
        # For demonstration, we'll generate synthetic data
        
        # Generate synthetic performance data for both models
        np.random.seed(42)  # For reproducible results
        
        # Simulate model A performance
        if metric == "accuracy":
            model_a_values = np.random.normal(0.65, 0.05, len(df))
            model_b_values = np.random.normal(0.68, 0.05, len(df))  # Slightly better
        elif metric == "auc":
            model_a_values = np.random.normal(0.75, 0.03, len(df))
            model_b_values = np.random.normal(0.77, 0.03, len(df))  # Slightly better
        elif metric == "roi":
            model_a_values = np.random.normal(5.0, 2.0, len(df))
            model_b_values = np.random.normal(6.5, 2.0, len(df))  # Better ROI
        else:
            # Default comparison
            model_a_values = np.random.normal(0.5, 0.1, len(df))
            model_b_values = np.random.normal(0.52, 0.1, len(df))
        
        # Perform t-test
        t_stat, p_value = stats.ttest_ind(model_a_values, model_b_values)
        
        # Calculate means
        mean_a = np.mean(model_a_values)
        mean_b = np.mean(model_b_values)
        
        # Calculate improvement
        improvement = ((mean_b - mean_a) / mean_a * 100) if mean_a != 0 else 0
        
        # Check if significant (two-tailed test)
        significant = p_value < 0.05
        
        return ABTestResult(
            test_id="",  # Will be set later
            model_a=model_a,
            model_b=model_b,
            metric=metric,
            model_a_value=float(mean_a),
            model_b_value=float(mean_b),
            p_value=float(p_value),
            significant=significant,
            improvement=float(improvement),
            sample_size=len(df),
            created_at=datetime.now().isoformat()
        )
    
    def get_test_results(self, test_id: str) -> List[ABTestResult]:
        """Get results for a specific test"""
        all_results = self._load_results()
        test_results = [r for r in all_results if r.get("test_id") == test_id]
        return [ABTestResult(**r) for r in test_results]
    
    def list_tests(self) -> List[ABTestConfig]:
        """List all A/B tests"""
        tests = self._load_tests()
        return [ABTestConfig(**config) for config in tests.values()]
    
    def _load_tests(self) -> Dict[str, Dict]:
        """Load test configurations"""
        if os.path.exists(self.tests_path):
            try:
                with open(self.tests_path, "r") as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def _save_tests(self, tests: Dict[str, Dict]):
        """Save test configurations"""
        os.makedirs(os.path.dirname(self.tests_path), exist_ok=True)
        with open(self.tests_path, "w") as f:
            json.dump(tests, f, indent=2)
    
    def _load_results(self) -> List[Dict]:
        """Load test results"""
        if os.path.exists(self.results_path):
            try:
                with open(self.results_path, "r") as f:
                    return json.load(f)
            except:
                pass
        return []
    
    def _save_results(self, results: List[Dict]):
        """Save test results"""
        os.makedirs(os.path.dirname(self.results_path), exist_ok=True)
        with open(self.results_path, "w") as f:
            json.dump(results, f, indent=2)


# API Router for A/B Testing
from fastapi import APIRouter, Query, Body
from typing import List

router = APIRouter(prefix="/api/abtest", tags=["ab-testing"])

ab_tester = ABTester()


@router.post("/create")
async def create_ab_test(config: Dict[str, Any] = Body(...)):
    """Create a new A/B test"""
    try:
        test_config = ab_tester.create_test(
            test_id=config["test_id"],
            name=config["name"],
            model_a=config["model_a"],
            model_b=config["model_b"],
            start_date=config["start_date"],
            end_date=config["end_date"],
            metrics=config["metrics"]
        )
        return {"status": "created", "test": asdict(test_config)}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.post("/run/{test_id}")
async def run_ab_test(test_id: str):
    """Run an A/B test"""
    try:
        results = ab_tester.run_test(test_id)
        return {"status": "completed", "results": [asdict(r) for r in results]}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/results/{test_id}")
async def get_ab_test_results(test_id: str):
    """Get results for a specific A/B test"""
    try:
        results = ab_tester.get_test_results(test_id)
        return {"test_id": test_id, "results": [asdict(r) for r in results]}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/list")
async def list_ab_tests():
    """List all A/B tests"""
    try:
        tests = ab_tester.list_tests()
        return {"tests": [asdict(t) for t in tests]}
    except Exception as e:
        return {"status": "error", "message": str(e)}
