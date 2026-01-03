"""
AI Concierge - Intelligent race analysis and betting advisor
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class AIConcierge:
    """AIコンシェルジュ - レース分析・購入アドバイザー"""
    
    def __init__(self):
        self.greetings = [
            "今日のレース分析ですね、お任せください！",
            "AIがデータを分析していますので、少々お待ちを...",
            "勝率の高いレースを見つけ出しますね"
        ]
        
    def analyze_race(self, race_data: pd.DataFrame) -> Dict[str, Any]:
        """レース詳細分析"""
        if race_data.empty:
            return {"error": "レースデータがありません"}
        
        analysis = {}
        
        # 1. 基本情報
        analysis['race_info'] = {
            "date": race_data['date'].iloc[0],
            "venue": race_data['jyo_name'].iloc[0] if 'jyo_name' in race_data.columns else f"会場{race_data['jyo_cd'].iloc[0]}",
            "race_no": int(race_data['race_no'].iloc[0]),
            "weather": f"水温{race_data['water_temperature'].iloc[0]}°C、風速{race_data['wind_speed'].iloc[0]}m/s"
        }
        
        # 2. 上位予想艇分析
        top_boats = race_data.nlargest(3, 'pred_prob')
        analysis['top_boats'] = []
        
        for _, boat in top_boats.iterrows():
            boat_analysis = {
                "boat_no": int(boat['boat_no']),
                "racer_name": boat.get('racer_name', "不明"),
                "win_rate": boat['racer_win_rate'],
                "predicted_prob": boat['pred_prob'],
                "confidence": self._get_confidence(boat['pred_prob']),
                "exhibition_time": boat.get('exhibition_time', 0),
                "reasons": self._analyze_boat_strengths(boat)
            }
            analysis['top_boats'].append(boat_analysis)
        
        # 3. レース傾向分析
        analysis['race_trends'] = self._analyze_race_patterns(race_data)
        
        # 4. 購入戦略提案
        analysis['betting_advice'] = self._generate_betting_advice(analysis['top_boats'], analysis['race_trends'])
        
        # 5. リスク評価
        analysis['risk_assessment'] = self._assess_race_risk(race_data)
        
        return analysis
    
    def get_daily_digest(self, date: str) -> Dict[str, Any]:
        """日次ダイジェスト作成"""
        try:
            # データ取得
            from src.api.dependencies import get_dataframe, get_predictor
            
            df = get_dataframe()
            if df.empty:
                return {"error": "データがありません"}
            
            # 対象日付に絞り込み
            today_df = df[df['date'].astype(str) == date].copy()
            
            if today_df.empty:
                return {"message": f"{date}のレースはありません"}
            
            # 各レース分析
            race_analyses = []
            for (jyo, race_no), race_group in today_df.groupby(['jyo_cd', 'race_no']):
                analysis = self.analyze_race(race_group)
                if 'error' not in analysis:
                    race_analyses.append(analysis)`
            
            # サマリー生成
            summary = {
                "date": date,
                "total_races": len(race_analyses),
                "top_confidence_races": self._get_high_confidence_races(race_analyses),
                "venue_overview": self._create_venue_summary(today_df),
                "market_trends": self._analyze_market_trends(today_df),
                "daily_advice": self._generate_daily_advice(race_analyses)
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to generate daily digest: {e}")
            return {"error": str(e)}
    
    def respond_to_question(self, question: str, context: Dict = None) -> Dict:
        """質問に回答"""
        question = question.lower().strip()
        
        # 質問タイプ判定
        if "勝率" in question or "確率" in question:
            return self._answer_probability_question(question, context)
        elif "購入" in question or "買い目" in question:
            return self._answer_betting_question(question, context)
        elif "天候" in question or "天気" in question:
            return self._answer_weather_question(question, context)
        elif "選手" in question or "レーサー" in question:
            return self._answer_racer_question(question, context)
        else:
            return self._answer_general_question(question, context)
    
    def _get_confidence(self, prob: float) -> str:
        """確信度レベル判定"""
        if prob >= 0.9:
            return "S（超安定）"
        elif prob >= 0.8:
            return "A（高確率）"
        elif prob >= 0.7:
            return "B（安定）"
        elif prob >= 0.6:
            return "C（平常）"
        else:
            return "D（低確率）"
    
    def _analyze_boat_strengths(self, boat: pd.Series) -> List[str]:
        """艇強み分析"""
        strengths = []
        
        # 勝率
        if boat['racer_win_rate'] > 6.0:
            strengths.append(f"勝率{boat['racer_win_rate']:.1f}%の強豪")
        elif boat['racer_win_rate'] > 4.5:
            strengths.append(f"勝率{boat['racer_win_rate']:.1f}%の中堅")
        
        # スタート
        exhibition_time = boat.get('exhibition_time', 0)
        if exhibition_time and exhibition_time < 6.8:
            strengths.append("スタートが得意")
        
        # コース有利性
        boat_no = int(boat['boat_no'])
        if boat_no <= 2:
            strengths.append(f"内枠{boat_no}艇で有利")
        
        return strengths[:3]  # 最大3件表示
    
    def _analyze_race_patterns(self, race_data: pd.DataFrame) -> Dict:
        """レースパターン分析"""
        patterns = {}
        
        # 勝率分布
        win_rates = race_data['racer_win_rate']
        patterns['win_rate_distribution'] = {
            "high_power": len(win_rates[win_rates > 6.0]),
            "mid_power": len(win_rates[(win_rates >= 4.0) & (win_rates <= 6.0)]),
            "low_power": len(win_rates[win_rates < 4.0])
        }
        
        # 競争レベル
        avg_win_rate = win_rates.mean()
        if avg_win_rate > 5.5:
            competition_level = "激戦"
        elif avg_win_rate > 4.5:
            competition_level = "平均的"
        else:
            competition_level = "緩やか"
        
        patterns['competition_level'] = competition_level
        
        # 天候影響評価
        weather = race_data.iloc[0]
        wind_speed = weather.get('wind_speed', 0)
        wave_height = weather.get('wave_height', 0)
        
        if wind_speed > 5 or wave_height > 3:
            patterns['weather_impact'] = "天候不順で波乱注意"
        elif wind_speed > 3 or wave_height > 2:
            patterns['weather_impact'] = "天候やや悪い"
        else:
            patterns['weather_impact'] = "天候良好"
        
        return patterns
    
    def _generate_betting_advice(self, top_boats: List[Dict], race_trends: Dict) -> Dict:
        """購入戦略提案"""
        advice = {"main_strategy": "", "alternatives": []}
        
        if not top_boats:
            advice["main_strategy"] = "本レースは見送りをおすすめ"
            return advice
        
        top_boat = top_boats[0]
        
        if top_boat['confidence'].startswith('S') or top_boat['confidence'].startswith('A'):
            # 高確率艇あり
            advice["main_strategy"] = (
                f"{top_boat['boat_no']}艇単勝に注目"
                f"（予想的中率{top_boat['predicted_prob']*100:.1f}%）"
            )
            
            # 2位艇との連頭も提案
            if len(top_boats) >= 2:
                second_boat = top_boats[1]
                if top_boat['boat_no'] != second_boat['boat_no']:
                    advice["alternatives"].append(
                        f"{top_boat['boat_no']}-{second_boat['boat_no']}連頭も安定"
                    )
        
        else:
            # Bランク以下の場合
            if race_trends['competition_level'] == "激戦":
                advice["main_strategy"] = "複数馬券で分散投資がおすすめ"
            else:
                advice["main_strategy"] = f"{top_boat['boat_no']}艇を中心に流しが良いかと"
        
        return advice
    
    def _assess_race_risk(self, race_data: pd.DataFrame) -> Dict:
        """レースリスク評価"""
        risk_level = "low"  # low, medium, high
        
        # 天候リスク
        weather = race_data.iloc[0]
        wind_speed = weather.get('wind_speed', 0)
        wave_height = weather.get('wave_height', 0)
        
        if wind_speed > 8 or wave_height > 5:
            risk_level = "high"
        elif wind_speed > 5 or wave_height > 3:
            risk_level = "medium"
        
        # 競争激しさ
        avg_win_rate = race_data['racer_win_rate'].mean()
        win_rate_std = race_data['racer_win_rate'].std()
        
        if avg_win_rate > 5.5 and win_rate_std < 1.5:
            risk_level = max(risk_level, "medium")  # 均等な強豪戦
        
        return {
            "level": risk_level,
            "factors": {
                "weather": f"風速{wind_speed}m/s、波高{wave_height}cm",
                "competition": f"平均勝率{avg_win_rate:.1f}%",
                "distribution": f"勝率標準偏差{win_rate_std:.1f}%"
            }
        }
    
    def _get_high_confidence_races(self, race_analyses: List[Dict]) -> List[Dict]:
        """高確信度レース抽出"""
        high_confidence = []
        
        for analysis in race_analyses:
            if analysis['top_boats'] and analysis['top_boats'][0]['confidence'] in ['S', 'A']:
                high_confidence.append({
                    "venue": analysis['race_info']['venue'],
                    "race_no": analysis['race_info']['race_no'],
                    "top_boat": analysis['top_boats'][0],
                    "confidence": analysis['top_boats'][0]['confidence']
                })
        
        return sorted(high_confidence, key=lambda x: x['top_boat']['predicted_prob'], reverse=True)
    
    def _create_venue_summary(self, today_df: pd.DataFrame) -> Dict:
        """会場サマリー生成"""
        venue_summary = {}
        
        for venue_code, venue_data in today_df.groupby('jyo_cd'):
            venue_summary[venue_code] = {
                "total_races": len(venue_data['race_no'].unique()),
                "avg_win_rate": venue_data['racer_win_rate'].mean(),
                "high_confidence_count": len(venue_data[venue_data['pred_prob'] > 0.8])
            }
        
        return venue_summary
    
    def _analyze_market_trends(self, today_df: pd.DataFrame) -> Dict:
        """市場トレンド分析"""
        return {
            "avg_prediction_rate": today_df['pred_prob'].mean(),
            "high_prediction_rate_races": len(today_df[today_df['pred_prob'] > 0.8]),
            "total_opportunities": len(today_df)
        }
    
    def _generate_daily_advice(self, race_analyses: List[Dict]) -> str:
        """日次アドバイス生成"""
        if not race_analyses:
            return "本日はレースがありません"
        
        high_conf_count = len([r for r in race_analyses if r['top_boats'] and r['top_boats'][0]['confidence'] in ['S', 'A']])
        total_races = len(race_analyses)
        
        if high_conf_count >= 3:
            return f"本日は{high_conf_count}レースが高確率！狙い目です"
        elif high_conf_count >= 1:
            return f"{high_conf_count}レースが高確率ですが、他は慎重に"
        else:
            return "高確率レース少なめ、見送りの勇気も重要です"
    
    def _answer_probability_question(self, question: str, context: Dict) -> Dict:
        """確率質問に回答"""
        return {
            "type": "probability",
            "answer": "AI予測は過去データを基に計算しています。70%以上であれば買い目候補です",
            "confidence": "medium"
        }
    
    def _answer_betting_question(self, question: str, context: Dict) -> Dict:
        """購入質問に回答"""
        return {
            "type": "betting",
            "answer": "高確率艇の単勝が基本ですが、連頭も検討しましょう。分散投資がおすすめです",
            "confidence": "high"
        }
    
    def _answer_weather_question(self, question: str, context: Dict) -> Dict:
        """天候質問に回答"""
        return {
            "type": "weather",
            "answer": "天候不順は波乱要因です。スタートの良い艇が有利になります",
            "confidence": "medium"
        }
    
    def _answer_racer_question(self, question: str, context: Dict) -> Dict:
        """選手質問に回答"""
        return {
            "type": "racer",
            "answer": "勝率だけでなく、モーターやスタートタイムも総合評価しています",
            "confidence": "high"
        }
    
    def _answer_general_question(self, question: str, context: Dict) -> Dict:
        """一般質問に回答"""
        greetings = [
            "質問ありがとうございます。分析対象のレースデータで詳しくお答えしますね",
            "良い質問ですね。AI予測の仕組みを詳しくご説明します",
            "難しい質問ですね。データから考えてみましょう"
        ]
        
        return {
            "type": "general",
            "answer": np.random.choice(greetings),
            "confidence": "low"
        }


# グローバルインスタンス
ai_concierge = AIConcierge()
