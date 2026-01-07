import optuna
import lightgbm as lgb
import pandas as pd
import json
import os
from sklearn.model_selection import train_test_split
from src.features.preprocessing import preprocess, FEATURES, CAT_FEATURES

DATA_PATH = "data/processed/race_data.csv"
CONFIG_PATH = "config/model_params.json"

def run_optimization(trials=50):
    if not os.path.exists(DATA_PATH):
        print("Data not found.")
        return None

    print("Loading data for optimization...")
    df = pd.read_csv(DATA_PATH)
    
    # Simple temporal split for validation
    df = df.sort_values('date')
    train_size = int(len(df) * 0.8)
    train_df = df.iloc[:train_size]
    val_df = df.iloc[train_size:]

    # Preprocess
    train_processed = preprocess(train_df, is_training=True)
    val_processed = preprocess(val_df, is_training=True)
    
    # Extract features and target
    X_train = train_processed[FEATURES]
    y_train = train_processed['target']
    X_val = val_processed[FEATURES]
    y_val = val_processed['target']

    def objective(trial):
        params = {
            'objective': 'binary',
            'metric': 'binary_logloss',
            'verbosity': -1,
            'boosting_type': 'gbdt',
            'learning_rate': trial.suggest_float('learning_rate', 0.005, 0.1, log=True),
            'num_leaves': trial.suggest_int('num_leaves', 20, 150),
            'max_depth': trial.suggest_int('max_depth', 3, 12),
            'min_child_samples': trial.suggest_int('min_child_samples', 5, 100),
            'subsample': trial.suggest_float('subsample', 0.5, 1.0),
            'colsample_bytree': trial.suggest_float('colsample_bytree', 0.5, 1.0),
        }
        
        train_data = lgb.Dataset(X_train[FEATURES], label=y_train, categorical_feature=CAT_FEATURES)
        valid_data = lgb.Dataset(X_val[FEATURES], label=y_val, categorical_feature=CAT_FEATURES, reference=train_data)
        
        model = lgb.train(
            params,
            train_data,
            valid_sets=[valid_data],
            callbacks=[lgb.early_stopping(stopping_rounds=10), lgb.log_evaluation(0)]
        )
        
        # Use log loss on validation set as metric
        return model.best_score['valid_0']['binary_logloss']

    print(f"Starting optimization with {trials} trials...")
    study = optuna.create_study(direction='minimize')
    study.optimize(objective, n_trials=trials)

    print("Best trials:")
    print(study.best_trial)

    best_params = study.best_trial.params
    # Add fixed params
    best_params.update({
        'objective': 'binary',
        'metric': 'binary_logloss',
        'verbose': -1,
        'boosting_type': 'gbdt'
    })

    # Save to config
    os.makedirs('config', exist_ok=True)
    with open(CONFIG_PATH, 'w') as f:
        json.dump(best_params, f, indent=4)
        
    print(f"Optimization complete. Parameters saved to {CONFIG_PATH}")
    return best_params

if __name__ == "__main__":
    run_optimization()
