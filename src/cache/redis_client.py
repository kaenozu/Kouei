import redis
import json
import os
import socket
from typing import Optional, Any, Dict
from datetime import datetime

class RedisCache:
    def __init__(self, host='localhost', port=6379, db=0):
        try:
            self.client = redis.Redis(
                host=host, 
                port=port, 
                db=db,
                decode_responses=True,
                socket_connect_timeout=2,
                socket_keepalive=True,
                socket_keepalive_options={socket.TCP_KEEPIDLE: 30, socket.TCP_KEEPINTVL: 5, socket.TCP_KEEPCNT: 3}
            )
            # Test connection
            self.client.ping()
            self.enabled = True
            print("✅ Redis connected")
            
            # Cache statistics
            self.stats = {
                "hits": 0,
                "misses": 0,
                "sets": 0,
                "errors": 0
            }
        except Exception as e:
            print(f"⚠️  Redis unavailable: {e}. Running without cache.")
            self.enabled = False
            self.client = None
            self.stats = {}

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.enabled:
            return None
        
        try:
            value = self.client.get(key)
            if value:
                self.stats["hits"] += 1
                return json.loads(value)
            else:
                self.stats["misses"] += 1
                return None
        except Exception as e:
            self.stats["errors"] += 1
            print(f"Cache get error: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = 300):
        """Set value in cache with TTL (seconds)"""
        if not self.enabled:
            return False
        
        try:
            # Use pipeline for better performance
            pipe = self.client.pipeline()
            pipe.setex(
                key,
                ttl,
                json.dumps(value, ensure_ascii=False, default=str)
            )
            pipe.execute()
            self.stats["sets"] += 1
            return True
        except Exception as e:
            self.stats["errors"] += 1
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
            self.stats["errors"] += 1
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
            self.stats["errors"] += 1
            print(f"Cache clear error: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.enabled:
            return {}
        
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "sets": self.stats["sets"],
            "errors": self.stats["errors"],
            "hit_rate": round(hit_rate, 2),
            "total_requests": total_requests,
            "timestamp": datetime.now().isoformat()
        }
    
    def reset_stats(self):
        """Reset cache statistics"""
        if self.enabled:
            self.stats = {
                "hits": 0,
                "misses": 0,
                "sets": 0,
                "errors": 0
            }

# Global instance
cache = RedisCache()

# Global instance
cache = RedisCache()
