"""レート制限ミドルウェア"""
import time
from collections import defaultdict
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, Tuple
import asyncio

from src.utils.logger import logger


class RateLimiter:
    """シンプルなインメモリレートリミッター"""
    
    def __init__(self, requests_per_minute: int = 60, burst: int = 10):
        self.requests_per_minute = requests_per_minute
        self.burst = burst
        self.requests: Dict[str, list] = defaultdict(list)
        self._lock = asyncio.Lock()
    
    async def is_allowed(self, client_id: str) -> Tuple[bool, int]:
        """
        リクエストが許可されるかチェック
        
        Returns:
            (allowed: bool, remaining: int)
        """
        async with self._lock:
            now = time.time()
            minute_ago = now - 60
            
            # 古いリクエストを削除
            self.requests[client_id] = [
                req_time for req_time in self.requests[client_id]
                if req_time > minute_ago
            ]
            
            request_count = len(self.requests[client_id])
            remaining = max(0, self.requests_per_minute - request_count)
            
            if request_count >= self.requests_per_minute:
                return False, 0
            
            # バースト制限（短時間に大量のリクエストを防ぐ）
            recent_second = now - 1
            recent_requests = [
                req_time for req_time in self.requests[client_id]
                if req_time > recent_second
            ]
            if len(recent_requests) >= self.burst:
                return False, remaining
            
            self.requests[client_id].append(now)
            return True, remaining - 1
    
    def get_client_id(self, request: Request) -> str:
        """クライアントIDを取得"""
        # X-Forwarded-Forヘッダーを優先
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        # クライアントIP
        if request.client:
            return request.client.host
        
        return "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """レート制限ミドルウェア"""
    
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.limiter = RateLimiter(requests_per_minute=requests_per_minute)
    
    async def dispatch(self, request: Request, call_next):
        # ヘルスチェックは除外
        if request.url.path in ["/health", "/"]:
            return await call_next(request)
        
        client_id = self.limiter.get_client_id(request)
        allowed, remaining = await self.limiter.is_allowed(client_id)
        
        if not allowed:
            logger.warning(f"Rate limit exceeded for {client_id}")
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please slow down.",
                headers={"Retry-After": "60"}
            )
        
        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Limit"] = str(self.limiter.requests_per_minute)
        
        return response


# 特定のエンドポイント向けの厳しい制限
class StrictRateLimiter:
    """特定のエンドポイント用の厳しいレート制限"""
    
    STRICT_ENDPOINTS = {
        "/api/sync": 1,  # 1 request per minute
        "/api/fetch": 2,
        "/api/optimize": 1,
        "/api/mlops/retrain": 1,
    }
    
    def __init__(self):
        self.last_request: Dict[str, Dict[str, float]] = defaultdict(dict)
    
    async def check(self, request: Request) -> bool:
        path = request.url.path
        if path not in self.STRICT_ENDPOINTS:
            return True
        
        client_id = request.client.host if request.client else "unknown"
        key = f"{client_id}:{path}"
        
        now = time.time()
        limit = self.STRICT_ENDPOINTS[path]
        minute_ago = now - 60
        
        if key in self.last_request:
            last = self.last_request[key]
            recent_count = sum(1 for t in last.values() if t > minute_ago)
            if recent_count >= limit:
                return False
        
        self.last_request[key][str(now)] = now
        return True
