"""
Enhanced Error Handler - Comprehensive error handling and logging system
"""
import logging
import traceback
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from functools import wraps
import json
from pathlib import Path


class EnhancedErrorHandler:
    """強化されたエラーハンドリング"""
    
    def __init__(self, log_file: str = "logs/errors.log"):
        self.log_file = log_file
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        
        # ログ設定
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger('kouei')
    
    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """例外処理ハンドラ"""
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        error_info = {
            'timestamp': datetime.now().isoformat(),
            'type': str(exc_type.__name__),
            'message': str(exc_value),
            'traceback': ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback)),
            'severity': 'critical'
        }
        
        self.logger.critical(f"Unhandled exception: {error_info}")
        self._save_error_report(error_info)
    
    def _save_error_report(self, error_info: Dict):
        """エラーレポートを保存"""
        try:
            error_dir = Path("data/errors")
            error_dir.mkdir(parents=True, exist_ok=True)
            
            filename = f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filepath = error_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(error_info, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Failed to save error report: {e}")


def handle_errors(func):
    """エラーハンドリングデコレータ"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger = logging.getLogger('kouei')
            logger.error(f"Error in {func.__name__}: {str(e)}")
            logger.debug(traceback.format_exc())
            
            # ユーザー向けエラーメッセージ
            error_messages = {
                'ValueError': '入力値が不正です',
                'KeyError': '必要なデータが見つかりません',
                'ConnectionError': '接続エラーが発生しました',
                'TimeoutError': '処理がタイムアウトしました'
            }
            
            error_type = type(e).__name__
            user_message = error_messages.get(error_type, f'予期せぬエラーが発生しました: {str(e)}')
            
            raise Exception(f"Error in {func.__name__}: {user_message}")
    
    return wrapper


async def safe_execute(func, *args, **kwargs):
    """安全な実行ラッパー（非同期）"""
    try:
        return await func(*args, **kwargs)
    except Exception as e:
        logger = logging.getLogger('kouei')
        logger.error(f"Async error in {func.__name__}: {str(e)}")
        return None


def safe_execute_sync(func, *args, **kwargs):
    """安全な実行ラッパー（同期）"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger = logging.getLogger('kouei')
        logger.error(f"Sync error in {func.__name__}: {str(e)}")
        return None


# グローバルエラーハンドラ設定
error_handler = EnhancedErrorHandler()
sys.excepthook = error_handler.handle_exception
