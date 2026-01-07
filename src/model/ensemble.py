"""Ensemble Predictor - Combines LightGBM, XGBoost, CatBoost"""
import pandas as pd
import numpy as np
import lightgbm as lgb
import xgboost as xgb
from catboost import CatBoostClassifier
import os
import json

from src.features.preprocessing import FEATURES, CAT_FEATURES
from src.utils.logger import logger

MODEL_DIR = "models"


class EnsemblePredictor:
    """Ensemble model combining multiple gradient boosting models"""
    
    def __init__(self):
        self.models = {}
        self.weights = {"lgb": 0.33, "xgb": 0.33, "cat": 0.34}
        self.loaded = False
        self.cat_feature_indices = []

    def load_models(self):
        """Load all available models"""
        try:
            # Load weights if available
            weights_path = f"{MODEL_DIR}/ensemble_weights.json"
            if os.path.exists(weights_path):
                with open(weights_path, 'r') as f:
                    data = json.load(f)
                    self.weights = data.get('weights', self.weights)
                logger.info(f"Loaded ensemble weights: {self.weights}")
            
            # LightGBM
            lgb_path = f"{MODEL_DIR}/lgbm_model.txt"
            if os.path.exists(lgb_path):
                self.models["lgb"] = lgb.Booster(model_file=lgb_path)
                logger.info("Loaded LightGBM model")
            
            # XGBoost
            xgb_path = f"{MODEL_DIR}/xgb_model.json"
            if os.path.exists(xgb_path):
                self.models["xgb"] = xgb.Booster()
                self.models["xgb"].load_model(xgb_path)
                logger.info("Loaded XGBoost model")
            
            # CatBoost
            cat_path = f"{MODEL_DIR}/cat_model.cbm"
            if os.path.exists(cat_path):
                self.models["cat"] = CatBoostClassifier()
                self.models["cat"].load_model(cat_path)
                logger.info("Loaded CatBoost model")
            
            self.loaded = True
            logger.info(f"Ensemble loaded: {list(self.models.keys())}")
            
        except Exception as e:
            logger.error(f"Error loading ensemble: {e}")
            raise

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Make ensemble prediction"""
        if not self.loaded:
            self.load_models()
        
        if not self.models:
            logger.warning("No models loaded, returning zeros")
            return np.zeros(len(X))
        
        predictions = {}
        
        # LightGBM prediction
        if "lgb" in self.models:
            try:
                predictions["lgb"] = self.models["lgb"].predict(X[FEATURES])
            except Exception as e:
                logger.warning(f"LightGBM prediction failed: {e}")
        
        # XGBoost prediction (needs encoded categorical)
        if "xgb" in self.models:
            try:
                X_xgb = X[FEATURES].copy()
                for col in CAT_FEATURES:
                    if col in X_xgb.columns:
                        X_xgb[col] = X_xgb[col].astype('category').cat.codes
                dmatrix = xgb.DMatrix(X_xgb)
                predictions["xgb"] = self.models["xgb"].predict(dmatrix)
            except Exception as e:
                logger.warning(f"XGBoost prediction failed: {e}")
        
        # CatBoost prediction
        if "cat" in self.models:
            try:
                predictions["cat"] = self.models["cat"].predict_proba(X[FEATURES])[:, 1]
            except Exception as e:
                logger.warning(f"CatBoost prediction failed: {e}")
        
        if not predictions:
            return np.zeros(len(X))
        
        # Weighted average
        ensemble_pred = np.zeros(len(X))
        total_weight = 0
        
        for name, pred in predictions.items():
            weight = self.weights.get(name, 0.33)
            ensemble_pred += weight * pred
            total_weight += weight
        
        if total_weight > 0:
            ensemble_pred /= total_weight
        
        return ensemble_pred

    def predict_with_details(self, X: pd.DataFrame) -> dict:
        """Make prediction with individual model scores"""
        if not self.loaded:
            self.load_models()
        
        result = {
            "ensemble": None,
            "models": {},
            "weights": self.weights
        }
        
        predictions = {}
        
        if "lgb" in self.models:
            try:
                predictions["lgb"] = self.models["lgb"].predict(X[FEATURES])
                result["models"]["lgb"] = predictions["lgb"].tolist()
            except:
                pass
        
        if "xgb" in self.models:
            try:
                X_xgb = X[FEATURES].copy()
                for col in CAT_FEATURES:
                    if col in X_xgb.columns:
                        X_xgb[col] = X_xgb[col].astype('category').cat.codes
                dmatrix = xgb.DMatrix(X_xgb)
                predictions["xgb"] = self.models["xgb"].predict(dmatrix)
                result["models"]["xgb"] = predictions["xgb"].tolist()
            except:
                pass
        
        if "cat" in self.models:
            try:
                predictions["cat"] = self.models["cat"].predict_proba(X[FEATURES])[:, 1]
                result["models"]["cat"] = predictions["cat"].tolist()
            except:
                pass
        
        # Calculate ensemble
        if predictions:
            ensemble_pred = np.zeros(len(X))
            total_weight = 0
            for name, pred in predictions.items():
                weight = self.weights.get(name, 0.33)
                ensemble_pred += weight * pred
                total_weight += weight
            if total_weight > 0:
                ensemble_pred /= total_weight
            result["ensemble"] = ensemble_pred.tolist()
        
        return result


# Singleton instance
_ensemble = None

def get_ensemble() -> EnsemblePredictor:
    """Get singleton ensemble predictor"""
    global _ensemble
    if _ensemble is None:
        _ensemble = EnsemblePredictor()
        _ensemble.load_models()
    return _ensemble
