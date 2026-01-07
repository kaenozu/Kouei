"""
Performance Optimizer - System performance enhancement utilities
"""
import asyncio
import time
import functools
from typing import Any, Callable
import logging

logger = logging.getLogger(__name__)


def async_lru_cache(maxsize=128):
    """Async LRUキャッシュデコレータ"""
    def decorator(func):
        cache = {}
        lock = asyncio.Lock()
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            key = str(args) + str(sorted(kwargs.items()))
            
            async with lock:
                if key in cache:
                    return cache[key]
            
            result = await func(*args, **kwargs)
            
            async with lock:
                if len(cache) >= maxsize:
                    # 最も古いエントリを削除
                    oldest_key = next(iter(cache))
                    del cache[oldest_key]
                cache[key] = result
            
            return result
        
        return wrapper
    return decorator


def timed_cache(seconds: int):
    """時間ベースキャッシュデコレータ"""
    def decorator(func):
        cache = {}
        lock = asyncio.Lock()
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            key = str(args) + str(sorted(kwargs.items()))
            now = time.time()
            
            async with lock:
                if key in cache:
                    result, timestamp = cache[key]
                    if now - timestamp < seconds:
                        return result
                    else:
                        del cache[key]
            
            result = await func(*args, **kwargs)
            
            async with lock:
                cache[key] = (result, now)
            
            return result
        
        return wrapper
    return decorator


def batch_processor(batch_size: int = 100):
    """バッチ処理デコレータ"""
    def decorator(func):
        queue = []
        lock = asyncio.Lock()
        task = None
        
        @functools.wraps(func)
        async def wrapper(item):
            async with lock:
                queue.append(item)
                
                # バッチサイズに達したら処理
                if len(queue) >= batch_size:
                    items = queue[:batch_size]
                    queue[:] = queue[batch_size:]
                    
                    # バックグラウンドで処理
                    asyncio.create_task(_process_batch(func, items))
            
            return None  # バッチ処理の結果は別途取得
        
        async def _process_batch(func, items):
            try:
                await func(items)
            except Exception as e:
                logger.error(f"Batch processing error: {e}")
        
        return wrapper
    return decorator


class PerformanceMonitor:
    """パフォーマンスモニター"""
    
    def __init__(self):
        self.metrics = {}
    
    def track_time(self, name: str):
        """時間計測デコレータ"""
        def decorator(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                start = time.time()
                try:
                    result = await func(*args, **kwargs)
                    return result
                finally:
                    duration = time.time() - start
                    self._record_metric(name, duration)
            
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                start = time.time()
                try:
                    result = func(*args, **kwargs)
                    return result
                finally:
                    duration = time.time() - start
                    self._record_metric(name, duration)
            
            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
        return decorator
    
    def _record_metric(self, name: str, duration: float):
        """メトリクス記録"""
        if name not in self.metrics:
            self.metrics[name] = {
                'count': 0,
                'total_time': 0,
                'min_time': float('inf'),
                'max_time': 0
            }
        
        metric = self.metrics[name]
        metric['count'] += 1
        metric['total_time'] += duration
        metric['min_time'] = min(metric['min_time'], duration)
        metric['max_time'] = max(metric['max_time'], duration)
    
    def get_metrics(self):
        """メトリクス取得"""
        result = {}
        for name, data in self.metrics.items():
            if data['count'] > 0:
                result[name] = {
                    'count': data['count'],
                    'avg_time': data['total_time'] / data['count'],
                    'min_time': data['min_time'],
                    'max_time': data['max_time'],
                    'total_time': data['total_time']
                }
        return result
    
    def reset_metrics(self):
        """メトリクスリセット"""
        self.metrics.clear()


# グローバルインスタンス
perf_monitor = PerformanceMonitor()
