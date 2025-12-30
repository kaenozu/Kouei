"""
Structured Logging Configuration
Outputs JSON format logs for easy parsing and monitoring
"""
import logging
import json
import sys
from datetime import datetime
from pathlib import Path

class JSONFormatter(logging.Formatter):
    """Custom formatter to output logs in JSON format"""
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, 'extra_data'):
            log_data.update(record.extra_data)
        
        return json.dumps(log_data, ensure_ascii=False)

def setup_logger(name="kyotei_ai", log_dir="logs", level=logging.INFO):
    """
    Setup structured logger with file and console handlers
    
    Args:
        name: Logger name
        log_dir: Directory for log files
        level: Logging level
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Create log directory
    Path(log_dir).mkdir(exist_ok=True)
    
    # File handler (JSON format)
    file_handler = logging.FileHandler(
        f"{log_dir}/app.log",
        encoding='utf-8'
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(JSONFormatter())
    
    # Console handler (human-readable)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Global logger instance
logger = setup_logger()

# Example usage helpers
def log_prediction(race_id, boat_no, probability, model="ensemble"):
    """Log a prediction event"""
    logger.info(
        f"Prediction: {race_id} boat {boat_no}",
        extra={'extra_data': {
            'race_id': race_id,
            'boat_no': boat_no,
            'probability': probability,
            'model': model
        }}
    )

def log_error(error_msg, context=None):
    """Log an error with context"""
    logger.error(
        error_msg,
        extra={'extra_data': context or {}},
        exc_info=True
    )

def log_api_request(endpoint, method, status_code, duration_ms):
    """Log API request"""
    logger.info(
        f"API {method} {endpoint}",
        extra={'extra_data': {
            'endpoint': endpoint,
            'method': method,
            'status_code': status_code,
            'duration_ms': duration_ms
        }}
    )

if __name__ == "__main__":
    # Test logging
    logger.info("Kyotei AI System Started")
    log_prediction("20250130_01_12", 1, 0.75)
    logger.warning("High memory usage detected")
    logger.debug("Debug information")
