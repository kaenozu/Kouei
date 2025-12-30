import pandas as pd
import numpy as np
import lightgbm as lgb
import xgboost as xgb
import catboost as cb
import os
import joblib
import json
from src.features.preprocessing import preprocess, FEATURES, CAT_FEATURES

MODEL_DIR = "models"
DATA_PATH = "data/processed/race_data.csv"

class EnsemblePredictor:
    def __init__(self):
        self.models = {}
        self.weights = {"lgb": 0.4, "xgb": 0.3, "cat": 0.3}
        self.loaded = False

    def load_models(self):
        try:
            # LightGBM
            if os.path.exists(f"{MODEL_DIR}/lgbm_model.txt"):
                self.models["lgb"] = lgb.Booster(model_file=f"{MODEL_DIR}/lgbm_model.txt")
            
            # XGBoost
            if os.path.exists(f"{MODEL_DIR}/xgb_model.json"):
                self.models["xgb"] = xgb.Booster()
                self.models["xgb"].load_model(f"{MODEL_DIR}/xgb_model.json")
            
            # CatBoost
            if os.path.exists(f"{MODEL_DIR}/cat_model.cbm"):
                self.models["cat"] = cb.CatBoostClassifier()
                self.models["cat"].load_model(f"{MODEL_DIR}/cat_model.cbm")
            
            self.loaded = True
            print(f"Ensemble loaded: {list(self.models.keys())}")
        except Exception as e:
            print(f"Error loading ensemble: {e}")

    def predict(self, X, pred_contrib=False):
        if not self.loaded:
            self.load_models()
        
        if not self.models:
            return np.zeros(len(X))

        # LightGBM Prediction
        preds = []
        if "lgb" in self.models:
            p = self.models["lgb"].predict(X)
            preds.append(p * self.weights["lgb"])
            
            # For feature importance/contrib, we typically just use LGB's as logical proxy
            # efficiently calculating exact SHAP for ensemble is expensive realtime
            if pred_contrib:
                # Return LGB contribs as representative
                return self.models["lgb"].predict(X, pred_contrib=True)

        # XGBoost Prediction
        if "xgb" in self.models:
            # XGB requires DMatrix
            dtest = xgb.DMatrix(X)
            p = self.models["xgb"].predict(dtest)
            preds.append(p * self.weights["xgb"])

        # CatBoost Prediction
        if "cat" in self.models:
            p = self.models["cat"].predict_proba(X)[:, 1] # Class 1 prob
            preds.append(p * self.weights["cat"])

        # Normalize logic: Sum of weights used
        used_weights = sum(self.weights[k] for k in self.models.keys())
        final_pred = sum(preds) / used_weights if used_weights > 0 else np.zeros(len(X))
        
        return final_pred

def train_ensemble():
    if not os.path.exists(DATA_PATH):
        print("Data not found.")
        return

    print("Loading data for Ensemble Training...")
    df = pd.read_csv(DATA_PATH)
    
    # Preprocess
    df = preprocess(df, is_training=True)
    X = df[FEATURES]
    y = df['target'] # Ensure target column creation in preprocessing or here? 
    # Note: 'target' is usually created in train_model.py logic. 
    # Let's ensure preprocess returns df with 'target' if it exists in raw data (it usually is 'rank' checks)
    
    # Wait, preprocess usually adds features. Target logic (rank==1 -> 1) is often external.
    # Let's add it here if missing.
    if 'target' not in df.columns:
         df['target'] = (df['rank'] == 1).astype(int)
         y = df['target']
    
    # Split
    # Simple standardized split for all
    dates = sorted(df['date'].unique())
    train_dates = dates[:-5] # Last 5 days validation
    val_dates = dates[-5:]
    
    train_mask = df['date'].isin(train_dates)
    val_mask = df['date'].isin(val_dates)
    
    X_train, y_train = X[train_mask], y[train_mask]
    X_val, y_val = X[val_mask], y[val_mask]
    
    os.makedirs(MODEL_DIR, exist_ok=True)
    
    # 1. Train LightGBM
    print("Training LightGBM...")
    train_data_lgb = lgb.Dataset(X_train, label=y_train, categorical_feature=CAT_FEATURES)
    val_data_lgb = lgb.Dataset(X_val, label=y_val, reference=train_data_lgb)
    
    lgb_params = {
        'objective': 'binary', 'metric': 'auc', 
        'learning_rate': 0.05, 'num_leaves': 31, 'verbose': -1
    }
    # Load optuna params if exist
    if os.path.exists("config/model_params.json"):
        with open("config/model_params.json", "r") as f:
            lgb_params.update(json.load(f))
            
    model_lgb = lgb.train(lgb_params, train_data_lgb, valid_sets=[val_data_lgb], 
                          callbacks=[lgb.early_stopping(stopping_rounds=20), lgb.log_evaluation(0)])
    model_lgb.save_model(f"{MODEL_DIR}/lgbm_model.txt")
    
    # 2. Train XGBoost
    print("Training XGBoost...")
    # XGB handles NaN naturally, but categorical needs handling or default to numeric
    # For simplicity, treat all as numeric for XGB (preprocessing usually encodes cats)
    dtrain_xgb = xgb.DMatrix(X_train, label=y_train, enable_categorical=True)
    dval_xgb = xgb.DMatrix(X_val, label=y_val, enable_categorical=True)
    
    xgb_params = {
        'objective': 'binary:logistic', 'eval_metric': 'auc',
        'learning_rate': 0.05, 'max_depth': 6
    }
    model_xgb = xgb.train(xgb_params, dtrain_xgb, num_boost_round=1000, 
                          evals=[(dval_xgb, "val")], early_stopping_rounds=20, verbose_eval=False)
    model_xgb.save_model(f"{MODEL_DIR}/xgb_model.json")
    
    # 3. Train CatBoost
    print("Training CatBoost...")
    # CatBoost handles NaNs and Cats great
    # Need to specify cat features indices (names in X)
    cat_feats_indices = [c for c in CAT_FEATURES if c in X.columns]
    
    model_cat = cb.CatBoostClassifier(
        iterations=1000, learning_rate=0.05, depth=6, eval_metric='AUC',
        verbose=0, early_stopping_rounds=20, allow_writing_files=False
    )
    model_cat.fit(X_train, y_train, cat_features=cat_feats_indices, eval_set=(X_val, y_val))
    model_cat.save_model(f"{MODEL_DIR}/cat_model.cbm")
    
    print("Ensemble Training Complete.")

if __name__ == "__main__":
    train_ensemble()
