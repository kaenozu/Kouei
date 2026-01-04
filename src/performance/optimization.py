"""Performance optimization utilities"""
import asyncio
import time
import functools
from typing import Any, Callable, Dict, List
import pandas as pd
import numpy as np
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import redis
import pickle
from datetime import datetime, timedelta
import logging

class PerformanceMonitor:
    def __init__(self):
        self.metrics = {
            'start_time': None,
            'end_time': None,
            'execution_time': 0,
            'memory_usage': 0,
            'cache_hits': 0,
            'cache_misses': 0
        }
    
    def __enter__(self):
        self.metrics['start_time'] = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.metrics['end_time'] = time.time()
        self.metrics['execution_time'] = self.metrics['end_time'] - self.metrics['start_time']
        
        # Log performance if enabled
        if self.metrics['execution_time'] > 1.0:  # Log if > 1 second
            logging.info(f"Slow operation: {self.metrics['execution_time']:.2f}s")

def performance_monitor(func: Callable) -> Callable:
    """Decorator to monitor function performance"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            if execution_time > 0.5:  # Log slow operations
                logging.warning(f"Slow function {func.__name__}: {execution_time:.2f}s")
            
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logging.error(f"Function {func.__name__} failed after {execution_time:.2f}s: {e}")
            raise
    return wrapper

class CacheManager:
    """Async cache manager using Redis"""
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        try:
            self.redis_client = redis.from_url(redis_url)
            self.enabled = True
        except Exception:
            self.enabled = False
            logging.warning("Redis not available, cache disabled")
            self.redis_client = None
    
    async def get(self, key: str) -> Any:
        """Get value from cache"""
        if not self.enabled:
            return None
            
        try:
            value = self.redis_client.get(key)
            return pickle.loads(value) if value else None
        except Exception as e:
            logging.error(f"Cache get error: {e}")
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600):
        """Set value in cache with TTL"""
        if not self.enabled:
            return False
            
        try:
            serialized = pickle.dumps(value)
            self.redis_client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logging.error(f"Cache set error: {e}")
            return False
    
    async def invalidate(self, pattern: str = "*"):
        """Invalidate cache entries matching pattern"""
        if not self.enabled:
            return
            
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
        except Exception as e:
            logging.error(f"Cache invalidation error: {e}")

class BatchProcessor:
    """Efficient batch processing for large datasets"""
    def __init__(self, batch_size: int = 1000, max_workers: int = 4):
        self.batch_size = batch_size
        self.max_workers = max_workers
    
    def process_batches(self, data: pd.DataFrame, processor_func: Callable) -> List[Any]:
        """Process data in batches using multiprocessing"""
        batches = [
            data.iloc[i:i + self.batch_size] 
            for i in range(0, len(data), self.batch_size)
        ]
        
        results = []
        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(processor_func, batch) for batch in batches]
            for future in futures:
                try:
                    result = future.result(timeout=300)  # 5 minute timeout
                    results.append(result)
                except Exception as e:
                    logging.error(f"Batch processing error: {e}")
        
        return results
    
    async def process_async_batches(self, data: pd.DataFrame, processor_func: Callable) -> List[Any]:
        """Process data in batches using async processing"""
        batches = [
            data.iloc[i:i + self.batch_size] 
            for i in range(0, len(data), self.batch_size)
        ]
        
        tasks = [self._process_batch_async(batch, processor_func) for batch in batches]
        results = await asyncio.gather(*tasks)
        
        return results
    
    async def _process_batch_async(self, batch: pd.DataFrame, processor_func: Callable) -> Any:
        """Process single batch asynchronously"""
        loop = asyncio.get_event_loop()
        
        with ThreadPoolExecutor() as executor:
            return await loop.run_in_executor(executor, processor_func, batch)

class MemoryOptimizer:
    """Memory optimization utilities"""
    
    @staticmethod
    def optimize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Optimize DataFrame memory usage"""
        for col in df.columns:
            col_type = df[col].dtype
            
            if col_type == 'object':
                if df[col].nunique() / len(df[col]) < 0.5:
                    # Convert to category if low cardinality
                    df[col] = df[col].astype('category')
            elif col_type == 'int64':
                if df[col].min() >= 0:
                    if df[col].max() < 255:
                        df[col] = df[col].astype('uint8')
                    elif df[col].max() < 65535:
                        df[col] = df[col].astype('uint16')
                    elif df[col].max() < 4294967295:
                        df[col] = df[col].astype('uint32')
            elif col_type == 'float64':
                df[col] = pd.to_numeric(df[col], downcast='float')
        
        return df
    
    @staticmethod
    def batch_process_large_dataframe(df: pd.DataFrame, chunk_size: int = 10000) -> pd.DataFrame:
        """Process large DataFrame in chunks to manage memory"""
        results = []
        
        for i in range(0, len(df), chunk_size):
            chunk = df.iloc[i:i + chunk_size]
            
            # Process chunk (add your processing logic here)
            processed_chunk = chunk.copy()
            results.append(processed_chunk)
        
        return pd.concat(results, ignore_index=True)

class QueryOptimizer:
    """Database query optimization"""
    
    @staticmethod
    def build_optimized_query(table: str, filters: Dict[str, Any], 
                             columns: List[str] = None,
                             limit: int = None) -> str:
        """Build optimized SQL query"""
        
        basic_query = f"SELECT {','.join(columns) if columns else '*'} FROM {table}"
        
        # Add WHERE clauses if filters exist
        if filters:
            where_clauses = []
            for key, value in filters.items():
                if isinstance(value, str):
                    where_clauses.append(f"{key} = '{value}'")
                else:
                    where_clauses.append(f"{key} = {value}")
            
            if where_clauses:
                basic_query += f" WHERE {' AND '.join(where_clauses)}"
        
        # Add LIMIT if specified
        if limit:
            basic_query += f" LIMIT {limit}"
        
        return basic_query
    
    @staticmethod
    def create_indexes(conn, table: str, columns: List[str]):
        """Create database indexes for performance"""
        cursor = conn.cursor()
        
        for column in columns:
            index_name = f"idx_{table}_{column}"
            try:
                cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table}({column})")
            except Exception as e:
                logging.warning(f"Failed to create index {index_name}: {e}")
        
        conn.commit()

class AsyncModelPredictor:
    """Async model prediction with connection pooling"""
    
    def __init__(self, model_path: str, pool_size: int = 5):
        self.model_path = model_path
        self.pool_size = pool_size
        self.model_pool = asyncio.Queue(maxsize=pool_size)
        self._initialized = False
    
    async def initialize(self):
        """Initialize model pool"""
        if self._initialized:
            return
            
        for _ in range(self.pool_size):
            model = await self._load_model()
            await self.model_pool.put(model)
        
        self._initialized = True
    
    async def _load_model(self):
        """Load model (async wrapper for synchronous operation)"""
        loop = asyncio.get_event_loop()
        
        def load_model_sync():
            import lightgbm as lgb
            return lgb.Booster(model_file=self.model_path)
        
        return await loop.run_in_executor(None, load_model_sync)
    
    async def predict(self, data: pd.DataFrame) -> np.ndarray:
        """Make predictions using pooled model"""
        if not self._initialized:
            await self.initialize()
        
        model = await self.model_pool.get()
        try:
            loop = asyncio.get_event_loop()
            prediction = await loop.run_in_executor(None, model.predict, data)
            return prediction
        finally:
            await self.model_pool.put(model)

# Global instances
cache_manager = CacheManager()
batch_processor = BatchProcessor()
memory_optimizer = MemoryOptimizer()
query_optimizer = QueryOptimizer()

# Utility functions
def async_cache(ttl: int = 3600):
    """Async caching decorator"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache_manager.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator