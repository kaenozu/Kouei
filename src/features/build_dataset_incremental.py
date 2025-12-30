"""Incremental Dataset Builder - Only process new/changed data"""
import os
import json
import pandas as pd
from datetime import datetime
from tqdm import tqdm
import warnings
from bs4 import XMLParsedAsHTMLWarning
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

from src.parser.html_parser import ProgramParser, ResultParser, BeforeInfoParser


METADATA_PATH = "data/processed/.build_metadata.json"


def load_metadata():
    """Load build metadata"""
    if os.path.exists(METADATA_PATH):
        with open(METADATA_PATH, 'r') as f:
            return json.load(f)
    return {"processed_files": {}, "last_build": None}


def save_metadata(metadata):
    """Save build metadata"""
    os.makedirs(os.path.dirname(METADATA_PATH), exist_ok=True)
    with open(METADATA_PATH, 'w') as f:
        json.dump(metadata, f)


def get_file_hash(path):
    """Get file modification time as hash"""
    if os.path.exists(path):
        return os.path.getmtime(path)
    return None


def process_single_race(stadium_dir, date_str, jyo_cd, race_no):
    """Process a single race and return dataframes"""
    program_df = None
    before_df = None
    result_df = None
    
    program_path = os.path.join(stadium_dir, f"program_{race_no}.html")
    if os.path.exists(program_path):
        with open(program_path, 'r', encoding='utf-8') as f:
            program_df = ProgramParser.parse(f.read(), date_str, jyo_cd, int(race_no))
    
    before_path = os.path.join(stadium_dir, f"beforeinfo_{race_no}.html")
    if os.path.exists(before_path):
        with open(before_path, 'r', encoding='utf-8') as f:
            before_df = BeforeInfoParser.parse(f.read(), date_str, jyo_cd, int(race_no))
    
    result_path = os.path.join(stadium_dir, f"result_{race_no}.html")
    if os.path.exists(result_path):
        with open(result_path, 'r', encoding='utf-8') as f:
            result_df = ResultParser.parse(f.read(), date_str, jyo_cd, int(race_no))
    
    return program_df, before_df, result_df


def build_dataset_incremental(raw_dir="data/raw", output_path="data/processed/race_data.csv", force_full=False):
    """Build dataset incrementally - only process changed files"""
    metadata = load_metadata()
    processed_files = metadata.get("processed_files", {})
    
    if not os.path.exists(raw_dir):
        print(f"Raw directory {raw_dir} not found.")
        return
    
    # Load existing dataset if incremental
    existing_df = None
    if not force_full and os.path.exists(output_path):
        existing_df = pd.read_csv(output_path)
        print(f"Loaded existing dataset: {len(existing_df)} rows")
    
    dates = sorted(os.listdir(raw_dir))
    
    new_programs = []
    new_beforeinfo = []
    new_results = []
    changed_keys = set()
    
    for date_str in tqdm(dates, desc="Scanning dates"):
        date_dir = os.path.join(raw_dir, date_str)
        if not os.path.isdir(date_dir):
            continue
        
        stadiums = sorted(os.listdir(date_dir))
        for jyo_cd in stadiums:
            stadium_dir = os.path.join(date_dir, jyo_cd)
            if not os.path.isdir(stadium_dir):
                continue
            
            for race_no in range(1, 13):
                # Check if any file changed
                key = f"{date_str}/{jyo_cd}/{race_no}"
                files_to_check = [
                    os.path.join(stadium_dir, f"program_{race_no}.html"),
                    os.path.join(stadium_dir, f"beforeinfo_{race_no}.html"),
                    os.path.join(stadium_dir, f"result_{race_no}.html"),
                ]
                
                current_hashes = {f: get_file_hash(f) for f in files_to_check}
                stored_hashes = processed_files.get(key, {})
                
                # Check if any file is new or changed
                needs_processing = force_full
                for f, h in current_hashes.items():
                    if h is not None and stored_hashes.get(f) != h:
                        needs_processing = True
                        break
                
                if needs_processing:
                    changed_keys.add(key)
                    program_df, before_df, result_df = process_single_race(
                        stadium_dir, date_str, jyo_cd, race_no
                    )
                    
                    if program_df is not None:
                        new_programs.append(program_df)
                    if before_df is not None:
                        new_beforeinfo.append(before_df)
                    if result_df is not None:
                        new_results.append(result_df)
                    
                    # Update metadata
                    processed_files[key] = current_hashes
    
    if not changed_keys:
        print("No changes detected. Dataset is up to date.")
        return
    
    print(f"Processing {len(changed_keys)} changed races...")
    
    # Build new data
    if new_programs:
        df_programs_new = pd.concat(new_programs, ignore_index=True)
        df_programs_new['race_no'] = df_programs_new['race_no'].astype(int)
        df_programs_new['boat_no'] = df_programs_new['boat_no'].astype(int)
        df_programs_new['jyo_cd'] = df_programs_new['jyo_cd'].astype(str)
        
        if new_beforeinfo:
            df_before_new = pd.concat(new_beforeinfo, ignore_index=True)
            df_before_new['race_no'] = df_before_new['race_no'].astype(int)
            df_before_new['boat_no'] = df_before_new['boat_no'].astype(int)
            df_before_new['jyo_cd'] = df_before_new['jyo_cd'].astype(str)
            df_programs_new = pd.merge(df_programs_new, df_before_new, 
                                       on=['date', 'jyo_cd', 'race_no', 'boat_no'], how='left')
        
        if new_results:
            df_results_new = pd.concat(new_results, ignore_index=True)
            df_results_new['race_no'] = df_results_new['race_no'].astype(int)
            df_results_new['boat_no'] = df_results_new['boat_no'].astype(int)
            df_results_new['jyo_cd'] = df_results_new['jyo_cd'].astype(str)
            df_new = pd.merge(df_programs_new, df_results_new,
                             on=['date', 'jyo_cd', 'race_no', 'boat_no'], how='left')
        else:
            df_new = df_programs_new
            df_new['rank'] = None
        
        # Merge with existing data
        if existing_df is not None:
            # Remove changed rows from existing
            existing_df['_key'] = existing_df['date'].astype(str) + '/' + \
                                  existing_df['jyo_cd'].astype(str) + '/' + \
                                  existing_df['race_no'].astype(str)
            existing_df = existing_df[~existing_df['_key'].isin(changed_keys)]
            existing_df = existing_df.drop(columns=['_key'])
            
            # Combine
            df_merged = pd.concat([existing_df, df_new], ignore_index=True)
        else:
            df_merged = df_new
        
        # Sort
        df_merged = df_merged.sort_values(['date', 'jyo_cd', 'race_no', 'boat_no'])
        
        # Atomic save
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        temp_path = output_path + ".tmp"
        df_merged.to_csv(temp_path, index=False)
        
        if os.path.exists(output_path):
            os.remove(output_path)
        os.rename(temp_path, output_path)
        
        # Save metadata
        metadata["processed_files"] = processed_files
        metadata["last_build"] = datetime.now().isoformat()
        save_metadata(metadata)
        
        print(f"Dataset updated: {output_path}. Shape: {df_merged.shape}")
    else:
        print("No new program data to process.")


if __name__ == "__main__":
    import sys
    force = "--force" in sys.argv
    build_dataset_incremental(force_full=force)
