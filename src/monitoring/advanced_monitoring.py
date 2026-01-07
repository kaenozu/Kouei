"""Advanced monitoring with notifications and alert system"""
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import sqlite3
from dataclasses import dataclass
from enum import Enum
import requests

# Discord webhook for notifications
class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning" 
    CRITICAL = "critical"
    SUCCESS = "success"

@dataclass
class AlertRule:
    name: str
    condition: str
    threshold: float
    level: AlertLevel
    is_active: bool = True
    notifications_sent: int = 0
    cooldown_minutes: int = 30
    last_triggered: Optional[datetime] = None
    
@dataclass
class SystemMetric:
    name: str
    value: float
    timestamp: datetime
    context: Optional[Dict[str, Any]] = None

class AdvancedMonitoring:
    def __init__(self, db_path: str = "data/monitoring.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self.alert_rules = []
        self.metrics_history = []
        self.discord_webhook = self._load_discord_webhook()
        self._init_database()
        
    def _load_discord_webhook(self) -> str:
        """Load Discord webhook from config"""
        try:
            with open('config.json', 'r') as f:
                config = json.load(f)
            return config.get('discord_webhook_url', '')
        except Exception:
            return ''
    
    def _init_database(self):
        """Initialize monitoring database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                value REAL NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                context TEXT
            )
        ''')
        
        # Create alerts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rule_name TEXT NOT NULL,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                resolved DATETIME,
                is_acknowledged BOOLEAN DEFAULT 0
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_metric(self, metric: SystemMetric):
        """Add a system metric to monitor"""
        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO metrics (name, value, context) VALUES (?, ?, ?)",
            (metric.name, metric.value, json.dumps(metric.context) if metric.context else None)
        )
        conn.commit()
        conn.close()
        
        # Keep in memory for recent metrics
        self.metrics_history.append(metric)
        
        # Keep only last 1000 metrics in memory
        if len(self.metrics_history) > 1000:
            self.metrics_history = self.metrics_history[-1000:]
        
        # Check alert rules
        self._check_alert_rules(metric)
    
    def add_alert_rule(self, rule: AlertRule):
        """Add a new alert rule"""
        self.alert_rules.append(rule)
        self.logger.info(f"Added alert rule: {rule.name}")
    
    def _check_alert_rules(self, metric: SystemMetric):
        """Check if any alert rules are triggered by this metric"""
        for rule in self.alert_rules:
            if not rule.is_active:
                continue
                
            # Check cooldown
            if rule.last_triggered:
                cooldown_remaining = (
                    datetime.now() - rule.last_triggered
                ).total_seconds() / 60
                if cooldown_remaining < rule.cooldown_minutes:
                    continue
            
            # Check rule condition
            triggered = self._evaluate_rule(rule, metric)
            
            if triggered:
                self._trigger_alert(rule, metric)
    
    def _evaluate_rule(self, rule: AlertRule, metric: SystemMetric) -> bool:
        """Evaluate alert rule condition"""
        if rule.name.lower() in metric.name.lower():
            if '>' in rule.condition:
                threshold = float(rule.condition.split('>')[1].strip())
                return metric.value > threshold
            elif '<' in rule.condition:
                threshold = float(rule.condition.split('<')[1].strip())
                return metric.value < threshold
        return False
    
    def _trigger_alert(self, rule: AlertRule, metric: SystemMetric):
        """Trigger alert notification"""
        message = self._create_alert_message(rule, metric)
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO alerts (rule_name, level, message) VALUES (?, ?, ?)",
            (rule.name, rule.level.value, message)
        )
        conn.commit()
        conn.close()
        
        # Send Discord notification
        if self.discord_webhook:
            self._send_discord_alert(rule, metric, message)
        
        # Update rule
        rule.last_triggered = datetime.now()
        rule.notifications_sent += 1
        
        self.logger.warning(f"Alert triggered: {rule.name} - {message}")
    
    def _create_alert_message(self, rule: AlertRule, metric: SystemMetric) -> str:
        """Create alert message"""
        level_emoji = {
            AlertLevel.INFO: "ℹ️",
            AlertLevel.WARNING: "⚠️", 
            AlertLevel.CRITICAL: "🚨",
            AlertLevel.SUCCESS: "✅"
        }
        
        emoji = level_emoji.get(rule.level, "📢")
        
        message = (
            f"{emoji} **{rule.name.upper()}**\n"
            f"Metric: {metric.name}\n"
            f"Value: {metric.value:.2f}\n"
            f"Threshold: {rule.condition}\n"
            f"Timestamp: {metric.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        if metric.context:
            message += f"\nContext: {json.dumps(metric.context, indent=2)}"
        
        return message
    
    def _send_discord_alert(self, rule: AlertRule, metric: SystemMetric, message: str):
        """Send alert to Discord webhook"""
        try:
            # Color by alert level
            colors = {
                AlertLevel.INFO: 0x3498db,  # blue
                AlertLevel.WARNING: 0xf39c12,  # orange
                AlertLevel.CRITICAL: 0xe74c3c,  # red
                AlertLevel.SUCCESS: 0x27ae60  # green
            }
            
            color = colors.get(rule.level, 0x3498db)
            
            payload = {
                "username": "Kouei Monitor",
                "avatar_url": "https://example.com/avatar.png",
                "embeds": [{
                    "title": f"{rule.name} Alert",
                    "description": message,
                    "color": color,
                    "timestamp": datetime.now().isoformat(),
                    "footer": {
                        "text": "Kouei AI System Monitor"
                    }
                }]
            }
            
            response = requests.post(self.discord_webhook, json=payload, timeout=10)
            response.raise_for_status()
            
        except Exception as e:
            self.logger.error(f"Failed to send Discord alert: {e}")
    
    def get_recent_metrics(self, metric_name: str, minutes: int = 60) -> List[SystemMetric]:
        """Get recent metrics for a specific metric name"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        
        recent = [
            m for m in self.metrics_history 
            if metric_name.lower() in m.name.lower() 
            and m.timestamp >= cutoff_time
        ]
        
        return sorted(recent, key=lambda x: x.timestamp)
    
    def get_system_health_summary(self) -> Dict[str, Any]:
        """Get overall system health summary"""
        # Get recent metrics
        cpu_metrics = self.get_recent_metrics('cpu', 10)
        memory_metrics = self.get_recent_metrics('memory', 10)
        prediction_metrics = self.get_recent_metrics('prediction', 10)
        
        # Calculate averages
        avg_cpu = sum(m.value for m in cpu_metrics) / len(cpu_metrics) if cpu_metrics else 0
        avg_memory = sum(m.value for m in memory_metrics) / len(memory_metrics) if memory_metrics else 0
        
        # Recent alerts (last hour)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        one_hour_ago = datetime.now() - timedelta(hours=1)
        cursor.execute(
            "SELECT COUNT(*) FROM alerts WHERE timestamp >= ? AND is_acknowledged = 0",
            (one_hour_ago.isoformat(),)
        )
        recent_alerts = cursor.fetchone()[0]
        
        # Determine overall status
        if avg_cpu > 90 or avg_memory > 90:
            status = "critical"
        elif avg_cpu > 70 or avg_memory > 70:
            status = "warning"
        else:
            status = "healthy"
        
        return {
            "status": status,
            "cpu_usage": avg_cpu,
            "memory_usage": avg_memory,
            "recent_alerts": recent_alerts,
            "total_predictions": len(prediction_metrics),
            "uptime_minutes": self._get_uptime()
        }
    
    def _get_uptime(self) -> int:
        """Get system uptime in minutes"""
        try:
            # Simplified uptime calculation
            if self.metrics_history:
                first_metric = min(self.metrics_history, key=lambda x: x.timestamp)
                uptime = (datetime.now() - first_metric.timestamp).total_seconds() / 60
                return int(uptime)
            return 0
        except Exception:
            return 0
    
    def create_default_alert_rules(self):
        """Create default alert rules"""
        default_rules = [
            AlertRule(
                name="High CPU Usage",
                condition="cpu_usage > 80",
                threshold=80,
                level=AlertLevel.WARNING,
                cooldown_minutes=20
            ),
            AlertRule(
                name="Critical CPU Usage",
                condition="cpu_usage > 90", 
                threshold=90,
                level=AlertLevel.CRITICAL,
                cooldown_minutes=10
            ),
            AlertRule(
                name="High Memory Usage",
                condition="memory_usage > 85",
                threshold=85,
                level=AlertLevel.WARNING,
                cooldown_minutes=15
            ),
            AlertRule(
                name="Low Model Accuracy",
                condition="model_accuracy < 0.6",
                threshold=0.6,
                level=AlertLevel.WARNING,
                cooldown_minutes=30
            ),
            AlertRule(
                name="Model Training Complete",
                condition="training_finished > 0",
                threshold=1,
                level=AlertLevel.SUCCESS,
                cooldown_minutes=60
            ),
            AlertRule(
                name="System Restart",
                condition="system_restart > 0",
                threshold=1,
                level=AlertLevel.INFO,
                cooldown_minutes=30
            )
        ]
        
        for rule in default_rules:
            self.add_alert_rule(rule)
        
        self.logger.info(f"Created {len(default_rules)} default alert rules")

# Global monitoring instance
monitor = AdvancedMonitoring()

# Helper function to record system metrics
def record_system_metric(name: str, value: float, context: Optional[Dict[str, Any]] = None):
    """Record a system metric for monitoring"""
    metric = SystemMetric(
        name=name,
        value=value,
        timestamp=datetime.now(),
        context=context
    )
    monitor.add_metric(metric)

# Initialize default rules
monitor.create_default_alert_rules()