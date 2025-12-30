"""Train ensemble models (LightGBM, XGBoost, CatBoost)"""
import pandas as pd
import numpy as np
import lightgbm as lgb
import xgboost as xgb
from catboost import CatBoostClassifier, Pool
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, accuracy_score
import os
import json

from src.features.preprocessing import preprocess, FEATURES, CAT_FEATURES
from src.utils.logger import logger

MODEL_DIR = "models"
DATA_PATH = "data/processed/race_data.csv"


def train_lightgbm(X_train, y_train, X_test, y_test, cat_features):
    """Train LightGBM model"""
    logger.info("Training LightGBM...")
    
    train_data = lgb.Dataset(X_train, label=y_train, categorical_feature=cat_features)
    test_data = lgb.Dataset(X_test, label=y_test, categorical_feature=cat_features, reference=train_data)
    
    params = {
        'objective': 'binary',
        'metric': 'auc',
        'boosting_type': 'gbdt',
        'num_leaves': 31,
        'learning_rate': 0.05,
        'feature_fraction': 0.8,
        'bagging_fraction': 0.8,
        'bagging_freq': 5,
        'verbose': -1,
        'seed': 42
    }
    
    model = lgb.train(
        params,
        train_data,
        valid_sets=[test_data],
        num_boost_round=500,
        callbacks=[lgb.early_stopping(50), lgb.log_evaluation(100)]
    )
    
    model.save_model(f"{MODEL_DIR}/lgbm_model.txt")
    
    preds = model.predict(X_test)
    auc = roc_auc_score(y_test, preds)
    logger.info(f"LightGBM AUC: {auc:.4f}")
    
    return model, auc


def train_xgboost(X_train, y_train, X_test, y_test):
    """Train XGBoost model"""
    logger.info("Training XGBoost...")
    
    dtrain = xgb.DMatrix(X_train, label=y_train)
    dtest = xgb.DMatrix(X_test, label=y_test)
    
    params = {
        'objective': 'binary:logistic',
        'eval_metric': 'auc',
        'max_depth': 6,
        'learning_rate': 0.05,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'seed': 42,
        'verbosity': 0
    }
    
    model = xgb.train(
        params,
        dtrain,
        num_boost_round=500,
        evals=[(dtest, 'eval')],
        early_stopping_rounds=50,
        verbose_eval=100
    )
    
    model.save_model(f"{MODEL_DIR}/xgb_model.json")
    
    preds = model.predict(dtest)
    auc = roc_auc_score(y_test, preds)
    logger.info(f"XGBoost AUC: {auc:.4f}")
    
    return model, auc


def train_catboost(X_train, y_train, X_test, y_test, cat_features):
    """Train CatBoost model"""
    logger.info("Training CatBoost...")
    
    # Get categorical feature indices
    cat_indices = [X_train.columns.get_loc(c) for c in cat_features if c in X_train.columns]
    
    model = CatBoostClassifier(
        iterations=500,
        learning_rate=0.05,
        depth=6,
        loss_function='Logloss',
        eval_metric='AUC',
        random_seed=42,
        verbose=100,
        early_stopping_rounds=50,
        cat_features=cat_indices
    )
    
    model.fit(
        X_train, y_train,
        eval_set=(X_test, y_test),
        use_best_model=True
    )
    
    model.save_model(f"{MODEL_DIR}/cat_model.cbm")
    
    preds = model.predict_proba(X_test)[:, 1]
    auc = roc_auc_score(y_test, preds)
    logger.info(f"CatBoost AUC: {auc:.4f}")
    
    return model, auc


def train_ensemble():
    """Train all ensemble models"""
    if not os.path.exists(DATA_PATH):
        logger.error("Data file not found.")
        return
    
    os.makedirs(MODEL_DIR, exist_ok=True)
    
    # Load and preprocess data
    df = pd.read_csv(DATA_PATH)
    logger.info(f"Loaded {len(df)} rows.")
    
    df = preprocess(df, is_training=True)
    logger.info(f"Post-preprocessing: {len(df)} rows.")
    
    X = df[FEATURES]
    y = df['target']
    
    # Date-based split
    unique_dates = sorted(df['date'].unique())
    train_dates = unique_dates[:-3]
    test_dates = unique_dates[-3:]
    
    train_idx = df['date'].isin(train_dates)
    test_idx = df['date'].isin(test_dates)
    
    X_train, y_train = X[train_idx], y[train_idx]
    X_test, y_test = X[test_idx], y[test_idx]
    
    logger.info(f"Train: {len(X_train)} rows, Test: {len(X_test)} rows")
    
    # Train models
    results = {}
    
    # LightGBM
    _, lgb_auc = train_lightgbm(X_train, y_train, X_test, y_test, CAT_FEATURES)
    results['lgb'] = lgb_auc
    
    # XGBoost (needs numeric features only for categorical)
    X_train_xgb = X_train.copy()
    X_test_xgb = X_test.copy()
    for col in CAT_FEATURES:
        if col in X_train_xgb.columns:
            X_train_xgb[col] = X_train_xgb[col].astype('category').cat.codes
            X_test_xgb[col] = X_test_xgb[col].astype('category').cat.codes
    
    _, xgb_auc = train_xgboost(X_train_xgb, y_train, X_test_xgb, y_test)
    results['xgb'] = xgb_auc
    
    # CatBoost
    _, cat_auc = train_catboost(X_train, y_train, X_test, y_test, CAT_FEATURES)
    results['cat'] = cat_auc
    
    # Calculate optimal weights based on AUC
    total_auc = sum(results.values())
    weights = {k: v / total_auc for k, v in results.items()}
    
    # Save weights
    with open(f"{MODEL_DIR}/ensemble_weights.json", 'w') as f:
        json.dump({
            'weights': weights,
            'auc_scores': results
        }, f, indent=2)
    
    logger.info(f"Ensemble trained. Weights: {weights}")
    logger.info(f"AUC scores: {results}")
    
    return results


if __name__ == "__main__":
    train_ensemble()
