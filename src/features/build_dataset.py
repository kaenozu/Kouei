import os
import pandas as pd
from tqdm import tqdm
import warnings
from bs4 import XMLParsedAsHTMLWarning
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
from src.parser.html_parser import ProgramParser, ResultParser, BeforeInfoParser

def build_dataset(raw_dir="data/raw", output_path="data/processed/race_data.csv"):
    all_programs = []
    all_results = []
    all_beforeinfo = []
    
    if not os.path.exists(raw_dir):
        print(f"Raw directory {raw_dir} not found.")
        return

    dates = sorted(os.listdir(raw_dir))
    # Optimization: If we have many dates, maybe only process recent ones? 
    # For now, let's keep it simple but make the file saving atomic to avoid locking.
    
    for date_str in tqdm(dates, desc="Processing Dates"):
        date_dir = os.path.join(raw_dir, date_str)
        if not os.path.isdir(date_dir):
            continue
            
        stadiums = sorted(os.listdir(date_dir))
        for jyo_cd in stadiums:
            stadium_dir = os.path.join(date_dir, jyo_cd)
            if not os.path.isdir(stadium_dir):
                continue
                
            for race_no in range(1, 13):
                program_path = os.path.join(stadium_dir, f"program_{race_no}.html")
                if os.path.exists(program_path):
                    with open(program_path, 'r', encoding='utf-8') as f:
                        df_prog = ProgramParser.parse(f.read(), date_str, jyo_cd, int(race_no))
                        all_programs.append(df_prog)
                
                before_path = os.path.join(stadium_dir, f"beforeinfo_{race_no}.html")
                if os.path.exists(before_path):
                    with open(before_path, 'r', encoding='utf-8') as f:
                        df_before = BeforeInfoParser.parse(f.read(), date_str, jyo_cd, int(race_no))
                        all_beforeinfo.append(df_before)

                result_path = os.path.join(stadium_dir, f"result_{race_no}.html")
                if os.path.exists(result_path):
                    with open(result_path, 'r', encoding='utf-8') as f:
                        df_res = ResultParser.parse(f.read(), date_str, jyo_cd, int(race_no))
                        all_results.append(df_res)

    if not all_programs:
        print("No program data found.")
        return

    df_programs_all = pd.concat(all_programs, ignore_index=True)
    df_programs_all['race_no'] = df_programs_all['race_no'].astype(int)
    df_programs_all['boat_no'] = df_programs_all['boat_no'].astype(int)
    df_programs_all['jyo_cd'] = df_programs_all['jyo_cd'].astype(str)

    if all_beforeinfo:
        df_before_all = pd.concat(all_beforeinfo, ignore_index=True)
        df_before_all['race_no'] = df_before_all['race_no'].astype(int)
        df_before_all['boat_no'] = df_before_all['boat_no'].astype(int)
        df_before_all['jyo_cd'] = df_before_all['jyo_cd'].astype(str)
        df_programs_all = pd.merge(df_programs_all, df_before_all, on=['date', 'jyo_cd', 'race_no', 'boat_no'], how='left')
    
    if all_results:
        df_results_all = pd.concat(all_results, ignore_index=True)
        df_results_all['race_no'] = df_results_all['race_no'].astype(int)
        df_results_all['boat_no'] = df_results_all['boat_no'].astype(int)
        df_results_all['jyo_cd'] = df_results_all['jyo_cd'].astype(str)
        df_merged = pd.merge(df_programs_all, df_results_all, on=['date', 'jyo_cd', 'race_no', 'boat_no'], how='left')
    else:
        df_merged = df_programs_all
        df_merged['rank'] = None

    # Atomic Save: Write to temp then rename to avoid locking issues in FastAPI
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    temp_path = output_path + ".tmp"
    df_merged.to_csv(temp_path, index=False)
    
    if os.path.exists(output_path):
        os.remove(output_path)
    os.rename(temp_path, output_path)
    
    print(f"Dataset updated atomically: {output_path}. Shape: {df_merged.shape}")

if __name__ == "__main__":
    build_dataset()
