import pandas as pd
import lightgbm as lgb
import os
import argparse
from datetime import datetime
from src.parser.html_parser import ProgramParser, ResultParser, BeforeInfoParser
from src.collector.downloader import Downloader
from src.features.preprocessing import preprocess, FEATURES

# Removed local preprocess - using src.features.preprocessing.preprocess

def predict_race(date_str, jyo_cd, race_no, model):
    # 1. Download/Load Data
    # For inference, we assume data is already downloaded or we download on the fly.
    # Let's simple check local file.
    base_dir = "data/raw"
    program_path = os.path.join(base_dir, date_str, jyo_cd, f"program_{race_no}.html")
    before_path = os.path.join(base_dir, date_str, jyo_cd, f"beforeinfo_{race_no}.html")
    
    if not os.path.exists(program_path):
        print(f"Program file not found: {program_path}")
        return
    
    with open(program_path, 'r', encoding='utf-8') as f:
        prog_df = ProgramParser.parse(f.read(), date_str, jyo_cd, int(race_no))
        
    before_df = None
    if os.path.exists(before_path):
        with open(before_path, 'r', encoding='utf-8') as f:
            before_df = BeforeInfoParser.parse(f.read(), date_str, jyo_cd, int(race_no))
            
    # Merge
    # Ensure types
    prog_df['boat_no'] = prog_df['boat_no'].astype(int)
    if before_df is not None:
        before_df['boat_no'] = before_df['boat_no'].astype(int)
        df_merged = pd.merge(prog_df, before_df, on=['date', 'jyo_cd', 'race_no', 'boat_no'], how='left')
    else:
        df_merged = prog_df
        print("Warning: No before info found.")

    # Preprocess
    df_processed = preprocess(df_merged, training=False)
    X = df_processed[FEATURES]
    
    # Predict
    prob = model.predict(X)
    
    df_merged['prob_win'] = prob
    
    # Display
    print(f"\nPrediction for {date_str} {jyo_cd} Race {race_no}:")
    result = df_merged[['boat_no', 'racer_name', 'prob_win']].sort_values('prob_win', ascending=False)
    print(result)
    
    # Simple bet suggestion
    winner = result.iloc[0]
    print(f"Predicted Winner: {winner['boat_no']} ({winner['racer_name']}) - Prob: {winner['prob_win']:.4f}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", type=str, required=True, help="YYYYMMDD")
    parser.add_argument("--jyo", type=str, required=True, help="Stadium Code (e.g. 02)")
    parser.add_argument("--race", type=int, default=1, help="Race No")
    args = parser.parse_args()
    
    model_path = "models/lgbm_model.txt"
    if not os.path.exists(model_path):
        print("Model not found. Train first.")
        return
        
    model = lgb.Booster(model_file=model_path)
    
    predict_race(args.date, args.jyo, args.race, model)

if __name__ == "__main__":
    main()
