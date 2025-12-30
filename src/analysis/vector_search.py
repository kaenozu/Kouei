"""
Vector Search - Similar Race Finder
Uses basic feature parity to find races with similar conditions (stadium, wind, humidity, boat rank)
"""
import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path

DB_PATH = "data/race_data.db"

class VectorSearch:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
    
    def _load_data(self, limit=5000):
        """Load recent race data for comparison"""
        if not Path(self.db_path).exists():
            return None
            
        conn = sqlite3.connect(self.db_path)
        query = f"SELECT * FROM races ORDER BY date DESC LIMIT {limit}"
        df = pd.read_sql(query, conn)
        conn.close()
        return df

    def find_similar_races(self, target_features, n_neighbors=5):
        """
        Find N races most similar to the provided feature vector
        
        Args:
            target_features (dict): Dictionary of features for the current race
            n_neighbors (int): Number of similar races to return
            
        Returns:
            DataFrame: Top N similar races
        """
        df = self._load_data()
        if df is None or df.empty:
            return pd.DataFrame()
        
        # Feature columns to use for similarity
        # We'll use: jyo_cd, wind_speed, wave_height
        features = ['jyo_cd', 'wind_speed', 'wave_height']
        
        # Ensure all columns exist
        available_features = [f for f in features if f in df.columns]
        if not available_features:
            return pd.DataFrame()
            
        # Convert to numpy for fast distance calculation
        # Ensure numeric types
        data_matrix = df[available_features].fillna(0).apply(pd.to_numeric).values
        
        # Prepare target vector
        target_vec = np.array([float(target_features.get(f, 0)) for f in available_features])
        
        # Calculate Euclidean distance
        distances = np.linalg.norm(data_matrix - target_vec, axis=1)
        
        # Get top indices
        top_indices = np.argsort(distances)[:n_neighbors]
        
        result = df.iloc[top_indices].copy()
        result['similarity_score'] = 1 / (1 + distances[top_indices])
        
        return result

# Global instance
race_finder = VectorSearch()

if __name__ == "__main__":
    # Test
    target = {
        'jyo_cd': '02',
        'wind_speed': 3.0,
        'wave_height': 2.0
    }
    
    print(f"Finding similar races for: {target}")
    similar = race_finder.find_similar_races(target)
    
    if not similar.empty:
        print("\n✅ Top Similar Races:")
        for _, row in similar.iterrows():
            print(f"- {row['date']} {row['jyo_cd']} {row['race_no']}R (Sim: {row['similarity_score']:.3f})")
    else:
        print("❌ No data found for comparison")
