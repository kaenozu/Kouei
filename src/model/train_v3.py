"""Enhanced Model Training Script V3 - Full retraining with all features"""
import pandas as pd
import numpy as np
import lightgbm as lgb
import xgboost as xgb
from catboost import CatBoostClassifier
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import roc_auc_score, accuracy_score, log_loss
import os
import json
from datetime import datetime
import joblib

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.features.preprocessing import preprocess, FEATURES, FEATURES_V2, CAT_FEATURES
from src.api.dependencies import get_dataframe


def add_v3_features(df):
    """Add V3 enhanced features for better prediction"""
    df = df.copy()
    
    # 1. Recent form features (using rolling windows)
    if 'racer_id' in df.columns and 'rank' in df.columns:
        df['rank_num'] = pd.to_numeric(df['rank'], errors='coerce')
        
        # Group by racer and calculate rolling stats
        df = df.sort_values(['date', 'jyo_cd', 'race_no', 'boat_no'])
        
        for racer_id in df['racer_id'].unique():
            mask = df['racer_id'] == racer_id
            racer_data = df.loc[mask, 'rank_num']
            
            # Rolling average rank (last 6 races)
            df.loc[mask, 'recent_avg_rank'] = racer_data.rolling(6, min_periods=1).mean().shift(1).fillna(3.5)
            
            # Rolling win rate (last 12 races)
            df.loc[mask, 'recent_win_rate'] = (racer_data == 1).rolling(12, min_periods=1).mean().shift(1).fillna(0.167)
            
            # Rolling rentai rate (1st or 2nd)
            df.loc[mask, 'recent_rentai_rate'] = (racer_data <= 2).rolling(12, min_periods=1).mean().shift(1).fillna(0.333)
    
    # 2. Course-specific performance
    if 'boat_no' in df.columns and 'racer_win_rate' in df.columns:
        # Interaction: high winrate racer on favorable course
        df['course_winrate_synergy'] = df['racer_win_rate'] * df.get('course_advantage', 1.0)
        
        # Inner course threat: if boat 1-3 have high win rates
        for i in range(1, 4):
            col = f'inner_boat_{i}_threat'
            df[col] = (df['boat_no'] > i).astype(int) * df.get('racer_win_rate', 0.5)
    
    # 3. Weather impact features
    if 'wind_speed' in df.columns:
        df['is_strong_wind'] = (df['wind_speed'] >= 5).astype(int)
        df['is_rough_conditions'] = ((df['wind_speed'] >= 4) | (df.get('wave_height', 0) >= 5)).astype(int)
        
        # Wind direction impact on outer courses
        if 'wind_direction' in df.columns and 'boat_no' in df.columns:
            # Tailwind (direction 3-5) benefits outer courses
            tailwind = df['wind_direction'].isin([3, 4, 5]).astype(int)
            df['tailwind_outer_benefit'] = tailwind * (df['boat_no'] >= 4).astype(int) * df['wind_speed'] / 10
    
    # 4. Motor/Boat equipment scores
    if 'motor_2ren' in df.columns and 'boat_2ren' in df.columns:
        df['equipment_total'] = df['motor_2ren'].fillna(30) + df['boat_2ren'].fillna(30)
        df['equipment_quality'] = (df['equipment_total'] > 70).astype(int) + (df['equipment_total'] > 80).astype(int)
    
    # 5. Exhibition time analysis
    if 'exhibition_time' in df.columns:
        df['fast_exhibition'] = (df['exhibition_time'] <= 6.70).astype(int)
        df['slow_exhibition'] = (df['exhibition_time'] >= 6.90).astype(int)
    
    # 6. Competitive field analysis
    if 'racer_win_rate' in df.columns:
        # Standard deviation of win rates in the race
        df['field_strength_std'] = df.groupby(['date', 'jyo_cd', 'race_no'])['racer_win_rate'].transform('std').fillna(0.1)
        df['is_competitive_race'] = (df['field_strength_std'] < 0.05).astype(int)
    
    return df


def train_lightgbm(X_train, y_train, X_val, y_val, cat_indices):
    """Train LightGBM model"""
    params = {
        'objective': 'binary',
        'metric': 'auc',
        'boosting_type': 'gbdt',
        'num_leaves': 63,
        'max_depth': 8,
        'learning_rate': 0.025,
        'feature_fraction': 0.8,
        'bagging_fraction': 0.8,
        'bagging_freq': 5,
        'min_child_samples': 50,
        'lambda_l1': 0.1,
        'lambda_l2': 0.1,
        'verbose': -1,
        'seed': 42,
        'n_jobs': -1
    }
    
    train_data = lgb.Dataset(X_train, label=y_train, categorical_feature=cat_indices)
    val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
    
    model = lgb.train(
        params,
        train_data,
        num_boost_round=1500,
        valid_sets=[val_data],
        callbacks=[
            lgb.early_stopping(stopping_rounds=100),
            lgb.log_evaluation(period=0)
        ]
    )
    return model


def train_xgboost(X_train, y_train, X_val, y_val):
    """Train XGBoost model"""
    params = {
        'objective': 'binary:logistic',
        'eval_metric': 'auc',
        'max_depth': 7,
        'learning_rate': 0.03,
        'subsample': 0.8,
        'colsample_bytree': 0.8,
        'min_child_weight': 50,
        'reg_alpha': 0.1,
        'reg_lambda': 0.1,
        'seed': 42,
        'n_jobs': -1,
        'verbosity': 0
    }
    
    dtrain = xgb.DMatrix(X_train, label=y_train)
    dval = xgb.DMatrix(X_val, label=y_val)
    
    model = xgb.train(
        params,
        dtrain,
        num_boost_round=1500,
        evals=[(dval, 'val')],
        early_stopping_rounds=100,
        verbose_eval=False
    )
    return model


def train_catboost(X_train, y_train, X_val, y_val, cat_indices):
    """Train CatBoost model"""
    model = CatBoostClassifier(
        iterations=1500,
        depth=7,
        learning_rate=0.03,
        loss_function='Logloss',
        eval_metric='AUC',
        random_seed=42,
        verbose=0,
        early_stopping_rounds=100,
        cat_features=cat_indices
    )
    model.fit(X_train, y_train, eval_set=(X_val, y_val), verbose=0)
    return model


def train_ensemble_v3(output_dir="models", n_splits=5, use_v3_features=True):
    """Train ensemble model with all enhancements"""
    print("=" * 70)
    print("🚀 Kouei Model Training V3 - Full Ensemble")
    print("=" * 70)
    
    # Load data
    print("\n📊 Loading data...")
    df = get_dataframe()
    print(f"  Total records: {len(df)}")
    
    if df.empty:
        print("❌ No data available")
        return None
    
    # Add V3 features
    if use_v3_features:
        print("\n⚙️ Adding V3 enhanced features...")
        df = add_v3_features(df)
    
    # Preprocess
    print("\n⚙️ Preprocessing data...")
    processed = preprocess(df, is_training=True)
    print(f"  Processed records: {len(processed)}")
    
    # Define features (add V3 features)
    v3_features = [
        'recent_avg_rank', 'recent_win_rate', 'recent_rentai_rate',
        'course_winrate_synergy', 'is_strong_wind', 'is_rough_conditions',
        'tailwind_outer_benefit', 'equipment_total', 'equipment_quality',
        'fast_exhibition', 'slow_exhibition', 'field_strength_std', 'is_competitive_race'
    ]
    
    # Seasonal features (V3.1)
    seasonal_features = [
        'month', 'is_winter', 'is_spring', 'is_summer', 'is_autumn',
        'temp_deviation', 'temp_zscore_seasonal', 'water_temp_deviation',
        'temp_venue_adjusted', 'temp_anomaly', 'winter_outer_advantage',
        'summer_speed_factor', 'temp_exhibition_interaction'
    ]
    v3_features = v3_features + seasonal_features
    
    all_features = FEATURES + [f for f in v3_features if f in processed.columns]
    available_features = [f for f in all_features if f in processed.columns]
    
    print(f"  Total features: {len(available_features)}")
    
    # Identify categorical features
    cat_indices = [i for i, f in enumerate(available_features) if f in CAT_FEATURES]
    print(f"  Categorical features: {len(cat_indices)}")
    
    X = processed[available_features].fillna(0)
    y = processed['target']
    
    print(f"\n📈 Target distribution:")
    print(f"  Win (1): {y.sum()} ({y.mean()*100:.1f}%)")
    print(f"  Loss (0): {len(y) - y.sum()} ({(1-y.mean())*100:.1f}%)")
    
    # Time series cross-validation
    print(f"\n🔄 Training with {n_splits}-fold time series CV...")
    tscv = TimeSeriesSplit(n_splits=n_splits)
    
    lgbm_scores = []
    xgb_scores = []
    cat_scores = []
    ensemble_scores = []
    
    best_lgbm = None
    best_xgb = None
    best_cat = None
    best_ensemble_score = 0
    best_weights = [0.4, 0.3, 0.3]  # LightGBM, XGBoost, CatBoost
    
    for fold, (train_idx, val_idx) in enumerate(tscv.split(X), 1):
        print(f"\n  Fold {fold}/{n_splits}")
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
        
        # Train LightGBM
        lgbm_model = train_lightgbm(X_train, y_train, X_val, y_val, cat_indices)
        lgbm_pred = lgbm_model.predict(X_val)
        lgbm_auc = roc_auc_score(y_val, lgbm_pred)
        lgbm_scores.append(lgbm_auc)
        print(f"    LightGBM AUC: {lgbm_auc:.4f}")
        
        # Train XGBoost
        xgb_model = train_xgboost(X_train, y_train, X_val, y_val)
        xgb_pred = xgb_model.predict(xgb.DMatrix(X_val))
        xgb_auc = roc_auc_score(y_val, xgb_pred)
        xgb_scores.append(xgb_auc)
        print(f"    XGBoost AUC:  {xgb_auc:.4f}")
        
        # Train CatBoost
        cat_model = train_catboost(X_train, y_train, X_val, y_val, cat_indices)
        cat_pred = cat_model.predict_proba(X_val)[:, 1]
        cat_auc = roc_auc_score(y_val, cat_pred)
        cat_scores.append(cat_auc)
        print(f"    CatBoost AUC: {cat_auc:.4f}")
        
        # Ensemble prediction
        ensemble_pred = best_weights[0] * lgbm_pred + best_weights[1] * xgb_pred + best_weights[2] * cat_pred
        ensemble_auc = roc_auc_score(y_val, ensemble_pred)
        ensemble_scores.append(ensemble_auc)
        print(f"    Ensemble AUC: {ensemble_auc:.4f}")
        
        if ensemble_auc > best_ensemble_score:
            best_ensemble_score = ensemble_auc
            best_lgbm = lgbm_model
            best_xgb = xgb_model
            best_cat = cat_model
            
            # Optimize weights
            from scipy.optimize import minimize
            def neg_auc(w):
                pred = w[0] * lgbm_pred + w[1] * xgb_pred + w[2] * cat_pred
                return -roc_auc_score(y_val, pred)
            
            result = minimize(neg_auc, [0.4, 0.3, 0.3], bounds=[(0,1)]*3, 
                            constraints={'type': 'eq', 'fun': lambda w: sum(w) - 1})
            best_weights = result.x.tolist()
    
    # Final results
    print("\n" + "=" * 70)
    print("📊 Final Cross-Validation Results:")
    print(f"  LightGBM - Avg AUC: {np.mean(lgbm_scores):.4f} (±{np.std(lgbm_scores):.4f})")
    print(f"  XGBoost  - Avg AUC: {np.mean(xgb_scores):.4f} (±{np.std(xgb_scores):.4f})")
    print(f"  CatBoost - Avg AUC: {np.mean(cat_scores):.4f} (±{np.std(cat_scores):.4f})")
    print(f"  Ensemble - Avg AUC: {np.mean(ensemble_scores):.4f} (±{np.std(ensemble_scores):.4f})")
    print(f"\n  Best ensemble weights: LGB={best_weights[0]:.2f}, XGB={best_weights[1]:.2f}, CAT={best_weights[2]:.2f}")
    
    # Feature importance (from LightGBM)
    print("\n🔑 Top 25 Feature Importance (LightGBM):")
    importance = pd.DataFrame({
        'feature': available_features,
        'importance': best_lgbm.feature_importance(importance_type='gain')
    }).sort_values('importance', ascending=False)
    
    for i, row in importance.head(25).iterrows():
        print(f"  {row['feature']}: {row['importance']:.0f}")
    
    # Save models
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Backup old models
    for model_file in ['lgbm_model.txt', 'xgb_model.json', 'cat_model.cbm']:
        old_path = os.path.join(output_dir, model_file)
        if os.path.exists(old_path):
            backup_path = os.path.join(output_dir, f"{model_file.split('.')[0]}_backup_{timestamp}.{model_file.split('.')[1]}")
            os.rename(old_path, backup_path)
    
    # Save new models
    best_lgbm.save_model(os.path.join(output_dir, "lgbm_model.txt"))
    best_xgb.save_model(os.path.join(output_dir, "xgb_model.json"))
    best_cat.save_model(os.path.join(output_dir, "cat_model.cbm"))
    
    print(f"\n✅ Saved models to {output_dir}/")
    
    # Save ensemble weights
    weights_data = {
        'weights': {'lgbm': best_weights[0], 'xgb': best_weights[1], 'cat': best_weights[2]},
        'timestamp': timestamp,
        'cv_scores': {
            'lgbm': {'mean': float(np.mean(lgbm_scores)), 'std': float(np.std(lgbm_scores))},
            'xgb': {'mean': float(np.mean(xgb_scores)), 'std': float(np.std(xgb_scores))},
            'cat': {'mean': float(np.mean(cat_scores)), 'std': float(np.std(cat_scores))},
            'ensemble': {'mean': float(np.mean(ensemble_scores)), 'std': float(np.std(ensemble_scores))}
        }
    }
    
    with open(os.path.join(output_dir, 'ensemble_weights.json'), 'w') as f:
        json.dump(weights_data, f, indent=2)
    
    # Save metadata
    metadata = {
        'timestamp': timestamp,
        'features': available_features,
        'n_features': len(available_features),
        'n_samples': len(X),
        'cat_features': [available_features[i] for i in cat_indices],
        'cv_results': {
            'lgbm': lgbm_scores,
            'xgb': xgb_scores,
            'cat': cat_scores,
            'ensemble': ensemble_scores
        },
        'best_weights': best_weights,
        'feature_importance': importance.head(40).to_dict('records')
    }
    
    with open(os.path.join(output_dir, 'training_metadata_v3.json'), 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print("✅ Training complete!")
    return best_lgbm, best_xgb, best_cat, best_weights


if __name__ == "__main__":
    train_ensemble_v3()
