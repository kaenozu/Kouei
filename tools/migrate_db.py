import pandas as pd
import sys
import os
sys.path.append(os.getcwd())
from src.db.database import DatabaseData

def migrate():
    csv_path = "data/processed/race_data.csv"
    if not os.path.exists(csv_path):
        print("No CSV found to migrate.")
        return

    print(f"Loading CSV from {csv_path}...")
    df = pd.read_csv(csv_path)
    
    print("Initializing Database...")
    db = DatabaseData()
    
    print("Saving to DB (this might take a moment)...")
    db.save_races_df(df)
    
    print("Migration Complete.")

if __name__ == "__main__":
    migrate()
