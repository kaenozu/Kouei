import os
import argparse
from datetime import datetime, timedelta
from src.collector.downloader import Downloader
from src.parser.schedule_parser import ScheduleParser

class RaceCollector:
    def __init__(self, base_dir="data"):
        self.base_dir = base_dir
        self.raw_dir = os.path.join(base_dir, "raw")
        self.downloader = Downloader(base_dir=self.raw_dir, delay=1.0)
        self.schedule_parser = ScheduleParser()

    def collect(self, start_date, end_date):
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime("%Y%m%d")
            print(f"Processing {date_str}...")
            
            # 1. Get Schedule
            schedule_url = f"https://www.boatrace.jp/owpc/pc/race/index?hd={date_str}"
            schedule_html = self.downloader.download_page(
                schedule_url, 
                save_path=os.path.join(self.raw_dir, date_str, "schedule.html")
            )
            
            if not schedule_html:
                print(f"Failed to download schedule for {date_str}")
                current_date += timedelta(days=1)
                continue

            jyo_codes = self.schedule_parser.parse(schedule_html)
            print(f"Found stadiums: {jyo_codes}")
            
            is_today = (current_date == datetime.now().date())
            max_age_dynamic = 600 if is_today else None # 10 minutes cache for today
            
            # 2. For each stadium, download Race Program and Results
            for jyo_cd in jyo_codes:
                for race_no in range(1, 13):
                    # Download Race Program (Entry List) - Usually doesn't change much, but could use some max_age
                    program_url = self.downloader.get_program_url(date_str, jyo_cd, race_no)
                    self.downloader.download_page(
                        program_url,
                        save_path=os.path.join(self.raw_dir, date_str, jyo_cd, f"program_{race_no}.html")
                    )

                    # Download Before Info (Weather, Exhibition) - Changes frequently
                    before_url = self.downloader.get_beforeinfo_url(date_str, jyo_cd, race_no)
                    self.downloader.download_page(
                        before_url,
                        save_path=os.path.join(self.raw_dir, date_str, jyo_cd, f"beforeinfo_{race_no}.html"),
                        max_age=max_age_dynamic
                    )
                    
                    # Download Race Result
                    # Attempt results for today (with max_age) as well as past dates
                    result_url = self.downloader.get_race_result_url(date_str, jyo_cd, race_no)
                    self.downloader.download_page(
                        result_url,
                        save_path=os.path.join(self.raw_dir, date_str, jyo_cd, f"result_{race_no}.html"),
                        max_age=max_age_dynamic
                    )
            
            current_date += timedelta(days=1)

def parse_args():
    parser = argparse.ArgumentParser(description="Collect Boat Race Data")
    parser.add_argument("--start_date", type=str, required=True, help="YYYYMMDD")
    parser.add_argument("--end_date", type=str, required=True, help="YYYYMMDD")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    start = datetime.strptime(args.start_date, "%Y%m%d").date()
    end = datetime.strptime(args.end_date, "%Y%m%d").date()
    
    collector = RaceCollector()
    collector.collect(start, end)
