import aiohttp
import asyncio
import os
from datetime import datetime

class AsyncDownloader:
    def __init__(self, cache_dir="data/html_cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
    
    def _get_cache_path(self, url):
        # Hash URL or use simple replacement
        filename = url.replace("https://", "").replace("http://", "").replace("/", "_").replace("?", "_")
        if len(filename) > 200: filename = filename[:200]
        return os.path.join(self.cache_dir, filename + ".html")

    def _get_cached_content(self, url, max_age_seconds=3600):
        path = self._get_cache_path(url)
        if os.path.exists(path):
            mtime = os.path.getmtime(path)
            if (datetime.now().timestamp() - mtime) < max_age_seconds:
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    return f.read()
        return None

    def _save_cache(self, url, content):
        path = self._get_cache_path(url)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

    async def fetch_page(self, session, url, max_age=3600):
        # Check cache first
        cached = self._get_cached_content(url, max_age)
        if cached:
            return cached

        try:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    try:
                        # Try utf-8 first, fallback to shift_jis if boatrace fails decoding
                        # Boatrace official site is typically EUC-JP or UTF-8 now? 
                        # Actually standard requests handles encoding well. aiohttp needs manual.
                        # Usually BoatRace is UTF-8 now but used to be EUC-JP.
                        # We use .read() and decode manually
                        raw = await response.read()
                        try:
                            text = raw.decode('utf-8')
                        except:
                            text = raw.decode('euc-jp', errors='ignore')
                        
                        self._save_cache(url, text)
                        return text
                    except Exception as e:
                        print(f"Decoding error {url}: {e}")
                        return ""
                else:
                    print(f"Error {response.status} for {url}")
                    return ""
        except Exception as e:
            print(f"Fetch error {url}: {e}")
            return ""

    async def download_batch(self, urls, max_age=3600):
        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch_page(session, url, max_age) for url in urls]
            return await asyncio.gather(*tasks)
