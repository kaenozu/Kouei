import pandas as pd
import lightgbm as lgb
import os
import argparse

def simulate(model_path="models/lgbm_model.txt", data_path="data/processed/race_data.csv", threshold=0.5, df=None):
    if not os.path.exists(model_path):
        print("Model not found.")
        return
    
    # Load Model
    model = lgb.Booster(model_file=model_path)
    
    # Use provided DF or load from path
    if df is None:
        if not os.path.exists(data_path):
            print("Data not found.")
            return
        df = pd.read_csv(data_path)
    else:
        # Create a copy to avoid modifying the original
        df = df.copy()
    
    # Filter for valid rows (where we have rank and dividend)
    # We need 'tansho' column
    if 'tansho' not in df.columns:
        print("Error: 'tansho' column missing in dataset. Please rebuild dataset.")
        return

    # Preprocessing (Same as train_model/predict)
    # We need to replicate preprocessing exactly or better, share code.
    # For now, replicate simplified version
    
    # Features
    features = [
        'jyo_cd', 'boat_no', 'racer_win_rate', 'motor_2ren', 'boat_2ren',
        'exhibition_time', 'tilt', 
        'temperature', 'water_temperature', 
        'wind_speed', 'wave_height', 
        'wind_direction', 'weather',
        'racer_win_rate_diff', 'motor_2ren_diff', 'exhibition_time_diff'
    ]
    numeric_cols = ['racer_win_rate', 'motor_2ren', 'boat_2ren', 'exhibition_time', 
                    'wind_speed', 'wave_height', 'temperature', 'water_temperature', 'tilt']
    
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        else:
            df[col] = 0.0
    
    # Impute
    df['jyo_cd'] = pd.to_numeric(df['jyo_cd'], errors='coerce').fillna(0).astype(int)
    df['exhibition_time'] = df['exhibition_time'].fillna(df['exhibition_time'].mean())
    df[numeric_cols] = df[numeric_cols].fillna(0)
    
    # Categorical
    for col in ['wind_direction', 'weather']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(-1).astype(int)
        else:
            df[col] = -1

    # Relative Features
    race_groups = df.groupby(['date', 'jyo_cd', 'race_no'])
    df['win_rate_avg'] = race_groups['racer_win_rate'].transform('mean')
    df['racer_win_rate_diff'] = df['racer_win_rate'] - df['win_rate_avg']
    df['motor_2ren_avg'] = race_groups['motor_2ren'].transform('mean')
    df['motor_2ren_diff'] = df['motor_2ren'] - df['motor_2ren_avg']
    df['exh_time_avg'] = race_groups['exhibition_time'].transform('mean')
    df['exhibition_time_diff'] = df['exhibition_time'] - df['exh_time_avg']

    # Convert rank to numeric for comparison
    df['rank'] = pd.to_numeric(df['rank'], errors='coerce')
    
    X = df[features]
    
    # Predict
    preds = model.predict(X)
    df['prob_win'] = preds
    
    # Simulation Logic
    # Strategy: Bet 100 yen on Boat with highest prob if prob > threshold
    
    # Group by Race
    # Ensure rank is available and valid
    df = df.dropna(subset=['rank'])
    
    races = df.groupby(['date', 'jyo_cd', 'race_no'])
    
    total_bet = 0
    total_return = 0
    bets_count = 0
    hits_count = 0
    
    print(f"Simulating strategy: Bet on 1st rank prob > {threshold}...")
    
    for (date, jyo, race), group in races:
        # Sort by prob
        group = group.sort_values('prob_win', ascending=False)
        top_boat = group.iloc[0]
        
        if top_boat['prob_win'] >= threshold:
            # Place Bet
            bet_amount = 100
            total_bet += bet_amount
            bets_count += 1
            
            # Check Result
            # Assuming 'rank' is available
            if top_boat['rank'] == 1:
                # HIT
                hits_count += 1
                return_amount = top_boat['tansho'] # 100 yen ticket payout
                total_return += return_amount
    
    roi = (total_return / total_bet * 100) if total_bet > 0 else 0
    hit_rate = (hits_count / bets_count * 100) if bets_count > 0 else 0
    
    results = {
        "total_bets": bets_count,
        "hit_rate": hit_rate,
        "hits": hits_count,
        "total_bet_amount": total_bet,
        "total_return_amount": total_return,
        "roi": roi,
        "profit": total_return - total_bet
    }
    
    print(f"--- Results ---")
    print(f"Total Bets: {results['total_bets']}")
    print(f"Hit Rate: {results['hit_rate']:.2f}% ({results['hits']}/{results['total_bets']})")
    print(f"Total Bet Amount: {results['total_bet_amount']} JPY")
    print(f"Total Return: {results['total_return_amount']} JPY")
    print(f"ROI: {results['roi']:.2f}%")
    print(f"Profit: {results['profit']} JPY")
    
    return results

def get_simulation_history(model_path="models/lgbm_model.txt", data_path="data/processed/race_data.csv", threshold=0.4, df=None):
    if not os.path.exists(model_path): return []

    model = lgb.Booster(model_file=model_path)
    
    if df is None:
        if not os.path.exists(data_path): return []
        df = pd.read_csv(data_path)
    else:
        df = df.copy()
    
    if 'tansho' not in df.columns: return []

    # Features and Preprocessing
    features = ['jyo_cd', 'boat_no', 'racer_win_rate', 'motor_2ren', 'boat_2ren', 'exhibition_time', 'tilt', 
                'temperature', 'water_temperature', 'wind_speed', 'wave_height', 'wind_direction', 'weather',
                'racer_win_rate_diff', 'motor_2ren_diff', 'exhibition_time_diff']
    numeric_cols = ['racer_win_rate', 'motor_2ren', 'boat_2ren', 'exhibition_time', 'wind_speed', 'wave_height', 'temperature', 'water_temperature', 'tilt']
    
    df['jyo_cd'] = pd.to_numeric(df['jyo_cd'], errors='coerce').fillna(0).astype(int)
    for col in numeric_cols: df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    for col in ['wind_direction', 'weather']: df[col] = pd.to_numeric(df[col], errors='coerce').fillna(-1).astype(int)

    # Relative Features
    race_groups = df.groupby(['date', 'jyo_cd', 'race_no'])
    df['win_rate_avg'] = race_groups['racer_win_rate'].transform('mean')
    df['racer_win_rate_diff'] = df['racer_win_rate'] - df['win_rate_avg']
    df['motor_2ren_avg'] = race_groups['motor_2ren'].transform('mean')
    df['motor_2ren_diff'] = df['motor_2ren'] - df['motor_2ren_avg']
    df['exh_time_avg'] = race_groups['exhibition_time'].transform('mean')
    df['exhibition_time_diff'] = df['exhibition_time'] - df['exh_time_avg']

    df['rank'] = pd.to_numeric(df['rank'], errors='coerce')
    
    preds = model.predict(df[features])
    df['prob_win'] = preds
    
    df = df.dropna(subset=['rank'])
    df = df.sort_values(['date', 'jyo_cd', 'race_no'])
    
    races = df.groupby(['date', 'jyo_cd', 'race_no'])
    
    history = []
    cumulative_profit = 0
    
    for (date, jyo, race), group in races:
        group = group.sort_values('prob_win', ascending=False)
        top_boat = group.iloc[0]
        
        if top_boat['prob_win'] >= threshold:
            bet_amount = 100
            payout = top_boat['tansho'] if top_boat['rank'] == 1 else 0
            profit = payout - bet_amount
            cumulative_profit += profit
            
            history.append({
                "date": str(date),
                "profit": int(cumulative_profit),
                "label": f"{str(date)[4:6]}/{str(date)[6:8]}" # MM/DD
            })
            
    # Subsample if too many points for chart performance
    if len(history) > 100:
        step = len(history) // 50
        history = history[::step]
        
    return history

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--threshold", type=float, default=0.3)
    args = parser.parse_args()
    simulate(threshold=args.threshold)
