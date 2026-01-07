"""Enhanced Model Training Script V2 with new features"""
import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import TimeSeriesSplit
import os
import json
from datetime import datetime

# Import preprocessing
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.features.preprocessing import preprocess, FEATURES
from src.api.dependencies import get_dataframe


def train_model_v2(output_dir="models", n_splits=5):
    """Train enhanced LightGBM model with new features"""
    print("=" * 60)
    print("🚀 Kouei Model Training V2")
    print("=" * 60)
    
    # Load data
    print("\n📊 Loading data...")
    df = get_dataframe()
    print(f"  Total records: {len(df)}")
    
    if df.empty:
        print("❌ No data available")
        return None
    
    # Preprocess
    print("\n⚙️ Preprocessing data...")
    processed = preprocess(df, is_training=True)
    print(f"  Processed records: {len(processed)}")
    
    # Prepare features
    available_features = [f for f in FEATURES if f in processed.columns]
    print(f"  Available features: {len(available_features)}/{len(FEATURES)}")
    
    X = processed[available_features].fillna(0)
    y = processed['target']
    
    print(f"\n📈 Target distribution:")
    print(f"  Win (1): {y.sum()} ({y.mean()*100:.1f}%)")
    print(f"  Loss (0): {len(y) - y.sum()} ({(1-y.mean())*100:.1f}%)")
    
    # LightGBM parameters
    params = {
        'objective': 'binary',
        'metric': 'auc',
        'boosting_type': 'gbdt',
        'num_leaves': 63,
        'max_depth': 8,
        'learning_rate': 0.03,
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
    
    # Time series cross-validation
    print(f"\n🔄 Training with {n_splits}-fold time series CV...")
    tscv = TimeSeriesSplit(n_splits=n_splits)
    
    cv_scores = []
    best_model = None
    best_score = 0
    
    for fold, (train_idx, val_idx) in enumerate(tscv.split(X), 1):
        X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
        y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]
        
        train_data = lgb.Dataset(X_train, label=y_train)
        val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
        
        model = lgb.train(
            params,
            train_data,
            num_boost_round=1000,
            valid_sets=[val_data],
            callbacks=[
                lgb.early_stopping(stopping_rounds=50),
                lgb.log_evaluation(period=0)  # Suppress output
            ]
        )
        
        # Evaluate
        val_pred = model.predict(X_val)
        from sklearn.metrics import roc_auc_score, accuracy_score
        auc = roc_auc_score(y_val, val_pred)
        acc = accuracy_score(y_val, (val_pred > 0.5).astype(int))
        
        cv_scores.append({'fold': fold, 'auc': auc, 'accuracy': acc})
        print(f"  Fold {fold}: AUC={auc:.4f}, Acc={acc:.4f}")
        
        if auc > best_score:
            best_score = auc
            best_model = model
    
    # Final metrics
    avg_auc = np.mean([s['auc'] for s in cv_scores])
    avg_acc = np.mean([s['accuracy'] for s in cv_scores])
    print(f"\n📊 Cross-Validation Results:")
    print(f"  Average AUC: {avg_auc:.4f}")
    print(f"  Average Accuracy: {avg_acc:.4f}")
    
    # Feature importance
    print("\n🔑 Top 20 Feature Importance:")
    importance = pd.DataFrame({
        'feature': available_features,
        'importance': best_model.feature_importance(importance_type='gain')
    }).sort_values('importance', ascending=False)
    
    for i, row in importance.head(20).iterrows():
        print(f"  {row['feature']}: {row['importance']:.0f}")
    
    # Save model
    os.makedirs(output_dir, exist_ok=True)
    model_path = os.path.join(output_dir, "lgbm_model.txt")
    
    # Backup old model
    if os.path.exists(model_path):
        backup_path = os.path.join(output_dir, f"lgbm_model_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        os.rename(model_path, backup_path)
        print(f"\n📦 Backed up old model to: {backup_path}")
    
    best_model.save_model(model_path)
    print(f"✅ Saved new model to: {model_path}")
    
    # Save training metadata
    metadata = {
        'timestamp': datetime.now().isoformat(),
        'features': available_features,
        'n_features': len(available_features),
        'n_samples': len(X),
        'cv_scores': cv_scores,
        'avg_auc': float(avg_auc),
        'avg_accuracy': float(avg_acc),
        'params': params,
        'feature_importance': importance.head(30).to_dict('records')
    }
    
    metadata_path = os.path.join(output_dir, "training_metadata.json")
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print(f"📝 Saved training metadata to: {metadata_path}")
    
    return best_model, metadata


def evaluate_betting_strategy(df, model, strategy='win'):
    """Evaluate model performance for betting"""
    print(f"\n💰 Evaluating {strategy} betting strategy...")
    
    processed = preprocess(df, is_training=False)
    available_features = [f for f in FEATURES if f in processed.columns]
    X = processed[available_features].fillna(0)
    
    processed['pred_prob'] = model.predict(X)
    processed['rank_num'] = pd.to_numeric(df['rank'], errors='coerce')
    
    total_bets = 0
    total_wins = 0
    total_return = 0
    
    # Evaluate by confidence level
    results_by_conf = {'S': [], 'A': [], 'B': [], 'C': []}
    
    for (date, jyo, race), group in processed.groupby(['date', 'jyo_cd', 'race_no']):
        if len(group) < 6:
            continue
        
        sorted_group = group.sort_values('pred_prob', ascending=False)
        top = sorted_group.iloc[0]
        
        # Determine confidence
        top_prob = top['pred_prob']
        if top_prob >= 0.5:
            conf = 'S'
        elif top_prob >= 0.4:
            conf = 'A'
        elif top_prob >= 0.3:
            conf = 'B'
        else:
            conf = 'C'
        
        # Check if prediction is correct
        actual_winner = group[group['rank_num'] == 1]
        if len(actual_winner) == 0:
            continue
        
        predicted_boat = int(top['boat_no'])
        actual_boat = int(actual_winner.iloc[0]['boat_no'])
        hit = predicted_boat == actual_boat
        
        # Estimate odds based on course
        COURSE_AVG_ODDS = {1: 2.5, 2: 6.0, 3: 7.0, 4: 8.0, 5: 12.0, 6: 15.0}
        odds = COURSE_AVG_ODDS.get(predicted_boat, 5.0)
        
        total_bets += 1
        if hit:
            total_wins += 1
            total_return += odds * 100
        
        results_by_conf[conf].append({'hit': hit, 'odds': odds})
    
    # Print results
    print(f"\n📊 Overall Results:")
    hit_rate = total_wins / total_bets * 100 if total_bets > 0 else 0
    roi = (total_return - total_bets * 100) / (total_bets * 100) * 100 if total_bets > 0 else 0
    print(f"  Bets: {total_bets}, Wins: {total_wins}")
    print(f"  Hit Rate: {hit_rate:.1f}%")
    print(f"  ROI: {roi:.1f}%")
    
    print(f"\n📈 Results by Confidence:")
    for conf in ['S', 'A', 'B', 'C']:
        results = results_by_conf[conf]
        if not results:
            continue
        bets = len(results)
        wins = sum(1 for r in results if r['hit'])
        returns = sum(r['odds'] * 100 if r['hit'] else 0 for r in results)
        hr = wins / bets * 100 if bets > 0 else 0
        r = (returns - bets * 100) / (bets * 100) * 100 if bets > 0 else 0
        print(f"  {conf}: Bets={bets}, Wins={wins}, Hit Rate={hr:.1f}%, ROI={r:.1f}%")
    
    return {
        'total_bets': total_bets,
        'total_wins': total_wins,
        'hit_rate': hit_rate,
        'roi': roi
    }


if __name__ == "__main__":
    model, metadata = train_model_v2()
    
    if model:
        # Evaluate on test data
        df = get_dataframe()
        if not df.empty:
            evaluate_betting_strategy(df, model)
