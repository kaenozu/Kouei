"""
Auto Collector - Real-time race data and odds collection system
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time
import json
from pathlib import Path

from src.collector.downloader import Downloader
from src.collector.odds_collector import OddsCollector
from src.parser.schedule_parser import ScheduleParser
from src.parser.race_parser import RaceParser
from src.parser.odds_parser import OddsParser
from src.api.routers.system import broadcast_event
from src.config.database import save_race_data, save_odds_data

logger = logging.getLogger(__name__)


class AutoCollector:
    """自動データ収集システム"""
    
    def __init__(self, collection_interval: int = 60):
        self.downloader = Downloader()
        self.odds_collector = OddsCollector()
        self.schedule_parser = ScheduleParser()
        self.race_parser = RaceParser()
        self.odds_parser = OddsParser()
        self.collection_interval = collection_interval  # seconds
        self.running = False
        self.latest_data = {}
        
    async def start_collection(self):
        """自動収集を開始"""
        self.running = True
        logger.info("🚀 AutoCollection started")
        
        while self.running:
            try:
                await self.collect_today_data()
                await asyncio.sleep(self.collection_interval)
            except Exception as e:
                logger.error(f"Collection error: {e}")
                await asyncio.sleep(30)  # Error retry delay
    
    def stop_collection(self):
        """自動収集を停止"""
        self.running = False
        logger.info("🛑 AutoCollection stopped")
    
    async def collect_today_data(self):
        """本日のレースデータを収集"""
        today = datetime.now().strftime("%Y%m%d")
        
        # 1. スケジュール収集
        schedule_data = await self._collect_schedule(today)
        
        if not schedule_data:
            logger.warning(f"No schedule data for {today}")
            return
        
        # 2. 各会場のレースデータ収集
        for venue_code in schedule_data.get('venues', []):
            await self._collect_venue_data(today, venue_code)
        
        # 3. オッズ更新
        await self._update_all_odds(today)
        
        # 4. 収集完了通知
        await self._notify_collection_complete(today)
    
    async def _collect_schedule(self, date: str) -> Optional[Dict]:
        """スケジュールデータ収集"""
        try:
            url = f"https://www.boatrace.jp/topia/data/schedule_{date}.json"
            html = await self.downloader.get_schedule_async(url)
            
            if html:
                schedule_data = self.schedule_parser.parse(html)
                self.latest_data[f'schedule_{date}'] = schedule_data
                logger.info(f"✅ Schedule collected for {date}")
                return schedule_data
        except Exception as e:
            logger.error(f"Schedule collection failed: {e}")
        return None
    
    async def _collect_venue_data(self, date: str, venue_code: str):
        """会場別レースデータ収集"""
        try:
            for race_no in range(1, 13):  # Max 12 races
                # レースデータ収集
                race_url = f"https://www.boatrace.jp/topia/race_result_{date}_{venue_code}_{race_no}.html"
                race_html = await self.downloader.get_race_async(race_url)
                
                if race_html:
                    race_data = self.race_parser.parse(race_html)
                    if race_data:
                        # データベース保存
                        save_race_data(race_data)
                        
                        # リアルタイム通知
                        await broadcast_event({
                            "type": "race_data_updated",
                            "date": date,
                            "venue": venue_code,
                            "race_no": race_no,
                            "data": race_data
                        })
                        
                        logger.info(f"✅ Race {venue_code}-{race_no} data collected")
                
                # 短い遅延
                await asyncio.sleep(0.5)
        except Exception as e:
            logger.error(f"Venue {venue_code} collection failed: {e}")
    
    async def _update_all_odds(self, date: str):
        """全オッズ更新"""
        try:
            odds_data = await self.odds_collector.collect_all_odds(date)
            
            if odds_data:
                # データベース保存
                save_odds_data(odds_data)
                
                # リアルタイム通知
                await broadcast_event({
                    "type": "odds_updated",
                    "date": date,
                    "data": odds_data
                })
                
                logger.info(f"✅ Odds updated for {date}")
        except Exception as e:
            logger.error(f"Odds update failed: {e}")
    
    async def _notify_collection_complete(self, date: str):
        """収集完了通知"""
        await broadcast_event({
            "type": "collection_complete",
            "date": date,
            "timestamp": datetime.now().isoformat(),
            "stats": {
                "venues": len(self.latest_data.get(f'schedule_{date}', {}).get('venues', [])),
                "total_races": sum(len(v.get('races', [])) for v in self.latest_data.values())
            }
        })
    
    async def backfill_missing_data(self, start_date: str, end_date: str):
        """過去データのバックフィル"""
        logger.info(f"🔄 Backfilling data from {start_date} to {end_date}")
        
        current_date = datetime.strptime(start_date, "%Y%m%d")
        end_date_obj = datetime.strptime(end_date, "%Y%m%d")
        
        while current_date <= end_date_obj:
            date_str = current_date.strftime("%Y%m%d")
            
            try:
                # スケジュール確認
                schedule_data = await self._collect_schedule(date_str)
                
                if schedule_data and schedule_data.get('venues'):
                    # データ収集
                    for venue_code in schedule_data['venues']:
                        await self._collect_venue_data(date_str, venue_code)
                    
                    logger.info(f"✅ Backfilled {date_str}")
                else:
                    logger.info(f"⏭️ No races for {date_str}")
                
            except Exception as e:
                logger.error(f"Backfill failed for {date_str}: {e}")
            
            current_date += timedelta(days=1)
            await asyncio.sleep(1)  # Rate limiting
    
    def get_collection_status(self) -> Dict:
        """収集ステータス取得"""
        return {
            "running": self.running,
            "collection_interval": self.collection_interval,
            "latest_collections": list(self.latest_data.keys()),
            "last_update": datetime.now().isoformat()
        }


# グローバルインスタンス
auto_collector = AutoCollector()


async def start_auto_collection():
    """自動収集を開始（ワーカー用）"""
    await auto_collector.start_collection()


def stop_auto_collection():
    """自動収集を停止"""
    auto_collector.stop_collection()
