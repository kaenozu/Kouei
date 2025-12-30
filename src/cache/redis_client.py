import redis
import json
import os
from typing import Optional, Any

class RedisCache:
    def __init__(self, host='localhost', port=6379, db=0):
        try:
            self.client = redis.Redis(
                host=host, 
                port=port, 
                db=db,
                decode_responses=True,
                socket_connect_timeout=2
            )
            # Test connection
            self.client.ping()
            self.enabled = True
            print("✅ Redis connected")
        except Exception as e:
            print(f"⚠️  Redis unavailable: {e}. Running without cache.")
            self.enabled = False
            self.client = None

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.enabled:
            return None
        
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            print(f"Cache get error: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = 300):
        """Set value in cache with TTL (seconds)"""
        if not self.enabled:
            return False
        
        try:
            self.client.setex(
                key,
                ttl,
                json.dumps(value, ensure_ascii=False)
            )
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False

    def delete(self, key: str):
        """Delete key from cache"""
        if not self.enabled:
            return False
        
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False

    def clear_pattern(self, pattern: str):
        """Clear all keys matching pattern"""
        if not self.enabled:
            return False
        
        try:
            keys = self.client.keys(pattern)
            if keys:
                self.client.delete(*keys)
            return True
        except Exception as e:
            print(f"Cache clear error: {e}")
            return False

# Global instance
cache = RedisCache()
