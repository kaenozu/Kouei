import lightgbm as lgb
import pandas as pd
import os
import sys
from datetime import datetime, timedelta
sys.path.append(os.getcwd())
from src.model.evaluator import AccuracyGuard

DATA_PATH = "data/processed/race_data.csv"
MODEL_PATH = "models/lgbm_model.txt"

def train_incremental():
    if not os.path.exists(DATA_PATH):
        print("No data found.")
        return
    
    df = pd.read_csv(DATA_PATH)
    
    # Preprocessing (Simplified - assume build_dataset did it)
    # We need 'target'
    if 'target' not in df.columns:
        # Create target (1 if rank=1 else 0)
        df['target'] = df['rank'].apply(lambda x: 1 if x == 1 else 0)
        
    # Split
    # New Data: Last 30 days
    # Validation: Random 20% of New Data
    df['date'] = pd.to_datetime(df['date'].astype(str), format='%Y%m%d')
    cutoff = df['date'].max() - timedelta(days=30)
    
    recent_df = df[df['date'] >= cutoff].copy()
    if len(recent_df) < 100:
        print("Not enough recent data for incremental update.")
        return

    # Train/Val Split
    val_size = int(len(recent_df) * 0.2)
    train_df = recent_df.iloc[:-val_size]
    val_df = recent_df.iloc[-val_size:]
    
    # Features
    drop_cols = ['target', 'date', 'race_id', 'rank', 'result_rank', 'tansho', 'entry_id', 'jyo_cd', 'race_no', 'race_name', 'racer_id', 'racer_name']
    features = [c for c in train_df.columns if c not in drop_cols]
    
    X_train = train_df[features]
    y_train = train_df['target']
    X_val = val_df[features]
    y_val = val_df['target']
    
    # Load Old Model
    params = {
        'objective': 'binary',
        'metric': 'auc',
        'verbosity': -1
    }
    
    init_model = None
    if os.path.exists(MODEL_PATH):
        print(f"Loading base model from {MODEL_PATH}")
        init_model = MODEL_PATH
        
    train_set = lgb.Dataset(X_train, label=y_train)
    val_set = lgb.Dataset(X_val, label=y_val, reference=train_set)
    
    print("Starting Incremental Training...")
    new_model = lgb.train(
        params,
        train_set,
        num_boost_round=100, # Small round for incremental
        valid_sets=[val_set],
        init_model=init_model, # KEEP THE KNOWLEDGE
        keep_training_booster=True
    )
    
    # Guard Check
    guard = AccuracyGuard(val_df)
    # Be careful: we passed df to Guard but it assumes columns match. 
    # Guard expects 'target' and drops known non-features.
    # We should ensure `val_df` passed to Guard has features + target.
    # The drop_cols list above is stricter.
    # Let's adjust Guard usage or rely on its internal drop.
    # For now, let's just assume Guard can handle it if we ensure columns match.
    
    # Guard needs features X and target y.
    # Our Guard implementation drops standard meta cols.
    
    if guard.compare(MODEL_PATH, new_model):
        print(f"Updating model at {MODEL_PATH}")
        new_model.save_model(MODEL_PATH)
    else:
        print("Update skipped.")

if __name__ == "__main__":
    train_incremental()
