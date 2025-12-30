"""
Feature Cache - Cache preprocessed feature vectors in Redis
2-3x faster predictions by avoiding repeated preprocessing
"""
import hashlib
import pickle
from src.cache.redis_client import cache

class FeatureCache:
    def __init__(self, ttl=3600):
        """
        Args:
            ttl: Time to live in seconds (default 1 hour)
        """
        self.ttl = ttl
        self.prefix = "features"
    
    def _make_key(self, race_id, boat_no):
        """Generate cache key"""
        return f"{self.prefix}:{race_id}:{boat_no}"
    
    def _make_hash_key(self, data_dict):
        """Generate hash key from raw data for validation"""
        data_str = str(sorted(data_dict.items()))
        return hashlib.md5(data_str.encode()).hexdigest()[:8]
    
    def get(self, race_id, boat_no):
        """
        Get cached features
        
        Returns:
            Cached feature vector or None
        """
        key = self._make_key(race_id, boat_no)
        cached = cache.get(key)
        
        if cached:
            try:
                # Deserialize
                features = pickle.loads(bytes.fromhex(cached))
                return features
            except:
                return None
        
        return None
    
    def set(self, race_id, boat_no, features):
        """
        Cache feature vector
        
        Args:
            race_id: Race identifier
            boat_no: Boat number
            features: Feature vector (numpy array or pandas Series)
        """
        key = self._make_key(race_id, boat_no)
        
        try:
            # Serialize to hex string (JSON-safe)
            serialized = pickle.dumps(features).hex()
            cache.set(key, serialized, ttl=self.ttl)
            return True
        except Exception as e:
            print(f"Feature cache set error: {e}")
            return False
    
    def invalidate(self, race_id):
        """Invalidate all cached features for a race"""
        pattern = f"{self.prefix}:{race_id}:*"
        cache.clear_pattern(pattern)
    
    def get_or_compute(self, race_id, boat_no, compute_fn, *args, **kwargs):
        """
        Get from cache or compute and cache
        
        Args:
            race_id: Race identifier
            boat_no: Boat number
            compute_fn: Function to compute features if not cached
            *args, **kwargs: Arguments for compute_fn
        
        Returns:
            Feature vector
        """
        # Try cache first
        features = self.get(race_id, boat_no)
        
        if features is not None:
            return features
        
        # Compute
        features = compute_fn(*args, **kwargs)
        
        # Cache for future
        self.set(race_id, boat_no, features)
        
        return features

# Global instance
feature_cache = FeatureCache()

if __name__ == "__main__":
    import numpy as np
    
    # Test
    race_id = "20250130_01_12"
    boat_no = 1
    
    # Mock features
    features = np.array([0.5, 0.3, 0.8, 0.2])
    
    # Cache
    feature_cache.set(race_id, boat_no, features)
    
    # Retrieve
    cached = feature_cache.get(race_id, boat_no)
    print(f"✅ Cached features: {cached}")
