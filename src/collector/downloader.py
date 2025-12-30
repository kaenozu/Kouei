import requests
import time
import os
from datetime import datetime

class Downloader:
    def __init__(self, base_dir="data/raw", delay=1.0):
        self.base_dir = base_dir
        self.delay = delay
        self.last_access_time = 0
        
        if not os.path.exists(self.base_dir):
            os.makedirs(self.base_dir)

    def _wait_for_politeness(self):
        current_time = time.time()
        time_diff = current_time - self.last_access_time
        if time_diff < self.delay:
            time.sleep(self.delay - time_diff)
        self.last_access_time = time.time()

    def download_page(self, url, save_path=None, force_download=False, max_age=None):
        """
        Downloads a page from the given URL.
        If save_path is provided, saves the content to that file.
        If force_download is False and file exists, checks max_age.
        """
        if save_path and os.path.exists(save_path) and not force_download:
            if max_age is not None:
                file_age = time.time() - os.path.getmtime(save_path)
                if file_age <= max_age:
                    # print(f"File is fresh ({file_age:.1f}s old): {save_path}")
                    with open(save_path, 'r', encoding='utf-8') as f:
                        return f.read()
            else:
                # print(f"File already exists: {save_path}")
                with open(save_path, 'r', encoding='utf-8') as f:
                    return f.read()

        self._wait_for_politeness()
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            content = response.text
            
            if save_path:
                # Ensure directory exists
                directory = os.path.dirname(save_path)
                if not os.path.exists(directory):
                    os.makedirs(directory)
                    
                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            return content
        except Exception as e:
            print(f"Error downloading {url}: {e}")
            return None

    def get_race_result_url(self, date_str, jyo_cd, race_no):
        """
        Construct URL for race result
        date_str: YYYYMMDD
        jyo_cd: 01-24 (Stadium Code)
        race_no: 1-12
        """
        # Example: https://www.boatrace.jp/owpc/pc/race/raceresult?rno=1&jcd=01&hd=20240101
        return f"https://www.boatrace.jp/owpc/pc/race/raceresult?rno={race_no}&jcd={jyo_cd}&hd={date_str}"

    def get_program_url(self, date_str, jyo_cd, race_no):
        """
        Construct URL for race program (entry list)
        """
        # Example: https://www.boatrace.jp/owpc/pc/race/racelist?rno=1&jcd=01&hd=20240101
        return f"https://www.boatrace.jp/owpc/pc/race/racelist?rno={race_no}&jcd={jyo_cd}&hd={date_str}"

    def get_beforeinfo_url(self, date_str, jyo_cd, race_no):
        """
        Construct URL for before info (weather, exhibition time)
        """
        # Example: https://www.boatrace.jp/owpc/pc/race/beforeinfo?rno=1&jcd=01&hd=20240101
        return f"https://www.boatrace.jp/owpc/pc/race/beforeinfo?rno={race_no}&jcd={jyo_cd}&hd={date_str}"

    def get_odds2n_url(self, date_str, jyo_cd, race_no):
        """Construct URL for 2-rentan odds"""
        return f"https://www.boatrace.jp/owpc/pc/race/odds2n?rno={race_no}&jcd={jyo_cd}&hd={date_str}"

    def get_odds3t_url(self, date_str, jyo_cd, race_no):
        """Construct URL for 3-rentan odds"""
        return f"https://www.boatrace.jp/owpc/pc/race/odds3t?rno={race_no}&jcd={jyo_cd}&hd={date_str}"
