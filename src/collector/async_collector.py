"""Fully Async Data Collector with Parallel Downloads"""
import asyncio
import aiohttp
import aiofiles
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import gzip
import hashlib

from src.config.settings import settings
from src.utils.logger import get_logger, log_execution_time
from src.parser.schedule_parser import ScheduleParser

logger = get_logger()


@dataclass
class DownloadTask:
    """Represents a download task"""
    url: str
    save_path: str
    max_age: Optional[int] = None  # seconds
    compress: bool = False


class AsyncRaceCollector:
    """High-performance async race data collector"""
    
    BASE_URL = "https://www.boatrace.jp/owpc/pc/race"
    
    def __init__(self, base_dir: str = "data"):
        self.base_dir = base_dir
        self.raw_dir = os.path.join(base_dir, "raw")
        self.schedule_parser = ScheduleParser()
        self.semaphore = asyncio.Semaphore(settings.max_concurrent_requests)
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=settings.scrape_timeout),
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def _is_cache_valid(self, path: str, max_age: Optional[int]) -> bool:
        """Check if cached file is still valid (checks both .html and .html.gz)"""
        # Check both compressed and uncompressed versions
        paths_to_check = [path]
        if path.endswith('.gz'):
            paths_to_check.append(path[:-3])  # Also check without .gz
        else:
            paths_to_check.append(path + '.gz')  # Also check with .gz
        
        for p in paths_to_check:
            if os.path.exists(p):
                if max_age is None:
                    return True
                mtime = os.path.getmtime(p)
                age = datetime.now().timestamp() - mtime
                if age < max_age:
                    return True
        return False
    
    async def _download_one(self, task: DownloadTask) -> Tuple[str, bool, Optional[str]]:
        """Download a single URL with rate limiting"""
        async with self.semaphore:
            # Check cache
            actual_path = task.save_path + ".gz" if task.compress else task.save_path
            if self._is_cache_valid(actual_path, task.max_age):
                logger.debug(f"Cache hit: {task.save_path}")
                return task.url, True, None
            
            try:
                # Rate limiting
                await asyncio.sleep(settings.scrape_delay / settings.max_concurrent_requests)
                
                async with self.session.get(task.url) as response:
                    if response.status != 200:
                        return task.url, False, f"HTTP {response.status}"
                    
                    content = await response.text()
                    
                    # Ensure directory exists
                    os.makedirs(os.path.dirname(task.save_path), exist_ok=True)
                    
                    # Save (optionally compressed)
                    if task.compress:
                        async with aiofiles.open(actual_path, 'wb') as f:
                            await f.write(gzip.compress(content.encode('utf-8')))
                    else:
                        async with aiofiles.open(task.save_path, 'w', encoding='utf-8') as f:
                            await f.write(content)
                    
                    logger.debug(f"Downloaded: {task.url}")
                    return task.url, True, content
                    
            except asyncio.TimeoutError:
                return task.url, False, "Timeout"
            except Exception as e:
                return task.url, False, str(e)
    
    async def _download_batch(self, tasks: List[DownloadTask]) -> Dict[str, bool]:
        """Download multiple URLs in parallel"""
        results = await asyncio.gather(
            *[self._download_one(task) for task in tasks],
            return_exceptions=True
        )
        
        success_count = sum(1 for r in results if isinstance(r, tuple) and r[1])
        logger.info(
            f"Batch download complete",
            total=len(tasks),
            success=success_count,
            failed=len(tasks) - success_count
        )
        
        return {r[0]: r[1] for r in results if isinstance(r, tuple)}
    
    def _get_urls_for_date(self, date_str: str, jyo_codes: List[str], is_today: bool) -> List[DownloadTask]:
        """Generate all download tasks for a date"""
        tasks = []
        max_age = settings.cache_ttl_realtime if is_today else None
        
        for jyo_cd in jyo_codes:
            for race_no in range(1, 13):
                base_path = os.path.join(self.raw_dir, date_str, jyo_cd)
                
                # Program (race entry list)
                tasks.append(DownloadTask(
                    url=f"{self.BASE_URL}/racelist?rno={race_no}&jcd={jyo_cd}&hd={date_str}",
                    save_path=os.path.join(base_path, f"program_{race_no}.html"),
                    max_age=max_age,
                    compress=False
                ))
                
                # Before Info (weather, exhibition)
                tasks.append(DownloadTask(
                    url=f"{self.BASE_URL}/beforeinfo?rno={race_no}&jcd={jyo_cd}&hd={date_str}",
                    save_path=os.path.join(base_path, f"beforeinfo_{race_no}.html"),
                    max_age=max_age,
                    compress=False
                ))
                
                # Race Result
                tasks.append(DownloadTask(
                    url=f"{self.BASE_URL}/raceresult?rno={race_no}&jcd={jyo_cd}&hd={date_str}",
                    save_path=os.path.join(base_path, f"result_{race_no}.html"),
                    max_age=max_age,
                    compress=False
                ))
                
                # Odds (2-ren, 3-ren)
                tasks.append(DownloadTask(
                    url=f"{self.BASE_URL}/odds2tf?rno={race_no}&jcd={jyo_cd}&hd={date_str}",
                    save_path=os.path.join(base_path, f"odds2_{race_no}.html"),
                    max_age=settings.cache_ttl_realtime if is_today else max_age,
                    compress=False
                ))
                
                tasks.append(DownloadTask(
                    url=f"{self.BASE_URL}/odds3t?rno={race_no}&jcd={jyo_cd}&hd={date_str}",
                    save_path=os.path.join(base_path, f"odds3_{race_no}.html"),
                    max_age=settings.cache_ttl_realtime if is_today else max_age,
                    compress=False
                ))
        
        return tasks
    
    @log_execution_time()
    async def collect_date(self, date: datetime.date) -> Dict[str, any]:
        """Collect all data for a single date"""
        date_str = date.strftime("%Y%m%d")
        is_today = date == datetime.now().date()
        
        logger.info(f"Collecting data for {date_str}", is_today=is_today)
        
        # 1. Get schedule
        schedule_url = f"{self.BASE_URL}/index?hd={date_str}"
        schedule_path = os.path.join(self.raw_dir, date_str, "schedule.html")
        
        schedule_task = DownloadTask(
            url=schedule_url,
            save_path=schedule_path,
            max_age=settings.cache_ttl_realtime if is_today else 86400
        )
        
        url, success, content = await self._download_one(schedule_task)
        
        if not success:
            logger.error(f"Failed to download schedule for {date_str}")
            return {"date": date_str, "status": "error", "stadiums": 0, "downloads": 0}
        
        # Read from file if content is None (cache hit)
        if content is None:
            async with aiofiles.open(schedule_path, 'r', encoding='utf-8') as f:
                content = await f.read()
        
        # 2. Parse stadium codes
        jyo_codes = self.schedule_parser.parse(content)
        logger.info(f"Found {len(jyo_codes)} stadiums", stadiums=jyo_codes)
        
        if not jyo_codes:
            return {"date": date_str, "status": "no_races", "stadiums": 0, "downloads": 0}
        
        # 3. Generate all download tasks
        tasks = self._get_urls_for_date(date_str, jyo_codes, is_today)
        
        # 4. Download all in parallel
        results = await self._download_batch(tasks)
        
        success_count = sum(1 for v in results.values() if v)
        
        return {
            "date": date_str,
            "status": "success",
            "stadiums": len(jyo_codes),
            "downloads": success_count,
            "total_tasks": len(tasks)
        }
    
    @log_execution_time()
    async def collect_range(self, start_date: datetime.date, end_date: datetime.date) -> List[Dict]:
        """Collect data for a date range"""
        results = []
        current = start_date
        
        while current <= end_date:
            result = await self.collect_date(current)
            results.append(result)
            current += timedelta(days=1)
        
        return results
    
    async def collect_realtime(self, jyo_cd: str, race_no: int) -> Dict:
        """Collect real-time data for a specific race (sniper mode)"""
        date_str = datetime.now().strftime("%Y%m%d")
        base_path = os.path.join(self.raw_dir, date_str, jyo_cd)
        
        tasks = [
            DownloadTask(
                url=f"{self.BASE_URL}/beforeinfo?rno={race_no}&jcd={jyo_cd}&hd={date_str}",
                save_path=os.path.join(base_path, f"beforeinfo_{race_no}.html"),
                max_age=30  # Very fresh data
            ),
            DownloadTask(
                url=f"{self.BASE_URL}/odds2tf?rno={race_no}&jcd={jyo_cd}&hd={date_str}",
                save_path=os.path.join(base_path, f"odds2_{race_no}.html"),
                max_age=15  # Real-time odds
            ),
            DownloadTask(
                url=f"{self.BASE_URL}/odds3t?rno={race_no}&jcd={jyo_cd}&hd={date_str}",
                save_path=os.path.join(base_path, f"odds3_{race_no}.html"),
                max_age=15
            ),
        ]
        
        results = await self._download_batch(tasks)
        return {
            "jyo_cd": jyo_cd,
            "race_no": race_no,
            "success": all(results.values())
        }


async def collect_data_async(start_date: str, end_date: str) -> List[Dict]:
    """Entry point for async collection"""
    start = datetime.strptime(start_date, "%Y%m%d").date()
    end = datetime.strptime(end_date, "%Y%m%d").date()
    
    async with AsyncRaceCollector() as collector:
        return await collector.collect_range(start, end)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) >= 3:
        start = sys.argv[1]
        end = sys.argv[2]
    else:
        today = datetime.now().strftime("%Y%m%d")
        start = end = today
    
    results = asyncio.run(collect_data_async(start, end))
    for r in results:
        print(r)
