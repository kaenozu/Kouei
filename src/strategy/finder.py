import pandas as pd
import lightgbm as lgb
import os
import json
import itertools
from src.features.preprocessing import preprocess, FEATURES
from concurrent.futures import ThreadPoolExecutor

DATA_PATH = "data/processed/race_data.csv"
MODEL_PATH = "models/lgbm_model.txt"
STRATEGY_PATH = "config/strategies.json"
STADIUMS = [f"{i:02d}" for i in range(1, 25)]

def find_strategies(min_roi=120.0, min_samples=30):
    if not os.path.exists(DATA_PATH) or not os.path.exists(MODEL_PATH):
        print("Data or model not found.")
        return []

    print("Loading data for Strategy Finder...")
    df = pd.read_csv(DATA_PATH)
    
    # Preprocess and Predict once
    model = lgb.Booster(model_file=MODEL_PATH)
    
    # Ensure features exist (same simplified preprocessing as simulator)
    # Ideally should use common preprocessing, but need raw cols for filtering
    # So we used preprocessed X for prediction, but keep raw df for filtering
    
    # Re-apply preprocessing to get features for prediction
    # We need to be careful not to overwrite raw columns we need for filtering like 'wind_speed'
    # Actually, preprocess() returns a NEW dataframe with features.
    
    encoded_df = preprocess(df.copy(), is_training=False)
    X = encoded_df[FEATURES]
    df['prob_win'] = model.predict(X)
    
    # Ensure rank and tansho are present
    df['rank'] = pd.to_numeric(df['rank'], errors='coerce')
    df['tansho'] = pd.to_numeric(df['tansho'], errors='coerce').fillna(0)
    
    valid_df = df.dropna(subset=['rank'])
    
    # Define Search Space
    # Stadiums: All
    # Wind: ["calm", "light", "medium", "strong"] 
    #   calm: 0-1m, light: 2-3m, medium: 4-6m, strong: 7m+
    # Prob Threshold: [0.3, 0.4, 0.5, 0.6]
    
    wind_conditions = {
        "calm": (0, 1),
        "light": (2, 3),
        "medium": (4, 6),
        "strong": (7, 100)
    }
    
    prob_thresholds = [0.3, 0.4, 0.5, 0.6]
    
    strategies = []
    
    print("Mining strategies...")
    
    # Iterate all combinations
    for jyo in STADIUMS:
        jyo_df = valid_df[valid_df['jyo_cd'] == int(jyo)]
        if len(jyo_df) == 0: continue
        
        for wind_name, (w_min, w_max) in wind_conditions.items():
            # Filter by wind
            wind_mask = (jyo_df['wind_speed'] >= w_min) & (jyo_df['wind_speed'] <= w_max)
            wind_df = jyo_df[wind_mask]
            
            if len(wind_df) < min_samples: continue
            
            for prob in prob_thresholds:
                # Filter by prediction confidence (only bet if top pred > prob)
                # Need to group by race to find top boat
                
                # Doing a fast vectorised simulation is hard with group-by top 1 logic
                # So we iterate races? Too slow for brute force.
                # Optimization: Filter rows where prob_win > prob first?
                # No, needs to be TOP boat.
                
                # Fast logic:
                # 1. Sort by Prob Desc within Race
                # 2. Take top 1
                # 3. Filter if top 1 prob > threshold
                
                # Let's pre-calculate "Top Boat" mask for the whole dataset to speed up
                # But creating a new df for every loop is slow.
                
                # Better approach:
                # Pre-calculate a "is_top_boat" column for the whole dataset?
                pass

    # Efficient Strategy:
    # 1. Mark top boat for every race in master DF
    # 2. Filter master DF for only top boats
    # 3. Apply filters (Stadium, Wind, Prob) on this "Top Boats DF"
    # 4. Calculate ROI
    
    # 1. Mark Top Boat
    # Sort by race_id, prob_win desc
    # (Assuming unique race_id can be made from date + jyo + race)
    valid_df['race_id'] = valid_df['date'].astype(str) + "_" + valid_df['jyo_cd'].astype(str) + "_" + valid_df['race_no'].astype(str)
    
    # Sort
    valid_df = valid_df.sort_values(['race_id', 'prob_win'], ascending=[True, False])
    
    # Drop duplicates to keep only top 1 (highest prob)
    top_boats = valid_df.drop_duplicates(subset=['race_id'], keep='first')
    
    discovered = []
    
    for jyo in STADIUMS:
        stadium_boats = top_boats[top_boats['jyo_cd'] == int(jyo)]
        
        for wind_name, (w_min, w_max) in wind_conditions.items():
            wind_boats = stadium_boats[
                (stadium_boats['wind_speed'] >= w_min) & 
                (stadium_boats['wind_speed'] <= w_max)
            ]
            
            for prob in prob_thresholds:
                target_boats = wind_boats[wind_boats['prob_win'] >= prob]
                
                n_bets = len(target_boats)
                if n_bets < min_samples: continue
                
                # Calc ROI
                hits = target_boats[target_boats['rank'] == 1]
                n_hits = len(hits)
                return_amt = hits['tansho'].sum()
                bet_amt = n_bets * 100
                roi = (return_amt / bet_amt) * 100
                
                if roi >= min_roi:
                    strategy = {
                        "name": f"{jyo}#{wind_name}#{prob}",
                        "display_name": f"会場{jyo} / 風{w_min}-{w_max}m / 自信{int(prob*100)}%+",
                        "filters": {
                            "jyo": jyo,
                            "wind_min": w_min,
                            "wind_max": w_max,
                            "min_prob": prob
                        },
                        "stats": {
                            "roi": round(roi, 1),
                            "hit_rate": round((n_hits/n_bets)*100, 1),
                            "sample_size": n_bets,
                            "profit": int(return_amt - bet_amt)
                        }
                    }
                    discovered.append(strategy)
                    print(f"FOUND: {strategy['display_name']} -> ROI: {roi:.1f}% (n={n_bets})")

    # Sort by ROI
    discovered.sort(key=lambda x: x['stats']['roi'], reverse=True)
    
    # Save
    os.makedirs('config', exist_ok=True)
    with open(STRATEGY_PATH, 'w', encoding='utf-8') as f:
        json.dump(discovered, f, indent=4, ensure_ascii=False)
        
    print(f"Saved {len(discovered)} strategies to {STRATEGY_PATH}")
    return discovered

if __name__ == "__main__":
    find_strategies()
