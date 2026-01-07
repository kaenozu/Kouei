"""
SNSメディアコレクター - 選手インタビュー sentiment分析
"""
import asyncio
import aiohttp
import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any
from src.utils.logger import logger

class SocialMediaCollector:
    """SNS情報収集・分析器"""
    
    def __init__(self):
        self.keywords = [
            "競艇", "ボートレース", "選手", "練習", "調子", "天候", "波", 
            "インコース", "アウトコース", "モーター", "出走", "体調"
        ]
        self.stadiums = [
            "平和島", "多摩川", "江戸川", "浜名湖", "蒲郡", "常滑", 
            "津", "三国", "びわこ", "住之江", "尼崎", "鳴門", "丸亀", "児島", "宮島", "徳山"
        ]
        
    async def collect_twitter_data(self, query: str, limit: int = 100) -> List[Dict]:
        """Twitterデータ収集（サンプル実装）"""
        sample_data = [
            {
                "text": "平和島は今日波が穏やかでインコースが有利かも",
                "timestamp": datetime.now().isoformat(),
                "author": "艇ファンA",
                "hashtags": ["#競艇", "#平和島"],
                "sentiment": 0.3
            },
            {
                "text": "選手〇〇の調子絶好調！連勝期待大",
                "timestamp": (datetime.now() - timedelta(hours=2)).isoformat(),
                "author": "レース観戦者B",
                "hashtags": ["#競艇", "#選手"],
                "sentiment": 0.8
            },
            {
                "text": "今日の蒲郡は風が強くて外が苦しいかも",
                "timestamp": (datetime.now() - timedelta(hours=4)).isoformat(),
                "author": "競艇アナリストC",
                "hashtags": ["#競艇", "#蒲郡"],
                "sentiment": -0.2
            }
        ]
        return sample_data[:limit]
    
    def analyze_sentiment(self, text: str) -> float:
        """テキストのsentiment分析（-1から1の範囲）"""
        # 簡易sentiment分析（実際にはTextBlobなど使用）
        positive_words = ["好調", "絶好調", "有利", "期待", "勝利", "連勝"]
        negative_words = ["苦しい", "不利", "悪い", "厳しい", "困難", "残念"]
        
        score = 0.0
        for word in positive_words:
            if word in text:
                score += 0.3
        
        for word in negative_words:
            if word in text:
                score -= 0.3
        
        return round(max(-1, min(1, score)), 3)
    
    def extract_racer_info(self, text: str) -> List[str]:
        """テキストから選手名を抽出（簡易実装）"""
        # 実際には選手名データベースとのマッチングが必要
        sample_racers = ["選手A", "選手B", "選手C", "選手D", "選手E", "選手F"]
        
        found = []
        for racer in sample_racers:
            if racer in text:
                found.append(racer)
        return found
    
    def extract_stadium_info(self, text: str) -> str:
        """テキストから競艇場名を抽出"""
        for stadium in self.stadiums:
            if stadium in text:
                return stadium
        return "不明"
    
    async def collect_and_analyze(self, hours: int = 24) -> Dict[str, Any]:
        """データ収集と分析実行"""
        logger.info(f"Collecting social media data for last {hours} hours...")
        
        # データ収集
        social_data = await self.collect_twitter_data("", limit=200)
        
        analyzed_posts = []
        sentiment_by_stadium = {}
        racer_mentions = {}
        
        for post in social_data:
            # sentiment分析
            sentiment = self.analyze_sentiment(post["text"])
            post["analyzed_sentiment"] = sentiment
            
            # 選手情報抽出
            racers = self.extract_racer_info(post["text"])
            for racer in racers:
                if racer not in racer_mentions:
                    racer_mentions[racer] = {"mentions": 0, "sentiment_sum": 0}
                racer_mentions[racer]["mentions"] += 1
                racer_mentions[racer]["sentiment_sum"] += sentiment
            
            # 競艇場ごとのsentiment
            stadium = self.extract_stadium_info(post["text"])
            if stadium != "不明":
                if stadium not in sentiment_by_stadium:
                    sentiment_by_stadium[stadium] = []
                sentiment_by_stadium[stadium].append(sentiment)
            
            analyzed_posts.append(post)
        
        # 集計
        summary = {
            "total_posts": len(analyzed_posts),
            "average_sentiment": sum(p["analyzed_sentiment"] for p in analyzed_posts) / len(analyzed_posts),
            "sentiment_by_stadium": {
                stadium: sum(sentiments) / len(sentiments)
                for stadium, sentiments in sentiment_by_stadium.items() if sentiments
            },
            "racer_sentiment": {
                racer: {
                    "mentions": data["mentions"],
                    "average_sentiment": data["sentiment_sum"] / data["mentions"]
                }
                for racer, data in racer_mentions.items()
            },
            "collection_time": datetime.now().isoformat()
        }
        
        logger.info(f"Analyzed {len(analyzed_posts)} social media posts")
        return summary

class WeatherDataEnhancer:
    """天候データ拡張器"""
    
    async def get_detailed_weather(self, stadium: str) -> Dict[str, Any]:
        """競艇場の詳細天候情報取得"""
        # 競艇場と都市のマッピング
        stadium_to_city = {
            "平和島": "Tokyo",
            "多摩川": "Tokyo", 
            "江戸川": "Tokyo",
            "浜名湖": "Shizuoka",
            "蒲郡": "Aichi",
            "常滑": "Aichi",
            "津": "Mie",
            "三国": "Fukui",
            "びわこ": "Shiga",
            "住之江": "Osaka",
            "尼崎": "Hyogo",
            "兒島": "Okayama",
            "宮島": "Hiroshima",
            "徳山": "Yamaguchi"
        }
        
        # サンプル詳細天候データ
        return {
            "stadium": stadium,
            "temperature": 18.5,
            "humidity": 65,
            "wind_speed": 3.2,
            "wind_direction": "NE",
            "wind_gusts": 5.8,
            "visibility": 10,
            "pressure": 1013,
            "wave_height": 0.8,
            "wave_period": 4,
            "water_temperature": 16.2,
            "precipitation_last_hour": 0,
            "precipitation_probability": 10,
            "cloud_cover": 40,
            "weather_condition": "partly_cloudy",
            "timestamp": datetime.now().isoformat()
        }
    
    def analyze_race_impact(self, weather_data: Dict[str, Any]) -> Dict[str, Any]:
        """天候がレースに与える影響分析"""
        analysis = {
            "overall_favorability": 0.5,
            "course_advantages": {str(i): 1.0 for i in range(1, 7)},
            "risk_factors": [],
            "recommendations": []
        }
        
        # 風速影響
        wind_speed = weather_data["wind_speed"]
        if wind_speed > 6:
            analysis["risk_factors"].append("強風で外モコ不利")
            analysis["course_advantages"]["1"] *= 1.1
            analysis["course_advantages"]["2"] *= 1.05
            analysis["course_advantages"]["6"] *= 0.9
            analysis["overall_favorability"] *= 0.8
            analysis["recommendations"].append("インコース狙い")
        
        # 波高影響
        wave_height = weather_data["wave_height"]
        if wave_height > 2:
            analysis["risk_factors"].append("高波で荒れた水面")
            analysis["course_advantages"]["1"] *= 1.15
            analysis["course_advantages"]["6"] *= 0.85
            analysis["overall_favorability"] *= 0.85
        
        return analysis

# 実行用ハンドラー
async def run_social_collection():
    """SNS収集実行"""
    collector = SocialMediaCollector()
    results = await collector.collect_and_analyze(hours=6)
    
    import json
    # 結果を保存
    output_path = "data/social_analysis.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Social media analysis saved to {output_path}")
    return results
