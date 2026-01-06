"""LLM-Enhanced Prediction Explainer

SHAP値をLLMで人間が理解しやすい説明に変換する。
"""
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import asyncio

from src.config.settings import settings
from src.utils.logger import get_logger

logger = get_logger()

# Try to import LLM clients
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


# Feature name translations (Japanese)
FEATURE_TRANSLATIONS = {
    'winrate': '勝率',
    'recent_win_rate': '最近の勝率',
    'recent_avg_rank': '最近の平均着順',
    'recent_rentai_rate': '連対率',
    'motor_no2rate': 'モーター2連対率',
    'boat_no2rate': 'ボート2連対率',
    'exhibition_time': '展示タイム',
    'course_winrate': 'コース勝率',
    'course_winrate_synergy': 'コース相性',
    'avg_start_timing': '平均STタイミング',
    'racer_class_encoded': '選手ランク',
    'field_strength': '出走メンバー強度',
    'field_strength_std': '出走メンバーばらつき',
    'is_strong_wind': '強風フラグ',
    'is_rough_conditions': '荒れコンディション',
    'tailwind_outer_benefit': '追い風アウト有利',
    'equipment_score': '機材スコア',
    'equipment_total': '機材総合点',
    'equipment_quality': '機材品質',
    'fast_exhibition': '展示好調',
    'slow_exhibition': '展示不調',
    'is_competitive_race': '接戦予想',
    'wind_speed': '風速',
    'wave_height': '波高',
    'temperature': '気温',
    'humidity': '湿度',
    'season_sin': '季節(sin)',
    'season_cos': '季節(cos)',
    'is_winter': '冬季',
    'is_summer': '夏季',
    'avg_opponent_winrate': '対戦相手平均勝率',
    'winrate_advantage': '勝率優位度',
    'is_top_racer_in_race': '最強レーサー',
}


@dataclass
class PredictionExplanation:
    """Structure for prediction explanation"""
    boat_no: int
    racer_name: str
    probability: float
    shap_values: List[Tuple[str, float]]  # Top SHAP features
    llm_explanation: Optional[str] = None
    summary: Optional[str] = None


class LLMExplainer:
    """Generate human-readable explanations using LLM"""
    
    SYSTEM_PROMPT = """あなたは競艇予測AIの説明アシスタントです。
機械学習モデルの予測結果とSHAP値（各特徴量の寄与度）を、
競艇ファンが理解しやすい日本語の説明に変換してください。

説明のポイント:
1. 専門用語を避け、分かりやすい言葉で説明
2. 数値よりも「高い/低い」「有利/不利」など定性的な表現を使用
3. 予測の根拠となる主要な要因を2-3点に絞る
4. 100文字程度の簡潔な説明にまとめる
"""
    
    def __init__(self):
        self.provider = settings.llm_provider.lower()
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """Initialize LLM client based on settings"""
        if self.provider == "openai" and OPENAI_AVAILABLE and settings.openai_api_key:
            self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
            logger.info("LLM Explainer: OpenAI client initialized")
        elif self.provider == "anthropic" and ANTHROPIC_AVAILABLE and settings.anthropic_api_key:
            self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
            logger.info("LLM Explainer: Anthropic client initialized")
        else:
            logger.info("LLM Explainer: No provider, using rule-based fallback")
    
    def _translate_feature(self, feature_name: str) -> str:
        """Translate feature name to Japanese"""
        return FEATURE_TRANSLATIONS.get(feature_name, feature_name)
    
    def _build_prompt(self, explanation: PredictionExplanation) -> str:
        """Build prompt for LLM"""
        prompt = f"""以下の予測結果を説明してください。

【対象】
{explanation.boat_no}号艇 {explanation.racer_name}
予測勝率: {explanation.probability*100:.1f}%

【主要な予測根拠（SHAP値）】
"""
        for feature, value in explanation.shap_values[:5]:
            translated = self._translate_feature(feature)
            direction = "上昇" if value > 0 else "下降"
            impact = abs(value)
            prompt += f"- {translated}: 勝率を{impact:.2f}ポイント{direction}させる\n"
        
        prompt += "\n上記を踏まえ、この選手の予測根拠を簡潔に説明してください。"
        return prompt
    
    async def explain_async(self, explanation: PredictionExplanation) -> str:
        """Generate explanation asynchronously"""
        if self.client is None:
            return self._generate_rule_based(explanation)
        
        prompt = self._build_prompt(explanation)
        
        try:
            if self.provider == "openai":
                response = await self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": self.SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=200,
                    temperature=0.5
                )
                return response.choices[0].message.content
            
            elif self.provider == "anthropic":
                response = await self.client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=200,
                    system=self.SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
        
        except Exception as e:
            logger.error(f"LLM explanation failed: {e}")
            return self._generate_rule_based(explanation)
    
    def explain(self, explanation: PredictionExplanation) -> str:
        """Synchronous wrapper"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    return pool.submit(
                        asyncio.run, self.explain_async(explanation)
                    ).result()
            else:
                return asyncio.run(self.explain_async(explanation))
        except Exception as e:
            logger.error(f"Explain failed: {e}")
            return self._generate_rule_based(explanation)
    
    def _generate_rule_based(self, exp: PredictionExplanation) -> str:
        """Rule-based fallback explanation"""
        parts = []
        
        # Analyze top factors
        for feature, value in exp.shap_values[:3]:
            translated = self._translate_feature(feature)
            
            if 'winrate' in feature or 'win_rate' in feature:
                if value > 0:
                    parts.append(f"{translated}が高い")
                else:
                    parts.append(f"{translated}が低め")
            
            elif 'motor' in feature or 'boat' in feature:
                if value > 0:
                    parts.append("機材状態が良好")
                else:
                    parts.append("機材がやや不安")
            
            elif 'exhibition' in feature:
                if value > 0:
                    parts.append("展示タイムが好調")
                else:
                    parts.append("展示の動きに課題")
            
            elif 'course' in feature:
                if value > 0:
                    parts.append(f"{exp.boat_no}コースとの相性◎")
                else:
                    parts.append(f"{exp.boat_no}コースはやや苦手")
            
            elif 'wind' in feature or 'wave' in feature or 'rough' in feature:
                if value > 0:
                    parts.append("コンディションが味方")
                else:
                    parts.append("水面状況が不利")
            
            elif 'field' in feature or 'opponent' in feature:
                if value > 0:
                    parts.append("相手関係で有利")
                else:
                    parts.append("強敵揃いで苦戦か")
            
            elif 'recent' in feature:
                if value > 0:
                    parts.append("最近の成績が好調")
                else:
                    parts.append("近況がやや下降気味")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_parts = []
        for p in parts:
            if p not in seen:
                seen.add(p)
                unique_parts.append(p)
        
        if not unique_parts:
            return f"{exp.boat_no}号艇{exp.racer_name}は総合力で予測されています。"
        
        prob_text = "高確率" if exp.probability > 0.3 else "中程度の確率"
        
        return f"{exp.boat_no}号艇{exp.racer_name}は{prob_text}で予測。{'、'.join(unique_parts[:3])}が主な根拠。"
    
    async def explain_race_async(
        self,
        predictions: List[Dict],
        shap_values_per_boat: Dict[int, List[Tuple[str, float]]]
    ) -> Dict[int, str]:
        """Explain all predictions in a race"""
        explanations = {}
        
        for pred in predictions:
            boat_no = pred.get('boat_no', pred.get('waku'))
            exp = PredictionExplanation(
                boat_no=boat_no,
                racer_name=pred.get('racer_name', pred.get('name', '不明')),
                probability=pred.get('probability', pred.get('prob', 0)),
                shap_values=shap_values_per_boat.get(boat_no, [])
            )
            explanations[boat_no] = await self.explain_async(exp)
        
        return explanations


class RaceExplanationGenerator:
    """Generate comprehensive race explanation"""
    
    def __init__(self, explainer: Optional[LLMExplainer] = None):
        self.explainer = explainer or LLMExplainer()
    
    def generate_race_summary(
        self,
        predictions: List[Dict],
        race_info: Dict,
        shap_values_per_boat: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Generate a complete race summary with explanations"""
        result = {
            "race_info": race_info,
            "predictions": [],
            "summary": "",
            "confidence": ""
        }
        
        # Sort predictions by probability
        sorted_preds = sorted(
            predictions,
            key=lambda x: x.get('probability', x.get('prob', 0)),
            reverse=True
        )
        
        # Generate explanation for top 3
        for pred in sorted_preds[:3]:
            boat_no = pred.get('boat_no', pred.get('waku'))
            
            exp = PredictionExplanation(
                boat_no=boat_no,
                racer_name=pred.get('racer_name', pred.get('name', '不明')),
                probability=pred.get('probability', pred.get('prob', 0)),
                shap_values=shap_values_per_boat.get(boat_no, []) if shap_values_per_boat else []
            )
            
            explanation_text = self.explainer._generate_rule_based(exp)
            
            result["predictions"].append({
                "boat_no": boat_no,
                "racer_name": exp.racer_name,
                "probability": exp.probability,
                "explanation": explanation_text,
                "top_factors": [
                    {"feature": self.explainer._translate_feature(f), "impact": v}
                    for f, v in exp.shap_values[:3]
                ] if exp.shap_values else []
            })
        
        # Generate overall summary
        top = sorted_preds[0] if sorted_preds else {}
        top_prob = top.get('probability', top.get('prob', 0))
        top_boat = top.get('boat_no', top.get('waku', 1))
        
        # Confidence rating
        if top_prob > 0.4:
            result["confidence"] = "S"
            conf_text = "非常に堅い"
        elif top_prob > 0.3:
            result["confidence"] = "A"
            conf_text = "信頼度高め"
        elif top_prob > 0.2:
            result["confidence"] = "B"
            conf_text = "標準的"
        else:
            result["confidence"] = "C"
            conf_text = "混戦模様"
        
        # Wind/condition summary
        wind_speed = race_info.get('wind_speed', 0)
        wave_height = race_info.get('wave_height', 0)
        
        cond_text = ""
        if wind_speed >= 5 or wave_height >= 10:
            cond_text = "荒れた条件で波乱含み。"
        elif wind_speed >= 3:
            cond_text = "やや風があり展開に影響。"
        
        result["summary"] = f"【{conf_text}】{top_boat}号艇が本命。{cond_text}"
        
        return result


# Singleton instance
_explainer: Optional[LLMExplainer] = None


def get_llm_explainer() -> LLMExplainer:
    """Get or create LLM explainer"""
    global _explainer
    if _explainer is None:
        _explainer = LLMExplainer()
    return _explainer


if __name__ == "__main__":
    # Test
    exp = PredictionExplanation(
        boat_no=1,
        racer_name="田中太郎",
        probability=0.42,
        shap_values=[
            ("recent_win_rate", 0.15),
            ("motor_no2rate", 0.08),
            ("course_winrate", 0.06),
            ("field_strength", -0.03),
        ]
    )
    
    explainer = LLMExplainer()
    result = explainer._generate_rule_based(exp)
    print("Rule-based explanation:")
    print(result)
    
    # Test race summary
    generator = RaceExplanationGenerator()
    predictions = [
        {"boat_no": 1, "racer_name": "田中太郎", "probability": 0.42},
        {"boat_no": 3, "racer_name": "鈴木次郎", "probability": 0.25},
        {"boat_no": 4, "racer_name": "佐藤三郎", "probability": 0.15},
    ]
    race_info = {"stadium": "戸田", "race_no": 5, "wind_speed": 4}
    
    summary = generator.generate_race_summary(predictions, race_info)
    print("\nRace summary:")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
