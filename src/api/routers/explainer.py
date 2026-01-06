"""予測説明APIルーター

SHAP値とLLMを使った予測説明機能を提供。
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime

router = APIRouter(prefix="/api/explain", tags=["Explainer"])

# Import explainer modules
try:
    from src.inference.llm_explainer import (
        get_llm_explainer,
        RaceExplanationGenerator,
        PredictionExplanation,
    )
    HAS_LLM_EXPLAINER = True
except ImportError:
    HAS_LLM_EXPLAINER = False

try:
    from src.model.explainer import SHAPExplainer
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False


class ExplainRequest(BaseModel):
    """予測説明リクエスト"""
    predictions: List[Dict[str, Any]]
    race_info: Optional[Dict[str, Any]] = None
    include_shap: bool = False


class ExplainResponse(BaseModel):
    """予測説明レスポンス"""
    success: bool
    predictions: List[Dict[str, Any]]
    summary: str
    confidence: str
    generated_at: str


@router.get("/status")
async def get_status():
    """説明機能のステータスを取得"""
    return {
        "llm_explainer": HAS_LLM_EXPLAINER,
        "shap_explainer": HAS_SHAP,
        "status": "ready" if HAS_LLM_EXPLAINER else "limited"
    }


@router.post("/race", response_model=ExplainResponse)
async def explain_race(request: ExplainRequest):
    """レース予測の説明を生成"""
    if not HAS_LLM_EXPLAINER:
        raise HTTPException(status_code=503, detail="LLM Explainer not available")
    
    try:
        generator = RaceExplanationGenerator()
        
        race_info = request.race_info or {}
        
        # SHAP values (if available)
        shap_values_per_boat = None
        if request.include_shap and HAS_SHAP:
            # Note: In real implementation, would need feature data to compute SHAP
            pass
        
        result = generator.generate_race_summary(
            predictions=request.predictions,
            race_info=race_info,
            shap_values_per_boat=shap_values_per_boat
        )
        
        return ExplainResponse(
            success=True,
            predictions=result["predictions"],
            summary=result["summary"],
            confidence=result["confidence"],
            generated_at=datetime.now().isoformat()
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/single")
async def explain_single_prediction(
    boat_no: int,
    racer_name: str,
    probability: float,
    shap_values: Optional[List[Dict[str, float]]] = None
):
    """単一予測の説明を生成"""
    if not HAS_LLM_EXPLAINER:
        raise HTTPException(status_code=503, detail="LLM Explainer not available")
    
    try:
        explainer = get_llm_explainer()
        
        # Convert shap_values format
        shap_list = []
        if shap_values:
            for sv in shap_values:
                for k, v in sv.items():
                    shap_list.append((k, v))
        
        exp = PredictionExplanation(
            boat_no=boat_no,
            racer_name=racer_name,
            probability=probability,
            shap_values=shap_list
        )
        
        explanation = explainer._generate_rule_based(exp)
        
        return {
            "boat_no": boat_no,
            "racer_name": racer_name,
            "probability": probability,
            "explanation": explanation,
            "generated_at": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/features")
async def get_feature_translations():
    """特徴量の日本語訳一覧を取得"""
    if HAS_LLM_EXPLAINER:
        from src.inference.llm_explainer import FEATURE_TRANSLATIONS
        return {"translations": FEATURE_TRANSLATIONS}
    return {"translations": {}}
