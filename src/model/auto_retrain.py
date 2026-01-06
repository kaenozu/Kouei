"""自動再トレーニングパイプライン

ドリフト検出時に自動でモデルを再トレーニングするパイプライン。
データ収集 → ドリフトチェック → 再トレーニング → モデルデプロイ
"""
import asyncio
import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import subprocess

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.utils.logger import logger
from src.monitoring.drift_detector import DriftDetector


class AutoRetrainPipeline:
    """自動再トレーニングパイプライン"""
    
    def __init__(
        self,
        model_dir: str = "models",
        data_dir: str = "data",
        retrain_interval_hours: int = 24,
        drift_threshold: float = 0.05,  # p-valueの閾値
        min_samples_for_retrain: int = 1000
    ):
        self.model_dir = model_dir
        self.data_dir = data_dir
        self.retrain_interval_hours = retrain_interval_hours
        self.drift_threshold = drift_threshold
        self.min_samples_for_retrain = min_samples_for_retrain
        self.last_retrain_time: Optional[datetime] = None
        self.retrain_history_file = os.path.join(data_dir, "retrain_history.json")
        self._load_history()
    
    def _load_history(self):
        """再トレーニング履歴を読み込み"""
        if os.path.exists(self.retrain_history_file):
            try:
                with open(self.retrain_history_file, 'r') as f:
                    history = json.load(f)
                if history and 'last_retrain' in history:
                    self.last_retrain_time = datetime.fromisoformat(history['last_retrain'])
            except Exception as e:
                logger.warning(f"Failed to load retrain history: {e}")
    
    def _save_history(self, result: Dict[str, Any]):
        """再トレーニング履歴を保存"""
        history = {
            'last_retrain': datetime.now().isoformat(),
            'last_result': result
        }
        try:
            with open(self.retrain_history_file, 'w') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save retrain history: {e}")
    
    def should_retrain(self, drift_result: Dict[str, Any]) -> bool:
        """再トレーニングが必要か判定"""
        # ドリフトが検出されているか
        if not drift_result.get('drift_detected', False):
            return False
        
        # 前回の再トレーニングから十分な時間が経過しているか
        if self.last_retrain_time:
            elapsed = datetime.now() - self.last_retrain_time
            if elapsed < timedelta(hours=self.retrain_interval_hours):
                logger.info(f"Skipping retrain - last retrain was {elapsed} ago")
                return False
        
        # 重大なドリフトかチェック
        metrics = drift_result.get('metrics', {})
        critical_drift_count = 0
        for feature, result in metrics.items():
            if result.get('drift', False) and result.get('p_value', 1) < 0.001:
                critical_drift_count += 1
        
        if critical_drift_count >= 2:
            logger.warning(f"Critical drift detected in {critical_drift_count} features")
            return True
        
        return False
    
    async def run_retrain(self) -> Dict[str, Any]:
        """モデルの再トレーニングを実行"""
        logger.info("🚀 Starting auto-retrain pipeline...")
        result = {
            'started_at': datetime.now().isoformat(),
            'success': False,
            'message': '',
            'metrics': {}
        }
        
        try:
            # train_v3.pyを実行
            process = await asyncio.create_subprocess_exec(
                'python', '-m', 'src.model.train_v3',
                cwd=os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                result['success'] = True
                result['message'] = "Retrain completed successfully"
                self.last_retrain_time = datetime.now()
                
                # メトリクスを読み込み
                metadata_file = os.path.join(self.model_dir, "training_metadata_v3.json")
                if os.path.exists(metadata_file):
                    with open(metadata_file, 'r') as f:
                        result['metrics'] = json.load(f)
                
                logger.info("✅ Auto-retrain completed successfully")
            else:
                result['message'] = f"Retrain failed: {stderr.decode()}"
                logger.error(f"❌ Auto-retrain failed: {stderr.decode()}")
        
        except Exception as e:
            result['message'] = f"Retrain error: {str(e)}"
            logger.error(f"❌ Auto-retrain error: {e}")
        
        result['completed_at'] = datetime.now().isoformat()
        self._save_history(result)
        return result
    
    async def check_and_retrain(self) -> Dict[str, Any]:
        """ドリフトをチェックし、必要であれば再トレーニング"""
        try:
            # ドリフトチェック
            detector = DriftDetector()
            drift_result = detector.check_drift()
            
            if self.should_retrain(drift_result):
                logger.info("Drift detected - triggering auto-retrain")
                return await self.run_retrain()
            else:
                return {
                    'action': 'skip',
                    'reason': 'No significant drift detected',
                    'drift_result': drift_result
                }
        except Exception as e:
            logger.error(f"Check and retrain failed: {e}")
            return {
                'action': 'error',
                'error': str(e)
            }


# グローバルインスタンス
_pipeline: Optional[AutoRetrainPipeline] = None


def get_auto_retrain_pipeline() -> AutoRetrainPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = AutoRetrainPipeline()
    return _pipeline


async def run_auto_retrain_check():
    """定期実行用のエントリポイント"""
    pipeline = get_auto_retrain_pipeline()
    return await pipeline.check_and_retrain()


if __name__ == "__main__":
    # テスト実行
    result = asyncio.run(run_auto_retrain_check())
    print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
