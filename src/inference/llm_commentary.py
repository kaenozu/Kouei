"""LLM-Enhanced Commentary Generation"""
import json
from typing import Dict, List, Optional, Any
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


@dataclass
class RaceContext:
    """Context for race commentary generation"""
    stadium_name: str
    race_no: int
    date: str
    weather: str
    wind_speed: float
    wind_direction: str
    wave_height: float
    predictions: List[Dict]
    top_factors: List[str]
    confidence: str
    similar_races: Optional[List[Dict]] = None


class LLMCommentaryGenerator:
    """Generate AI commentary using LLM APIs"""
    
    SYSTEM_PROMPT = """あなたは競艇のエキスパートアナリストです。
レースデータと予測結果に基づいて、的確で分かりやすい解説を日本語で提供してください。

重要な観点:
- 1号艇のイン逃げ成功率（競艇では1号艇有利が基本）
- モーター性能と選手の技量の組み合わせ
- 風速・波高が与える影響（強風時は荒れやすい）
- 展示タイムの示す調子
- 過去の類似レースパターン

回答は簡潔に、100-200文字程度でまとめてください。
"""
    
    def __init__(self):
        self.provider = settings.llm_provider.lower()
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """Initialize LLM client based on settings"""
        if self.provider == "openai" and OPENAI_AVAILABLE and settings.openai_api_key:
            self.client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
            logger.info("LLM: OpenAI client initialized")
        elif self.provider == "anthropic" and ANTHROPIC_AVAILABLE and settings.anthropic_api_key:
            self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
            logger.info("LLM: Anthropic client initialized")
        else:
            logger.info("LLM: No provider configured, using rule-based fallback")
    
    def _build_prompt(self, context: RaceContext) -> str:
        """Build prompt from race context"""
        top_3 = context.predictions[:3]
        
        prompt = f"""以下のレースについて解説してください。

【レース情報】
- 会場: {context.stadium_name} {context.race_no}R
- 日付: {context.date}
- 天候: {context.weather}
- 風速: {context.wind_speed}m
- 風向: {context.wind_direction}
- 波高: {context.wave_height}cm

【AI予測トップ3】
"""
        for i, pred in enumerate(top_3, 1):
            prompt += f"{i}. {pred.get('boat_no')}号艇 {pred.get('racer_name', '不明')} - 勝率予測: {pred.get('probability', 0)*100:.1f}%\n"
        
        prompt += f"\n【注目ポイント】\n"
        for factor in context.top_factors:
            prompt += f"- {factor}\n"
        
        prompt += f"\n信頼度: {context.confidence}ランク"
        
        if context.similar_races:
            prompt += f"\n\n【類似過去レース】\n"
            for race in context.similar_races[:2]:
                prompt += f"- {race.get('date')} {race.get('stadium')} {race.get('result', '')}\n"
        
        return prompt
    
    async def generate_async(self, context: RaceContext) -> str:
        """Generate commentary asynchronously"""
        if self.client is None:
            return self._generate_rule_based(context)
        
        prompt = self._build_prompt(context)
        
        try:
            if self.provider == "openai":
                response = await self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": self.SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=300,
                    temperature=0.7
                )
                return response.choices[0].message.content
            
            elif self.provider == "anthropic":
                response = await self.client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=300,
                    system=self.SYSTEM_PROMPT,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
        
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return self._generate_rule_based(context)
    
    def generate(self, context: RaceContext) -> str:
        """Synchronous wrapper for generate_async"""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If called from async context, create task
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    return pool.submit(
                        asyncio.run, self.generate_async(context)
                    ).result()
            else:
                return asyncio.run(self.generate_async(context))
        except Exception as e:
            logger.error(f"Generate failed: {e}")
            return self._generate_rule_based(context)
    
    def _generate_rule_based(self, context: RaceContext) -> str:
        """Rule-based fallback commentary"""
        top_boat = context.predictions[0] if context.predictions else {}
        boat_no = top_boat.get('boat_no', 1)
        prob = top_boat.get('probability', 0) * 100
        
        # Wind analysis
        wind_comment = ""
        if context.wind_speed >= 5:
            wind_comment = "強風のため荒れる展開が予想されます。"
        elif context.wind_speed >= 3:
            wind_comment = "やや風が強く、ターン時に差が出やすい条件です。"
        
        # Confidence analysis
        conf_comment = ""
        if context.confidence == "S":
            conf_comment = "データ的に非常に堅い一戦。"
        elif context.confidence == "A":
            conf_comment = "信頼度の高い予測です。"
        elif context.confidence == "C":
            conf_comment = "波乱含みの展開も。"
        
        # Build comment
        comment = f"{boat_no}号艇が{prob:.0f}%の高確率でトップ予測。{wind_comment}{conf_comment}"
        
        # Add factors
        if context.top_factors:
            comment += f"注目点は「{context.top_factors[0]}」。"
        
        return comment


class RAGCommentaryGenerator(LLMCommentaryGenerator):
    """RAG-enhanced commentary with historical context"""
    
    def __init__(self, vector_db=None):
        super().__init__()
        self.vector_db = vector_db
    
    async def generate_with_rag(self, context: RaceContext, query_conditions: Dict) -> str:
        """Generate commentary with RAG retrieval"""
        # Retrieve similar historical races
        if self.vector_db:
            try:
                similar = self.vector_db.search(query_conditions, top_k=3)
                context.similar_races = similar
            except Exception as e:
                logger.warning(f"RAG retrieval failed: {e}")
        
        return await self.generate_async(context)


# Singleton instance
_generator: Optional[LLMCommentaryGenerator] = None


def get_commentary_generator() -> LLMCommentaryGenerator:
    """Get or create commentary generator"""
    global _generator
    if _generator is None:
        _generator = LLMCommentaryGenerator()
    return _generator


if __name__ == "__main__":
    # Test
    gen = get_commentary_generator()
    
    test_context = RaceContext(
        stadium_name="戸田",
        race_no=5,
        date="2024-01-15",
        weather="晴",
        wind_speed=4.5,
        wind_direction="北",
        wave_height=3,
        predictions=[
            {"boat_no": 1, "racer_name": "田中太郎", "probability": 0.45},
            {"boat_no": 3, "racer_name": "鈴木次郎", "probability": 0.25},
            {"boat_no": 4, "racer_name": "佐藤三郎", "probability": 0.15},
        ],
        top_factors=["モーター性能の高さ", "展示タイム好調"],
        confidence="A"
    )
    
    result = gen.generate(test_context)
    print(result)
