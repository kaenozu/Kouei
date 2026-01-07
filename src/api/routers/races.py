"""Races Router - Race listing and info endpoints"""
from fastapi import APIRouter, Depends, Query
from typing import Optional
import pandas as pd
import os
from datetime import datetime

from src.api.dependencies import get_dataframe, get_cache, STADIUM_MAP, get_stadium_name
from src.parser.html_parser import ProgramParser
from src.cache.redis_client import RedisCache
from src.utils.logger import logger

router = APIRouter(prefix="/api", tags=["races"])


@router.get("/stadiums")
async def get_stadiums():
    """Get list of all stadiums"""
    return [{"code": k, "name": v} for k, v in STADIUM_MAP.items()]


@router.get("/races")
async def get_races(
    date: str = Query(..., pattern=r"^\d{8}$"),
    jyo: str = Query(..., pattern=r"^\d{1,2}$"),
    cache: RedisCache = Depends(get_cache)
):
    """Get race list for a stadium on a given date"""
    try:
        jyo_str = jyo.zfill(2)
        cache_key = f"races:{date}:{jyo_str}"
        
        # Check cache
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        df = get_dataframe()
        if df.empty:
            return []
        
        df['jyo_cd'] = df['jyo_cd'].astype(str).str.zfill(2)
        df['date'] = df['date'].astype(str)
        
        stadium_data = df[(df['date'] == date) & (df['jyo_cd'] == jyo_str)]
        
        # Get start times from HTML
        start_times = _get_start_times(date, jyo_str)

        races = []
        for race_no in range(1, 13):
            race_df = stadium_data[stadium_data['race_no'] == race_no]
            
            status = 'no_data'
            has_prediction = False
            start_time = start_times.get(race_no)
            
            if not race_df.empty:
                if race_df['rank'].notna().any():
                    status = 'finished'
                else:
                    status = 'awaiting_result'
                
                if race_df['exhibition_time'].notna().any():
                    has_prediction = True
                
                if not start_time and 'start_time' in race_df.columns:
                    val = race_df['start_time'].iloc[0]
                    if pd.notna(val):
                        start_time = str(val)
            
            races.append({
                "race_no": race_no,
                "status": status,
                "has_prediction": has_prediction,
                "start_time": start_time
            })
        
        # Cache for 2 minutes
        cache.set(cache_key, races, ttl=120)
        
        return races
    except Exception as e:
        logger.error(f"Get races error: {e}")
        return {"error": str(e)}


@router.get("/today")
async def get_today_races(cache: RedisCache = Depends(get_cache)):
    """Get all races happening today across all stadiums"""
    try:
        cache_key = "races:today"
        
        # Check cache (short TTL for real-time feel)
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        today = datetime.now().strftime("%Y%m%d")
        
        df = get_dataframe()
        if df.empty:
            return {"meta": {"now": datetime.now().strftime("%H:%M"), "total": 0}, "races": []}
        
        df['jyo_cd'] = df['jyo_cd'].astype(str).str.zfill(2)
        df['date'] = df['date'].astype(str)
        
        today_data = df[df['date'] == today]
        active_stadiums = today_data['jyo_cd'].unique()
        
        now = datetime.now()
        now_str = now.strftime("%H:%M")
        
        all_races = []
        
        for jyo_cd in active_stadiums:
            stadium_data = today_data[today_data['jyo_cd'] == jyo_cd]
            start_times = _get_start_times(today, jyo_cd)
            
            for race_no in range(1, 13):
                race_df = stadium_data[stadium_data['race_no'] == race_no]
                
                if race_df.empty:
                    continue
                
                status = 'no_data'
                has_prediction = False
                start_time = start_times.get(race_no)
                
                if not start_time and 'start_time' in race_df.columns:
                    val = race_df['start_time'].iloc[0]
                    if pd.notna(val):
                        start_time = str(val)
                
                if start_time:
                    start_time = start_time.strip()

                # Determine status
                if race_df['rank'].notna().any():
                    status = 'finished'
                elif start_time and start_time < now_str:
                    status = 'finished'
                else:
                    status = 'awaiting_result'
                
                if race_df['exhibition_time'].notna().any():
                    has_prediction = True
                
                # Race Name
                race_name = _get_race_name(race_df, today, jyo_cd, race_no)
                
                # Racers
                racers = []
                if 'racer_name' in race_df.columns:
                    racer_rows = race_df[['boat_no', 'racer_name']].dropna().sort_values('boat_no')
                    racers = [str(name) for name in racer_rows['racer_name'].tolist()]
                
                if start_time:
                    all_races.append({
                        "jyo_cd": jyo_cd,
                        "jyo_name": STADIUM_MAP.get(jyo_cd, jyo_cd),
                        "race_no": race_no,
                        "race_name": race_name,
                        "start_time": start_time,
                        "status": status,
                        "has_prediction": has_prediction,
                        "racers": racers
                    })
        
        # Sort: upcoming first, then finished
        upcoming = [r for r in all_races if r['status'] != 'finished']
        finished = [r for r in all_races if r['status'] == 'finished']
        
        upcoming.sort(key=lambda x: x['start_time'])
        finished.sort(key=lambda x: x['start_time'])
        
        result = {
            "meta": {
                "now": now_str,
                "total": len(all_races)
            },
            "races": upcoming + finished
        }
        
        # Cache for 1 minute
        cache.set(cache_key, result, ttl=60)
        
        return result
    except Exception as e:
        logger.error(f"Get today races error: {e}")
        return {"error": str(e)}


def _get_start_times(date: str, jyo_cd: str) -> dict:
    """Get start times from HTML file"""
    start_times = {}
    raw_program_p1 = os.path.join("data", "raw", date, jyo_cd, "program_1.html")
    if os.path.exists(raw_program_p1):
        try:
            with open(raw_program_p1, 'r', encoding='utf-8') as f:
                start_times = ProgramParser.parse_start_times(f.read())
        except Exception as e:
            logger.warning(f"Failed to parse start times: {e}")
    return start_times


def _get_race_name(race_df: pd.DataFrame, date: str, jyo_cd: str, race_no: int) -> str:
    """Get race name from DataFrame or HTML"""
    race_name = ""
    if 'race_name' in race_df.columns:
        val = race_df['race_name'].iloc[0]
        if pd.notna(val):
            race_name = str(val)
    
    if not race_name:
        raw_program = os.path.join("data", "raw", date, jyo_cd, f"program_{race_no}.html")
        if os.path.exists(raw_program):
            try:
                with open(raw_program, 'r', encoding='utf-8') as f:
                    race_name = ProgramParser.parse_race_name(f.read())
            except:
                pass
    
    return race_name
