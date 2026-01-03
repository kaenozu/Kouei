"""
Accuracy Monitor - Real-time model accuracy monitoring system
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import sqlite3
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class AccuracyMonitor:
    """精度監視システム"""
    
    def __init__(self, db_path: str = "data/accuracy_monitor.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """精度監視用データベース初期化"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 予測精度テーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prediction_accuracy (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                jyo_cd TEXT,
                race_no INTEGER,
                boat_no INTEGER,
                predicted_prob REAL,
                actual_rank INTEGER,
                predicted_hit BOOLEAN,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                model_version TEXT DEFAULT 'v3.0'
            )
        """)
        
        # 日次サマリーテーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_summary (
                date TEXT PRIMARY KEY,
                total_predictions INTEGER,
                correct_predictions INTEGER,
                hit_rate REAL,
                avg_confidence REAL,
                roi REAL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # モデルドリフト監視テーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_drift (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                metric_name TEXT,
                current_value REAL,
                baseline_value REAL,
                drift_detected BOOLEAN,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def record_prediction(self, 
                         date: str,
                         jyo_cd: str, 
                         race_no: int,
                         boat_no: int,
                         predicted_prob: float,
                         actual_rank: int) -> bool:
        """予測結果を記録"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            predicted_hit = (actual_rank == 1)
            
            cursor.execute("""
                INSERT INTO prediction_accuracy 
                (date, jyo_cd, race_no, boat_no, predicted_prob, actual_rank, predicted_hit)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (date, jyo_cd, race_no, boat_no, predicted_prob, actual_rank, predicted_hit))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Recorded prediction: {date}-{jyo_cd}-{race_no}-{boat_no}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to record prediction: {e}")
            return False
    
    def update_daily_summary(self, date: str):
        """日次サマリーを更新"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # 日次集計
            cursor.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(predicted_hit) as correct,
                    AVG(predicted_prob) as avg_conf
                FROM prediction_accuracy 
                WHERE date = ?
            """, (date,))
            
            result = cursor.fetchone()
            total, correct, avg_conf = result or (0, 0, 0)
            
            if total > 0:
                hit_rate = (correct / total) * 100
                
                # ROI計算
                roi = self._calculate_daily_roi(date)
                
                cursor.execute("""
                    INSERT OR REPLACE INTO daily_summary 
                    (date, total_predictions, correct_predictions, hit_rate, avg_confidence, roi)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (date, total, correct, hit_rate, avg_conf, roi))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to update daily summary: {e}")
    
    def _calculate_daily_roi(self, date: str) -> float:
        """日次ROIを計算"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT predicted_prob, actual_rank, 
                   (SELECT tansho FROM race_data 
                    WHERE date = ? AND jyo_cd = pa.jyo_cd 
                    AND race_no = pa.race_no AND boat_no = pa.boat_no) as odds
            FROM prediction_accuracy pa
            WHERE date = ? AND predicted_hit = 1
        """, (date, date))
        
        results = cursor.fetchall()
        conn.close()
        
        total_return = sum(odds if odds and odds > 0 else 1 for _, _, odds in results)
        total_bets = len(results)
        
        return ((total_return - total_bets) / total_bets * 100) if total_bets > 0 else 0
    
    def get_accuracy_stats(self, days: int = 30) -> Dict:
        """精度統計を取得"""
        conn = sqlite3.connect(self.db_path)
        
        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
        
        # 全体精度
        overall_df = pd.read_sql_query("""
            SELECT date, total_predictions, correct_predictions, hit_rate, roi
            FROM daily_summary
            WHERE date >= ? AND date <= ?
            ORDER BY date
        """, conn, params=[start_date, end_date])
        
        # 確信度別精度
        confidence_df = pd.read_sql_query("""
            SELECT 
                CASE 
                    WHEN predicted_prob >= 0.9 THEN 'S'
                    WHEN predicted_prob >= 0.8 THEN 'A'
                    WHEN predicted_prob >= 0.7 THEN 'B'
                    WHEN predicted_prob >= 0.6 THEN 'C'
                    ELSE 'D'
                END as confidence_level,
                COUNT(*) as total,
                SUM(predicted_hit) as correct,
                AVG(predicted_prob) as avg_confidence
            FROM prediction_accuracy
            WHERE date >= ? AND date <= ?
            GROUP BY confidence_level
            ORDER BY avg_confidence DESC
        """, conn, params=[start_date, end_date])
        
        conn.close()
        
        return {
            "period_days": days,
            "daily_stats": overall_df.to_dict('records'),
            "confidence_stats": confidence_df.to_dict('records'),
            "overall_hit_rate": overall_df['hit_rate'].mean() if not overall_df.empty else 0,
            "overall_roi": overall_df['roi'].mean() if not overall_df.empty else 0
        }
    
    def detect_model_drift(self, window: int = 7) -> List[Dict]:
        """モデルドリフト検出"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # 最近のwindow日の精度
            recent_cursor = conn.cursor()
            recent_cursor.execute("""
                SELECT AVG(hit_rate) as recent_hit_rate, AVG(roi) as recent_roi
                FROM daily_summary
                WHERE date >= date('now', '-{} days')
            """.format(window))
            
            recent_result = recent_cursor.fetchone()
            recent_hit_rate, recent_roi = recent_result or (0, 0)
            
            # ベースライン精度（過去30日平均）
            baseline_cursor = conn.cursor()
            baseline_cursor.execute("""
                SELECT AVG(hit_rate) as baseline_hit_rate, AVG(roi) as baseline_roi
                FROM daily_summary
                WHERE date >= date('now', '-30 days') AND date < date('now', '-{} days')
            """.format(window))
            
            baseline_result = baseline_cursor.fetchone()
            baseline_hit_rate, baseline_roi = baseline_result or (0, 0)
            
            # ドリフト検出
            drift_detected = False
            alerts = []
            
            hit_rate_drift = abs(recent_hit_rate - baseline_hit_rate) / baseline_hit_rate if baseline_hit_rate > 0 else 0
            roi_drift = abs(recent_roi - baseline_roi) / abs(baseline_roi) if baseline_roi != 0 else 0
            
            if hit_rate_drift > 0.1:  # 10%以上変動
                drift_detected = True
                alerts.append({
                    "type": "hit_rate_drift",
                    "severity": "high" if hit_rate_drift > 0.2 else "medium",
                    "current": recent_hit_rate,
                    "baseline": baseline_hit_rate,
                    "change_percent": hit_rate_drift * 100
                })
            
            if roi_drift > 0.15:  # 15%以上変動
                drift_detected = True
                alerts.append({
                    "type": "roi_drift",
                    "severity": "high" if roi_drift > 0.3 else "medium",
                    "current": recent_roi,
                    "baseline": baseline_roi,
                    "change_percent": roi_drift * 100
                })
            
            # ドリフト記録
            if drift_detected:
                self._record_drift_alerts(alerts)
            
            conn.close()
            
            return alerts
            
        except Exception as e:
            logger.error(f"Drift detection failed: {e}")
            return []
    
    def _record_drift_alerts(self, alerts: List[Dict]):
        """ドリフト警告を記録"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        for alert in alerts:
            alert_type = alert["type"]
            current_value = alert["current"]
            baseline_value = alert["baseline"]
            
            cursor.execute("""
                INSERT INTO model_drift 
                (date, metric_name, current_value, baseline_value, drift_detected)
                VALUES (?, ?, ?, ?, ?)
            """, (datetime.now().strftime("%Y%m%d"), alert_type, current_value, baseline_value, True))
        
        conn.commit()
        conn.close()


# グローバルインスタンス
accuracy_monitor = AccuracyMonitor()
