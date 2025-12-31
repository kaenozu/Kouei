"""
Vector DB Manager (Phase 14)
Handles high-performance similarity search for historical races.
Can be upgraded to FAISS if needed, current implementation uses optimized matrix operations.
"""
import pandas as pd
import numpy as np
import os
import joblib
from pathlib import Path

INDEX_PATH = "models/vector_index.joblib"
DATA_PATH = "data/processed/race_data.csv"

class VectorDBManager:
    def __init__(self, data_path=DATA_PATH):
        self.data_path = data_path
        self.features = ['jyo_cd', 'wind_speed', 'wave_height', 'temperature', 'water_temperature']
        self.index = None
        self.metadata = None

    def build_index(self):
        """Builds a flattened vector index from processed data."""
        if not os.path.exists(self.data_path):
            print("⚠️ Data source not found for indexing.")
            return False
            
        df = pd.read_csv(self.data_path)
        if df.empty: return False
        
        # Keep only numeric features for indexing
        # Fill NaNs with mean/zero
        df_feat = df[self.features].fillna(0).apply(pd.to_numeric)
        
        # Normalize features for better similarity (Euclidean distance works better on normalized scales)
        # Simple Min-Max or standard scaling
        mean = df_feat.mean()
        std = df_feat.std().replace(0, 1)
        normalized_data = (df_feat - mean) / std
        
        self.index = normalized_data.values.astype('float32')
        self.metadata = df.to_dict(orient='records') # Store full metadata for RAG retrieval
        self.scaling_params = {'mean': mean.tolist(), 'std': std.tolist()}
        
        # Save index to disk
        joblib.dump({
            'index': self.index,
            'metadata': self.metadata,
            'scaling': self.scaling_params,
            'features': self.features
        }, INDEX_PATH)
        
        print(f"✅ Vector index built with {len(self.index)} entries.")
        return True

    def load_index(self):
        """Loads index from disk."""
        if not os.path.exists(INDEX_PATH):
            return self.build_index()
            
        data = joblib.load(INDEX_PATH)
        self.index = data['index']
        self.metadata = data['metadata']
        self.scaling_params = data['scaling']
        self.features = data['features']
        return True

    def search(self, target_features, top_k=5):
        """Perform fast similarity search."""
        if self.index is None:
            if not self.load_index(): return []
            
        # Prepare target vector
        vec = []
        for f in self.features:
            val = float(target_features.get(f, 0))
            idx_f = self.features.index(f)
            # Scale target vector using same params
            norm_val = (val - self.scaling_params['mean'][idx_f]) / self.scaling_params['std'][idx_f]
            vec.append(norm_val)
            
        target_vec = np.array(vec, dtype='float32')
        
        # Compute distances (Matrix subtraction + norm)
        diff = self.index - target_vec
        dists = np.sqrt(np.sum(diff**2, axis=1))
        
        # Get top K indices
        top_indices = np.argsort(dists)[:top_k]
        
        results = []
        for i in top_indices:
            meta = self.metadata[i].copy()
            meta['similarity_score'] = float(1 / (1 + dists[i]))
            # Replace any NaN/inf values with None to ensure JSON compliance
            for key, value in meta.items():
                if isinstance(value, float) and (np.isnan(value) or np.isinf(value)):
                    meta[key] = None
                elif pd.isna(value):
                    meta[key] = None
            results.append(meta)
            
        return results

# Singleton implementation
vector_db = VectorDBManager()

if __name__ == "__main__":
    # Test build and search
    mgr = VectorDBManager()
    if mgr.build_index():
        sample_query = {'jyo_cd': 2, 'wind_speed': 3.0, 'wave_height': 1.0, 'temperature': 20.0, 'water_temperature': 18.0}
        res = mgr.search(sample_query)
        print(f"Search results for {sample_query}:")
        for r in res:
            print(f"- {r['date']} {r['jyo_cd']} {r['race_no']}R (Sim: {r['similarity_score']:.3f})")
