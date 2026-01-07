"""Structured Logging with JSON format support"""
import logging
import sys
import json
from datetime import datetime
from typing import Any, Optional
import traceback
from functools import wraps
import time


class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add extra fields
        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info) if record.exc_info[0] else None
            }
        
        return json.dumps(log_data, ensure_ascii=False, default=str)


class PrettyFormatter(logging.Formatter):
    """Human-readable formatter for development"""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, '')
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # Format extra data if present
        extra = ""
        if hasattr(record, 'extra_data') and record.extra_data:
            extra = f" | {record.extra_data}"
        
        return f"{color}[{timestamp}] {record.levelname:8}{self.RESET} {record.name}: {record.getMessage()}{extra}"


class StructuredLogger:
    """Enhanced logger with structured logging support"""
    
    def __init__(self, name: str = "kouei", json_format: bool = False, level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        self.logger.handlers = []  # Clear existing handlers
        
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(level)
        
        if json_format:
            handler.setFormatter(JSONFormatter())
        else:
            handler.setFormatter(PrettyFormatter())
        
        self.logger.addHandler(handler)
    
    def _log(self, level: int, message: str, **kwargs):
        """Internal log method with extra data support"""
        extra = {'extra_data': kwargs} if kwargs else {}
        self.logger.log(level, message, extra=extra)
    
    def debug(self, message: str, **kwargs):
        self._log(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        self._log(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        self._log(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        self._log(logging.CRITICAL, message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log exception with traceback"""
        self.logger.exception(message, extra={'extra_data': kwargs})


def log_execution_time(logger: Optional[StructuredLogger] = None):
    """Decorator to log function execution time"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            elapsed = time.time() - start
            
            log = logger or get_logger()
            log.debug(
                f"{func.__name__} completed",
                duration_ms=round(elapsed * 1000, 2),
                function=func.__name__
            )
            return result
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            result = await func(*args, **kwargs)
            elapsed = time.time() - start
            
            log = logger or get_logger()
            log.debug(
                f"{func.__name__} completed",
                duration_ms=round(elapsed * 1000, 2),
                function=func.__name__
            )
            return result
        
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper
    return decorator


def log_api_request(logger: Optional[StructuredLogger] = None):
    """Decorator for API endpoint logging"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start = time.time()
            log = logger or get_logger()
            
            try:
                result = await func(*args, **kwargs)
                elapsed = time.time() - start
                
                log.info(
                    f"API {func.__name__}",
                    endpoint=func.__name__,
                    duration_ms=round(elapsed * 1000, 2),
                    status="success"
                )
                return result
            except Exception as e:
                elapsed = time.time() - start
                log.error(
                    f"API {func.__name__} failed",
                    endpoint=func.__name__,
                    duration_ms=round(elapsed * 1000, 2),
                    status="error",
                    error=str(e)
                )
                raise
        return wrapper
    return decorator


# Global logger instance
_logger: Optional[StructuredLogger] = None


def get_logger(name: str = "kouei", json_format: bool = False) -> StructuredLogger:
    """Get or create global logger instance"""
    global _logger
    if _logger is None:
        import os
        json_format = os.environ.get("LOG_FORMAT", "pretty").lower() == "json"
        level = logging.DEBUG if os.environ.get("DEBUG", "false").lower() == "true" else logging.INFO
        _logger = StructuredLogger(name=name, json_format=json_format, level=level)
    return _logger


# Convenience alias
logger = get_logger()
