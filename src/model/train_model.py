import pandas as pd
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score
import matplotlib.pyplot as plt
import os
import json
from src.features.preprocessing import preprocess, FEATURES, CAT_FEATURES

# Removed local preprocess - using src.features.preprocessing.preprocess

def train_model():
    data_path = "data/processed/race_data.csv"
    if not os.path.exists(data_path):
        print("Data file not found.")
        return

    df = pd.read_csv(data_path)
    print(f"Loaded {len(df)} rows.")
    
    df = preprocess(df, is_training=True)
    print(f"Post-preprocessing: {len(df)} rows.")
    
    # Features and Labels
    X = df[FEATURES]
    y = df['target']
    
    # Date-based split
    unique_dates = sorted(df['date'].unique())
    train_dates = unique_dates[:-3] # All but last 3 days
    test_dates = unique_dates[-3:]  # Last 3 days
    
    train_idx = df['date'].isin(train_dates)
    test_idx = df['date'].isin(test_dates)
    
    X_train, y_train = X[train_idx], y[train_idx]
    X_test, y_test = X[test_idx], y[test_idx]
    
    print(f"Train on {len(train_dates)} days ({len(X_train)} rows), Test on {len(test_dates)} days ({len(X_test)} rows).")
    
    # LightGBM Dataset
    train_data = lgb.Dataset(X_train, label=y_train, categorical_feature=CAT_FEATURES)
    test_data = lgb.Dataset(X_test, label=y_test, categorical_feature=CAT_FEATURES, reference=train_data)
    
    # Parameters for Binary Classification
    # Load optimized params if available
    params_path = "config/model_params.json"
    if os.path.exists(params_path):
        print(f"Loading optimized parameters from {params_path}")
        with open(params_path, 'r') as f:
            params = json.load(f)
    else:
        print("Using default parameters")
        params = {
            'objective': 'binary',
            'metric': 'auc',
            'boosting_type': 'gbdt',
            'learning_rate': 0.05,
            'num_leaves': 31,
            'feature_fraction': 0.8,
            'bagging_fraction': 0.8,
            'bagging_freq': 5,
            'verbose': -1
        }
    
    # Train
    model = lgb.train(
        params, 
        train_data, 
        valid_sets=[test_data], 
        num_boost_round=1000,
        callbacks=[lgb.early_stopping(stopping_rounds=50), lgb.log_evaluation(50)]
    )
    
    # Evaluate
    y_pred_prob = model.predict(X_test)
    y_pred_binary = (y_pred_prob > 0.5).astype(int)
    
    from sklearn.metrics import roc_auc_score, accuracy_score
    auc = roc_auc_score(y_test, y_pred_prob)
    acc = accuracy_score(y_test, y_pred_binary)
    
    print(f"Test AUC: {auc:.4f}")
    print(f"Test Accuracy: {acc:.4f}")

    # Evaluate Hit Rate (Rank 1)
    temp_df = X_test.copy()
    temp_df['target'] = y_test
    temp_df['pred'] = y_pred_prob
    temp_df['date'] = df.loc[X_test.index, 'date']
    temp_df['race_no'] = df.loc[X_test.index, 'race_no']
    
    hits = 0
    total_races = 0
    for _, group in temp_df.groupby(['date', 'jyo_cd', 'race_no']):
        top_pred = group.sort_values('pred', ascending=False).iloc[0]
        if top_pred['target'] == 1:
            hits += 1
        total_races += 1
    
    hit_rate = hits / total_races if total_races > 0 else 0
    print(f"Test Hit Rate (Rank 1): {hit_rate:.4f} ({hits}/{total_races})")
    
    # Feature Importance
    importance = model.feature_importance(importance_type='gain')
    feature_names = model.feature_name()
    
    print("\nFeature Importance (Gain):")
    for name, imp in zip(feature_names, importance):
        print(f"{name}: {imp:.4f}")
    
    # Save Model
    os.makedirs("models", exist_ok=True)
    model.save_model("models/lgbm_model.txt")
    print("\nModel saved to models/lgbm_model.txt")

if __name__ == "__main__":
    train_model()
