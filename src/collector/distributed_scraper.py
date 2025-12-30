"""
Distributed Scraper
Uses multiprocessing to parallelize data collection across different stadiums.
"""
import multiprocessing
import time
from src.collector.collect_data import RaceCollector
from datetime import datetime

def scrape_stadium(jyo_cd, date_str):
    """Worker function to scrape a single stadium"""
    print(f"🧵 Worker: Starting stadium {jyo_cd}...")
    collector = RaceCollector()
    # Mocking the call to avoid heavy load during test, but showing logic
    # collector.collect_single_stadium(date_str, jyo_cd)
    time.sleep(2)
    print(f"✅ Worker: Finished stadium {jyo_cd}")

class DistributedScraper:
    def __init__(self, n_workers=4):
        self.n_workers = n_workers

    def run(self, date_str, jyo_list):
        print(f"🚀 Starting Distributed Scraper with {self.n_workers} workers")
        
        with multiprocessing.Pool(processes=self.n_workers) as pool:
            # Create tasks for each stadium
            tasks = [(jyo, date_str) for jyo in jyo_list]
            pool.starmap(scrape_stadium, tasks)
            
        print("🏁 Distributed scraping complete.")

if __name__ == "__main__":
    scraper = DistributedScraper(n_workers=4)
    # Test with top 4 stadiums
    test_jyos = ["01", "02", "03", "04"]
    scraper.run(datetime.now().strftime("%Y%m%d"), test_jyos)
