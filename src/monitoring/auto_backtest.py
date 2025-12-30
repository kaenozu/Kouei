"""Automatic Backtest - Daily prediction accuracy tracking"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
from typing import Dict, List, Optional

from src.model.predictor import Predictor
from src.model.ensemble import get_ensemble
from src.features.preprocessing import preprocess, FEATURES
from src.utils.logger import logger

BACKTEST_LOG_PATH = "data/backtest_history.json"
DATA_PATH = "data/processed/race_data.csv"


def load_backtest_history() -> List[Dict]:
    """Load backtest history"""
    if os.path.exists(BACKTEST_LOG_PATH):
        with open(BACKTEST_LOG_PATH, 'r') as f:
            return json.load(f)
    return []


def save_backtest_history(history: List[Dict]):
    """Save backtest history"""
    os.makedirs(os.path.dirname(BACKTEST_LOG_PATH), exist_ok=True)
    with open(BACKTEST_LOG_PATH, 'w') as f:
        json.dump(history, f, indent=2)


def run_daily_backtest(target_date: Optional[str] = None) -> Dict:
    """Run backtest for a specific date"""
    if not os.path.exists(DATA_PATH):
        return {"error": "No data available"}
    
    df = pd.read_csv(DATA_PATH)
    
    # Default to yesterday
    if target_date is None:
        target_date = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
    
    # Filter to target date
    df_date = df[df['date'].astype(str) == target_date]
    
    if len(df_date) == 0:
        return {"error": f"No data for {target_date}"}
    
    # Preprocess
    df_date = preprocess(df_date.copy(), is_training=False)
    
    if len(df_date) == 0:
        return {"error": "No valid data after preprocessing"}
    
    # Get predictions
    try:
        ensemble = get_ensemble()
        X = df_date[FEATURES]
        predictions = ensemble.predict(X)
        df_date['pred_prob'] = predictions
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        return {"error": str(e)}
    
    # Calculate metrics
    results = {
        "date": target_date,
        "timestamp": datetime.now().isoformat(),
        "total_races": len(df_date) // 6,
        "total_entries": len(df_date)
    }
    
    # Accuracy metrics
    if 'target' in df_date.columns:
        # AUC
        from sklearn.metrics import roc_auc_score, accuracy_score
        try:
            results["auc"] = round(roc_auc_score(df_date['target'], df_date['pred_prob']), 4)
        except:
            results["auc"] = None
        
        # Top-1 accuracy (highest prob in each race)
        correct = 0
        total_races = 0
        
        for (date, jyo, race), group in df_date.groupby(['date', 'jyo_cd', 'race_no']):
            if len(group) == 6:
                pred_winner = group.loc[group['pred_prob'].idxmax(), 'boat_no']
                actual_winner_mask = group['target'] == 1
                if actual_winner_mask.any():
                    actual_winner = group.loc[actual_winner_mask.idxmax(), 'boat_no']
                    if pred_winner == actual_winner:
                        correct += 1
                total_races += 1
        
        results["top1_accuracy"] = round(correct / total_races, 4) if total_races > 0 else 0
        results["correct_predictions"] = correct
        results["total_races_evaluated"] = total_races
    
    # Confidence calibration
    prob_bins = [(0, 0.2), (0.2, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.0)]
    calibration = []
    
    for low, high in prob_bins:
        mask = (df_date['pred_prob'] >= low) & (df_date['pred_prob'] < high)
        subset = df_date[mask]
        if len(subset) > 0 and 'target' in subset.columns:
            calibration.append({
                "bin": f"{low:.1f}-{high:.1f}",
                "count": len(subset),
                "predicted_prob": round(subset['pred_prob'].mean(), 3),
                "actual_rate": round(subset['target'].mean(), 3)
            })
    
    results["calibration"] = calibration
    
    # ROI simulation (bet on highest prob per race)
    roi_results = simulate_betting(df_date)
    results.update(roi_results)
    
    return results


def simulate_betting(df: pd.DataFrame, bet_amount: int = 100) -> Dict:
    """Simulate betting on predictions"""
    total_bet = 0
    total_return = 0
    wins = 0
    
    for (date, jyo, race), group in df.groupby(['date', 'jyo_cd', 'race_no']):
        if len(group) != 6:
            continue
        
        # Bet on highest probability
        best_idx = group['pred_prob'].idxmax()
        best_boat = group.loc[best_idx]
        
        total_bet += bet_amount
        
        # Check if won
        if 'rank' in group.columns:
            rank = best_boat.get('rank', '')
            if str(rank) == '1':
                wins += 1
                # Use actual tansho odds if available
                tansho = best_boat.get('tansho', 0)
                if tansho and tansho > 0:
                    total_return += bet_amount * (tansho / 100)
                else:
                    total_return += bet_amount * 2.5  # Default
    
    roi = ((total_return - total_bet) / total_bet * 100) if total_bet > 0 else 0
    
    return {
        "sim_total_bet": total_bet,
        "sim_total_return": round(total_return, 0),
        "sim_roi": round(roi, 2),
        "sim_wins": wins
    }


def run_auto_backtest():
    """Run automatic daily backtest and save results"""
    history = load_backtest_history()
    
    # Get yesterday's date
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
    
    # Check if already processed
    if any(h.get("date") == yesterday for h in history):
        logger.info(f"Backtest for {yesterday} already exists")
        return
    
    # Run backtest
    result = run_daily_backtest(yesterday)
    
    if "error" not in result:
        history.append(result)
        # Keep last 90 days
        history = history[-90:]
        save_backtest_history(history)
        logger.info(f"Backtest completed for {yesterday}: AUC={result.get('auc')}, Top1={result.get('top1_accuracy')}")
    else:
        logger.warning(f"Backtest failed for {yesterday}: {result.get('error')}")
    
    return result


def get_backtest_summary(days: int = 30) -> Dict:
    """Get summary of recent backtest results"""
    history = load_backtest_history()
    
    if not history:
        return {"error": "No backtest history"}
    
    recent = history[-days:]
    
    aucs = [h.get("auc") for h in recent if h.get("auc") is not None]
    top1s = [h.get("top1_accuracy") for h in recent if h.get("top1_accuracy") is not None]
    rois = [h.get("sim_roi") for h in recent if h.get("sim_roi") is not None]
    
    return {
        "period_days": len(recent),
        "avg_auc": round(np.mean(aucs), 4) if aucs else None,
        "avg_top1_accuracy": round(np.mean(top1s), 4) if top1s else None,
        "avg_roi": round(np.mean(rois), 2) if rois else None,
        "trend": recent[-7:] if len(recent) >= 7 else recent,
        "last_update": recent[-1].get("timestamp") if recent else None
    }


if __name__ == "__main__":
    result = run_auto_backtest()
    print(json.dumps(result, indent=2, ensure_ascii=False))
