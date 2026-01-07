import os
import pandas as pd
from tqdm import tqdm
import warnings
from bs4 import XMLParsedAsHTMLWarning
import concurrent.futures
from typing import List, Tuple, Optional

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
from src.parser.html_parser import ProgramParser, ResultParser, BeforeInfoParser

def _process_single_race(args) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame], Optional[pd.DataFrame]]:
    """Process a single race in parallel"""
    stadium_dir, date_str, jyo_cd, race_no = args
    
    # Process program
    program_df = None
    program_path = os.path.join(stadium_dir, f"program_{race_no}.html")
    if os.path.exists(program_path):
        try:
            with open(program_path, 'r', encoding='utf-8') as f:
                program_df = ProgramParser.parse(f.read(), date_str, jyo_cd, int(race_no))
        except Exception as e:
            print(f"Error parsing program for {date_str} {jyo_cd} R{race_no}: {e}")
    
    # Process before info
    before_df = None
    before_path = os.path.join(stadium_dir, f"beforeinfo_{race_no}.html")
    if os.path.exists(before_path):
        try:
            with open(before_path, 'r', encoding='utf-8') as f:
                before_df = BeforeInfoParser.parse(f.read(), date_str, jyo_cd, int(race_no))
        except Exception as e:
            print(f"Error parsing beforeinfo for {date_str} {jyo_cd} R{race_no}: {e}")
    
    # Process result
    result_df = None
    result_path = os.path.join(stadium_dir, f"result_{race_no}.html")
    if os.path.exists(result_path):
        try:
            with open(result_path, 'r', encoding='utf-8') as f:
                result_df = ResultParser.parse(f.read(), date_str, jyo_cd, int(race_no))
        except Exception as e:
            print(f"Error parsing result for {date_str} {jyo_cd} R{race_no}: {e}")
    
    return program_df, before_df, result_df


def build_dataset(raw_dir="data/raw", output_path="data/processed/race_data.csv", max_workers=4):
    """Build dataset with parallel processing"""
    all_programs = []
    all_results = []
    all_beforeinfo = []
    
    if not os.path.exists(raw_dir):
        print(f"Raw directory {raw_dir} not found.")
        return

    dates = sorted(os.listdir(raw_dir))
    
    # Prepare all race tasks
    race_tasks = []
    for date_str in dates:
        date_dir = os.path.join(raw_dir, date_str)
        if not os.path.isdir(date_dir):
            continue
            
        stadiums = sorted(os.listdir(date_dir))
        for jyo_cd in stadiums:
            stadium_dir = os.path.join(date_dir, jyo_cd)
            if not os.path.isdir(stadium_dir):
                continue
                
            for race_no in range(1, 13):
                race_tasks.append((stadium_dir, date_str, jyo_cd, race_no))
    
    # Process races in parallel
    print(f"Processing {len(race_tasks)} races with {max_workers} workers...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Process in chunks to show progress
        chunk_size = max(1, len(race_tasks) // 100)  # Show progress every 1%
        results = []
        
        with tqdm(total=len(race_tasks), desc="Processing Races") as pbar:
            for i in range(0, len(race_tasks), chunk_size):
                chunk = race_tasks[i:i+chunk_size]
                chunk_results = list(executor.map(_process_single_race, chunk))
                results.extend(chunk_results)
                pbar.update(len(chunk))
    
    # Collect results
    for program_df, before_df, result_df in results:
        if program_df is not None:
            all_programs.append(program_df)
        if before_df is not None:
            all_beforeinfo.append(before_df)
        if result_df is not None:
            all_results.append(result_df)

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
