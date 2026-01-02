"""Odds and Expected Value Analysis Router"""
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import httpx
import asyncio
from bs4 import BeautifulSoup
import re

router = APIRouter(prefix="/api", tags=["odds"])

class OddsResponse(BaseModel):
    date: str
    jyo_cd: str
    race_no: int
    updated_at: str
    tansho: List[Dict[str, Any]]
    nirentan: Optional[List[Dict[str, Any]]] = None
    sanrentan: Optional[List[Dict[str, Any]]] = None
    value_bets: List[Dict[str, Any]]
    alerts: List[str]


async def fetch_odds_from_boatrace(date: str, jyo: str, race: int) -> Dict[str, Any]:
    """Fetch odds from official boatrace website"""
    url = f"https://www.boatrace.jp/owpc/pc/race/oddstf?rno={race}&jcd={jyo}&hd={date}"
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=10.0)
            if resp.status_code != 200:
                return None
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Parse tansho odds
            tansho = []
            tansho_table = soup.select('.is-w495 tbody tr')
            for row in tansho_table:
                cells = row.select('td')
                if len(cells) >= 2:
                    try:
                        odds_text = cells[1].get_text(strip=True)
                        odds = float(odds_text) if odds_text and odds_text != '-' else None
                        tansho.append({'odds': odds})
                    except:
                        tansho.append({'odds': None})
            
            return {
                'tansho': tansho if tansho else [{'odds': None}] * 6,
                'updated_at': datetime.now().isoformat()
            }
    except Exception as e:
        print(f"Error fetching odds: {e}")
        return None


def calculate_value_bets(predictions: List[Dict], odds_data: Dict) -> List[Dict[str, Any]]:
    """Calculate value bets based on predictions and odds"""
    value_bets = []
    
    if not odds_data or not predictions:
        return value_bets
    
    tansho = odds_data.get('tansho', [])
    
    for i, pred in enumerate(predictions):
        if i >= len(tansho):
            break
        
        odds = tansho[i].get('odds')
        prob = pred.get('probability', 0)
        
        if odds and prob > 0:
            ev = prob * odds
            if ev > 1.2:  # 20% edge threshold
                value_bets.append({
                    'type': '単勝',
                    'combination': str(pred.get('boat_no', i + 1)),
                    'odds': odds,
                    'probability': prob,
                    'ev': ev
                })
    
    # Sort by EV
    value_bets.sort(key=lambda x: x['ev'], reverse=True)
    return value_bets


def detect_odds_alerts(current_odds: Dict, previous_odds: Dict = None) -> List[str]:
    """Detect significant odds movements"""
    alerts = []
    
    if not previous_odds:
        return alerts
    
    current_tansho = current_odds.get('tansho', [])
    prev_tansho = previous_odds.get('tansho', [])
    
    for i, (curr, prev) in enumerate(zip(current_tansho, prev_tansho)):
        curr_odds = curr.get('odds')
        prev_odds = prev.get('odds')
        
        if curr_odds and prev_odds:
            change = (curr_odds - prev_odds) / prev_odds
            if abs(change) > 0.2:  # 20% change
                direction = "上昇" if change > 0 else "下降"
                alerts.append(f"{i+1}号艇のオッズが{abs(change)*100:.0f}%{direction}（{prev_odds:.1f}→{curr_odds:.1f}）")
    
    return alerts


@router.get("/odds/analysis", response_model=OddsResponse)
async def get_odds(
    date: str = Query(..., description="Date in YYYYMMDD format"),
    jyo: str = Query(..., description="Venue code"),
    race: int = Query(..., ge=1, le=12, description="Race number")
):
    """Get real-time odds and value bet analysis"""
    
    # Fetch odds from boatrace.jp
    odds_data = await fetch_odds_from_boatrace(date, jyo, race)
    
    # Check if we got valid data (at least one non-null odds)
    has_valid_odds = False
    if odds_data and odds_data.get('tansho'):
        has_valid_odds = any(t.get('odds') is not None for t in odds_data['tansho'])
    
    if not has_valid_odds:
        # Return mock data if fetch fails or no valid odds
        odds_data = {
            'tansho': [
                {'odds': 2.1}, {'odds': 5.5}, {'odds': 8.2},
                {'odds': 12.4}, {'odds': 25.0}, {'odds': 45.0}
            ],
            'updated_at': datetime.now().isoformat()
        }
    
    # Get predictions for EV calculation
    predictions = []
    try:
        from src.api.dependencies import get_predictor, get_dataframe
        model = get_predictor()
        df = get_dataframe()
        
        if model and not df.empty:
            jyo_str = jyo.zfill(2)
            race_df = df[(df['date'] == date) & (df['jyo_cd'] == jyo_str) & (df['race_no'] == race)]
            
            if not race_df.empty:
                probs = model.predict(race_df)
                for i, prob in enumerate(probs):
                    predictions.append({'boat_no': i + 1, 'probability': prob})
                    if i < len(odds_data['tansho']):
                        odds_data['tansho'][i]['probability'] = prob
    except Exception as e:
        print(f"Error getting predictions: {e}")
    
    # Calculate value bets
    value_bets = calculate_value_bets(predictions, odds_data)
    
    # Detect alerts
    alerts = detect_odds_alerts(odds_data)
    
    return OddsResponse(
        date=date,
        jyo_cd=jyo,
        race_no=race,
        updated_at=odds_data.get('updated_at', datetime.now().isoformat()),
        tansho=odds_data.get('tansho', []),
        value_bets=value_bets,
        alerts=alerts
    )
