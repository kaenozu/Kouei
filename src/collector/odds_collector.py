"""Real-time Odds Collector"""
import aiohttp
import asyncio
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
from dataclasses import dataclass
import re

from src.utils.logger import logger


@dataclass
class OddsData:
    """Odds data for a race"""
    date: str
    jyo_cd: str
    race_no: int
    tansho: Dict[int, float]  # boat_no -> odds
    nirentan: Dict[str, float]  # "1-2" -> odds
    sanrentan: Dict[str, float]  # "1-2-3" -> odds
    timestamp: str


class OddsCollector:
    """Collect real-time odds from boatrace.jp"""
    
    BASE_URL = "https://www.boatrace.jp/owpc/pc/race"
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=10),
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        return self
    
    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()
    
    async def fetch_tansho_odds(self, date: str, jyo_cd: str, race_no: int) -> Dict[int, float]:
        """Fetch win (tansho) odds"""
        url = f"{self.BASE_URL}/oddstf?rno={race_no}&jcd={jyo_cd}&hd={date}"
        
        try:
            async with self.session.get(url) as resp:
                if resp.status != 200:
                    return {}
                
                html = await resp.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                odds = {}
                # Parse odds table
                rows = soup.select('table.is-w495 tbody tr')
                for row in rows:
                    cells = row.select('td')
                    if len(cells) >= 2:
                        try:
                            boat_no = int(cells[0].get_text(strip=True))
                            odds_text = cells[1].get_text(strip=True)
                            odds_val = float(odds_text.replace(',', ''))
                            odds[boat_no] = odds_val
                        except:
                            pass
                
                return odds
        except Exception as e:
            logger.warning(f"Failed to fetch tansho odds: {e}")
            return {}
    
    async def fetch_nirentan_odds(self, date: str, jyo_cd: str, race_no: int) -> Dict[str, float]:
        """Fetch exacta (nirentan) odds"""
        url = f"{self.BASE_URL}/odds2tf?rno={race_no}&jcd={jyo_cd}&hd={date}"
        
        try:
            async with self.session.get(url) as resp:
                if resp.status != 200:
                    return {}
                
                html = await resp.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                odds = {}
                # Parse 2-rentan odds
                cells = soup.select('td.oddsPoint')
                # Pattern: boat combinations in order
                combinations = [(i, j) for i in range(1, 7) for j in range(1, 7) if i != j]
                
                for idx, cell in enumerate(cells):
                    if idx < len(combinations):
                        try:
                            odds_text = cell.get_text(strip=True)
                            if odds_text and odds_text != '-':
                                i, j = combinations[idx]
                                odds[f"{i}-{j}"] = float(odds_text.replace(',', ''))
                        except:
                            pass
                
                return odds
        except Exception as e:
            logger.warning(f"Failed to fetch nirentan odds: {e}")
            return {}
    
    async def fetch_all_odds(self, date: str, jyo_cd: str, race_no: int) -> OddsData:
        """Fetch all odds for a race"""
        from datetime import datetime
        
        tansho, nirentan = await asyncio.gather(
            self.fetch_tansho_odds(date, jyo_cd, race_no),
            self.fetch_nirentan_odds(date, jyo_cd, race_no)
        )
        
        return OddsData(
            date=date,
            jyo_cd=jyo_cd,
            race_no=race_no,
            tansho=tansho,
            nirentan=nirentan,
            sanrentan={},  # Skip 3-rentan for speed
            timestamp=datetime.now().isoformat()
        )


async def get_realtime_odds(date: str, jyo_cd: str, race_no: int) -> OddsData:
    """Helper function to get real-time odds"""
    async with OddsCollector() as collector:
        return await collector.fetch_all_odds(date, jyo_cd, race_no)
