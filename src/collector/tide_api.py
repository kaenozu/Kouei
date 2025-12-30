"""
Tide API Integration
Fetches sea level / tide data for specific Boat Race stadium coordinates.
Uses Open-Meteo Marine API (Free).
"""
import requests
import pandas as pd
from datetime import datetime

STADIUM_COORDS = {
    "01": (36.41, 139.31),  # Kiryu
    "02": (35.82, 139.67),  # Toda
    "03": (35.70, 139.85),  # Edogawa
    "04": (35.58, 139.75),  # Heiwajima
    "05": (35.65, 139.50),  # Tamagawa
    "06": (34.76, 137.64),  # Hamanako
    "07": (34.83, 137.23),  # Gamagori
    "08": (34.88, 136.85),  # Tokoname
    "09": (34.69, 136.52),  # Tsu
    "10": (36.23, 136.17),  # Mikuni
    "11": (35.02, 135.87),  # Biwako
    "12": (34.61, 135.50),  # Suminoe
    "13": (34.72, 135.41),  # Amagasaki
    "14": (34.19, 134.61),  # Naruto
    "15": (34.29, 133.79),  # Marugame
    "16": (34.46, 133.82),  # Kojima
    "17": (34.30, 132.31),  # Miyajima
    "18": (34.05, 131.81),  # Tokuyama
    "19": (33.95, 130.93),  # Shimonoseki
    "20": (33.90, 130.80),  # Wakamatsu
    "21": (33.90, 130.67),  # Ashiya
    "22": (33.59, 130.38),  # Fukuoka
    "23": (33.45, 129.98),  # Karatsu
    "24": (32.93, 129.94)   # Omura
}

class TideAPI:
    def __init__(self):
        self.base_url = "https://marine-api.open-meteo.com/v1/marine"

    def fetch_tide_data(self, jyo_cd, date_str):
        """
        Fetch tide height for a specific date and stadium
        date_str: YYYY-MM-DD
        """
        coords = STADIUM_COORDS.get(jyo_cd)
        if not coords:
            return None
            
        lat, lon = coords
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "sea_level_height",
            "start_date": date_str,
            "end_date": date_str
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            if response.status_code != 200:
                print(f"API Error {response.status_code}: {response.text}")
                return None
            
            data = response.json()
            if "hourly" in data:
                return data["hourly"]["sea_level_height"]
            return None
        except Exception as e:
            print(f"Exception fetching tide: {e}")
            return None

# Global instance
tide_api = TideAPI()

if __name__ == "__main__":
    # Test for Suminoe (12) - Close to now
    test_date = "2024-12-10" # Use a known past date for stability
    print(f"Fetching tide data for Suminoe (12) on {test_date}...")
    tide = tide_api.fetch_tide_data("12", test_date)
    if tide:
        print("Tide Heights (24h):")
        for h, val in enumerate(tide):
            print(f"{h:02d}:00 -> {val:.2f}m")
    else:
        print("Failed to fetch tide data.")
