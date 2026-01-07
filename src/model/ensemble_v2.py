"""Enhanced Ensemble Model with XGBoost, LightGBM, CatBoost, Neural Network"""
import pandas as pd
import numpy as np
import joblib
import json
from typing import Dict, List, Tuple
import logging
from datetime import datetime

# ML imports
import lightgbm as lgb
import catboost as cb
import xgboost as xgb
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, accuracy_score

# Custom imports
from .neural_network import NeuralNetworkPredictor
from .enhanced_features import add_enhanced_features
from .train_model import FEATURES, CAT_FEATURES

class EnhancedEnsemble:
    """Enhanced ensemble with multiple models"""
    def __init__(self):
        self.models = {
            'lightgbm': None,
            'catboost': None,
            'xgboost': None,
            'random_forest': None,
            'neural_network': None
        }
        self.weights = {
            'lightgbm': 0.3,
            'catboost': 0.25,
            'xgboost': 0.2,
            'random_forest': 0.1,
            'neural_network': 0.15
        }
        self.feature_names = FEATURES
        self.is_fitted = False
        self.training_stats = {}
        
    def fit(self, X: pd.DataFrame, y: pd.Series) -> None:
        """Fit all models in the ensemble"""
        print(f"Training Enhanced Ensemble with {len(X)} samples")
        
        # 拡張特徴量を追加
        X = add_enhanced_features(X)
        
        # 特徴量名の更新
        self.feature_names = [col for col in X.columns if col != 'target']
        
        # 各モデルを学習
        self._train_lightgbm(X, y)
        self._train_catboost(X, y)
        self._train_xgboost(X, y)
        self._train_random_forest(X, y)
        self._train_neural_network(X, y)
        
        # 重みの最適化
        self._optimize_weights(X, y)
        self.is_fitted = True
        
        print("Enhanced Ensemble training completed")
    
    def _train_lightgbm(self, X: pd.DataFrame, y: pd.Series) -> None:
        """Train LightGBM model"""
        params = {
            'objective': 'binary',
            'metric': 'auc',
            'learning_rate': 0.05,
            'num_leaves': 63,
            'feature_fraction': 0.8,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'verbose': -1
        }
        
        train_data = lgb.Dataset(X, label=y, categorical_feature=CAT_FEATURES)
        self.models['lightgbm'] = lgb.train(
            params, train_data, num_boost_round=1000,
            callbacks=[lgb.early_stopping(stopping_rounds=50), lgb.log_evaluation(0)]
        )
        
        self.training_stats['lightgbm_auc'] = self._evaluate_model('lightgbm', X, y)
    
    def _train_catboost(self, X: pd.DataFrame, y: pd.Series) -> None:
        """Train CatBoost model"""
        cat_features_idx = [X.columns.get_loc(col) for col in CAT_FEATURES if col in X.columns]
        
        params = {
            'iterations': 1000,
            'learning_rate': 0.05,
            'depth': 8,
            'l2_leaf_reg': 3,
            'loss_function': 'Logloss',
            'eval_metric': 'AUC',
            'random_seed': 42,
            'verbose': False
        }
        
        self.models['catboost'] = cb.CatBoostClassifier(**params)
        self.models['catboost'].fit(X, y, cat_features=cat_features_idx, verbose=False)
        
        self.training_stats['catboost_auc'] = self._evaluate_model('catboost', X, y)
    
    def _train_xgboost(self, X: pd.DataFrame, y: pd.Series) -> None:
        """Train XGBoost model"""
        params = {
            'objective': 'binary:logistic',
            'eval_metric': 'auc',
            'max_depth': 8,
            'eta': 0.05,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'random_state': 42
        }
        
        dtrain = xgb.DMatrix(X, label=y)
        self.models['xgboost'] = xgb.train(params, dtrain, num_boost_round=1000, verbose_eval=False)
        
        self.training_stats['xgboost_auc'] = self._evaluate_model('xgboost', X, y)
    
    def _train_random_forest(self, X: pd.DataFrame, y: pd.Series) -> None:
        """Train Random Forest model"""
        self.models['random_forest'] = RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=10,
            random_state=42
        )
        self.models['random_forest'].fit(X, y)
        
        self.training_stats['random_forest_auc'] = self._evaluate_model('random_forest', X, y)
    
    def _train_neural_network(self, X: pd.DataFrame, y: pd.Series) -> None:
        """Train Neural Network model"""
        self.models['neural_network'] = NeuralNetworkPredictor()
        train_df = X.copy()
        train_df['target'] = y
        
        stats = self.models['neural_network'].train(train_df, epochs=100, batch_size=512)
        self.training_stats['neural_network_auc'] = stats['best_val_auc']
    
    def _evaluate_model(self, model_name: str, X: pd.DataFrame, y: pd.Series) -> float:
        """Evaluate single model"""
        if model_name == 'lightgbm':
            pred = self.models[model_name].predict(X)
        elif model_name == 'neural_network':
            pred = self.models[model_name].predict_proba(X)
        else:
            pred = self.models[model_name].predict_proba(X)[:, 1]
        
        return roc_auc_score(y, pred)
    
    def _optimize_weights(self, X: pd.DataFrame, y: pd.Series) -> None:
        """Optimize ensemble weights based on performance"""
        # 各モデルの性能に基づいて重みを調整
        performance_scores = {}
        total_score = 0
        
        for model_name in self.models.keys():
            score = self.training_stats.get(f'{model_name}_auc', 0.5)
            performance_scores[model_name] = score
            total_score += score
        
        # 性能に比例して重みを設定
        for model_name in self.weights.keys():
            score = performance_scores.get(model_name, 0.5)
            self.weights[model_name] = score / total_score if total_score > 0 else 0.2
        
        print("Optimized weights:", self.weights)
    
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Make ensemble predictions"""
        if not self.is_fitted:
            raise ValueError("Ensemble not fitted yet")
        
        # 拡張特徴量を追加
        X = add_enhanced_features(X)
        
        predictions = np.zeros(len(X))
        
        for model_name, weight in self.weights.items():
            if model_name == 'lightgbm':
                pred = self.models[model_name].predict(X)
            elif model_name == 'neural_network':
                pred = self.models[model_name].predict_proba(X)
            elif model_name == 'xgboost':
                dtest = xgb.DMatrix(X)
                pred = self.models[model_name].predict(dtest)
            else:  # catboost, random_forest
                pred = self.models[model_name].predict_proba(X)[:, 1]
            
            # 確率にクリップ
            pred = np.clip(pred, 0.01, 0.99)
            predictions += weight * pred
        
        return predictions
    
    def predict_proba(self, X: pd.DataFrame) -> np.ndarray:
        """Predict with probabilities (same as predict)"""
        predictions = self.predict(X)
        return np.column_stack([1-predictions, predictions])
    
    def save_models(self, path: str) -> None:
        """Save all models"""
        import os
        os.makedirs(path, exist_ok=True)
        
        # Save base models
        for name, model in self.models.items():
            if name in ['catboost', 'random_forest']:
                joblib.dump(model, f'{path}/{name}.joblib')
            elif name == 'lightgbm':
                model.save_model(f'{path}/{name}.txt')
            elif name == 'xgboost':
                model.save_model(f'{path}/{name}.json')
            elif name == 'neural_network':
                model.save_model(f'{path}/{name}.pth')
        
        # Save metadata
        metadata = {
            'weights': self.weights,
            'feature_names': self.feature_names.tolist() if hasattr(self.feature_names, 'tolist') else self.feature_names,
            'training_stats': self.training_stats,
            'is_fitted': self.is_fitted,
            'saved_at': datetime.now().isoformat()
        }
        
        with open(f'{path}/ensemble_metadata.json', 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def load_models(self, path: str) -> None:
        """Load all models"""
        import os
        if not os.path.exists(path):
            raise FileNotFoundError(f"Path {path} does not exist")
        
        # Load metadata
        with open(f'{path}/ensemble_metadata.json', 'r') as f:
            metadata = json.load(f)
        
        self.weights = metadata['weights']
        self.feature_names = metadata['feature_names']
        self.training_stats = metadata['training_stats']
        self.is_fitted = metadata['is_fitted']
        
        # Load models
        self.models['lightgbm'] = lgb.Booster(model_file=f'{path}/lightgbm.txt')
        self.models['catboost'] = joblib.load(f'{path}/catboost.joblib')
        self.models['random_forest'] = joblib.load(f'{path}/random_forest.joblib')
        
        # XGBoost
        if os.path.exists(f'{path}/xgboost.json'):
            self.models['xgboost'] = xgb.Booster()
            self.models['xgboost'].load_model(f'{path}/xgboost.json')
        
        # Neural Network
        if os.path.exists(f'{path}/neural_network.pth'):
            self.models['neural_network'] = NeuralNetworkPredictor()
            self.models['neural_network'].load_model(f'{path}/neural_network.pth')
        
        print(f"Loaded Enhanced Ensemble from {path}")