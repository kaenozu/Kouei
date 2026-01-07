"""Notification Service - Discord and LINE notifications"""
import aiohttp
import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import os

from src.utils.logger import logger


@dataclass
class RaceAlert:
    """High probability race alert"""
    date: str
    jyo_cd: str
    jyo_name: str
    race_no: int
    race_time: str
    boat_no: int
    racer_name: str
    probability: float
    confidence: str
    tansho_odds: Optional[float] = None
    ev: Optional[float] = None


class Notifier:
    """Send notifications via Discord and LINE"""
    
    VENUE_NAMES = {
        "01": "桐生", "02": "戸田", "03": "江戸川", "04": "平和島",
        "05": "多摩川", "06": "浜名湖", "07": "蒲郡", "08": "常滑",
        "09": "津", "10": "三国", "11": "びわこ", "12": "住之江",
        "13": "尼崎", "14": "鳴門", "15": "丸亀", "16": "児島",
        "17": "宮島", "18": "徳山", "19": "下関", "20": "若松",
        "21": "芦屋", "22": "福岡", "23": "唐津", "24": "大村"
    }
    
    def __init__(self):
        self.discord_webhook = os.getenv("DISCORD_WEBHOOK_URL", "")
        self.line_token = os.getenv("LINE_NOTIFY_TOKEN", "")
    
    async def send_discord(self, content: str, embeds: List[Dict] = None):
        """Send message to Discord webhook"""
        if not self.discord_webhook:
            return False
        
        payload = {"content": content}
        if embeds:
            payload["embeds"] = embeds
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.discord_webhook, json=payload) as resp:
                    return resp.status in (200, 204)
        except Exception as e:
            logger.error(f"Discord error: {e}")
            return False
    
    async def send_line(self, message: str):
        """Send message via LINE Notify"""
        if not self.line_token:
            return False
        
        url = "https://notify-api.line.me/api/notify"
        headers = {"Authorization": f"Bearer {self.line_token}"}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data={"message": message}) as resp:
                    return resp.status == 200
        except Exception as e:
            logger.error(f"LINE error: {e}")
            return False
    
    def format_alert(self, alert: RaceAlert) -> str:
        """Format alert for text notification"""
        confidence_emoji = {"S": "🔥🔥🔥", "A": "🔥🔥", "B": "🔥", "C": ""}
        
        lines = [
            f"\n{confidence_emoji.get(alert.confidence, '')} 【高期待値レース】",
            f"📍 {alert.jyo_name} {alert.race_no}R ({alert.race_time})",
            f"🚤 {alert.boat_no}号艇 {alert.racer_name}",
            f"📊 予測勝率: {alert.probability:.1%}",
        ]
        
        if alert.tansho_odds:
            lines.append(f"💰 単勝オッズ: {alert.tansho_odds:.1f}倍")
        
        if alert.ev and alert.ev > 0:
            lines.append(f"📈 期待値: +{alert.ev:.1%}")
        
        return "\n".join(lines)
    
    def format_discord_embed(self, alert: RaceAlert) -> Dict:
        """Format alert as Discord embed"""
        color = {"S": 0xFF0000, "A": 0xFF6600, "B": 0xFFCC00, "C": 0x00FF00}
        
        fields = [
            {"name": "会場", "value": alert.jyo_name, "inline": True},
            {"name": "レース", "value": f"{alert.race_no}R", "inline": True},
            {"name": "時刻", "value": alert.race_time, "inline": True},
            {"name": "艇番", "value": f"{alert.boat_no}号艇", "inline": True},
            {"name": "選手", "value": alert.racer_name or "不明", "inline": True},
            {"name": "予測勝率", "value": f"{alert.probability:.1%}", "inline": True},
        ]
        
        if alert.tansho_odds:
            fields.append({"name": "単勝", "value": f"{alert.tansho_odds:.1f}倍", "inline": True})
        
        if alert.ev:
            fields.append({"name": "期待値", "value": f"{alert.ev:+.1%}", "inline": True})
        
        return {
            "title": "🎯 高期待値レース検出",
            "color": color.get(alert.confidence, 0x808080),
            "fields": fields,
            "footer": {"text": f"信頼度: {alert.confidence}"},
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def send_alert(self, alert: RaceAlert):
        """Send alert to all configured channels"""
        tasks = []
        
        if self.discord_webhook:
            embed = self.format_discord_embed(alert)
            tasks.append(self.send_discord("", embeds=[embed]))
        
        if self.line_token:
            message = self.format_alert(alert)
            tasks.append(self.send_line(message))
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return any(r is True for r in results)
        
        return False


_notifier = None

def get_notifier() -> Notifier:
    global _notifier
    if _notifier is None:
        _notifier = Notifier()
    return _notifier
