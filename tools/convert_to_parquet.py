"""
Convert CSV data to Parquet format for better performance
"""
import pandas as pd
import os

def convert_csv_to_parquet():
    csv_path = "data/processed/race_data.csv"
    parquet_path = "data/processed/race_data.parquet"
    
    if not os.path.exists(csv_path):
        print(f"❌ CSV not found: {csv_path}")
        return False
    
    print(f"Loading CSV from {csv_path}...")
    df = pd.read_csv(csv_path)
    
    print(f"Converting to Parquet...")
    df.to_parquet(parquet_path, engine='pyarrow', compression='snappy')
    
    # Compare sizes
    csv_size = os.path.getsize(csv_path) / (1024 * 1024)  # MB
    parquet_size = os.path.getsize(parquet_path) / (1024 * 1024)  # MB
    
    print(f"✅ Conversion complete!")
    print(f"   CSV size: {csv_size:.2f} MB")
    print(f"   Parquet size: {parquet_size:.2f} MB")
    print(f"   Compression ratio: {csv_size/parquet_size:.1f}x")
    
    return True

if __name__ == "__main__":
    convert_csv_to_parquet()
