import asyncio
import sys
import os
sys.path.append(os.getcwd())

from src.crawler.downloader_async import AsyncDownloader

async def test_async():
    print("Testing AsyncDownloader...")
    downloader = AsyncDownloader()
    # Test with a robust public URL
    url = "https://www.google.com" 
    
    print(f"Fetching {url}...")
    content = await downloader.download_batch([url])
    
    if content and len(content[0]) > 0:
        print(f"Success! Fetched {len(content[0])} bytes.")
    else:
        print("Failed to fetch content.")

if __name__ == "__main__":
    asyncio.run(test_async())
