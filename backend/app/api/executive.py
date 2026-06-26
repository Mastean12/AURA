from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.schemas import (
    AutonomousAnalysisRequest,
    ExecutiveIntelligenceResponse,
    RiskItem,
    OpportunityItem,
    RecommendationAction,
)
from app.services.executive_intelligence_service import generate_executive_intelligence
from app.services.executive_intelligence_engine_v3 import run_executive_intelligence

router = APIRouter(tags=["executive"])


class DocRequest(BaseModel):
    doc_id: int


@router.post("/analytics/executive-intelligence", response_model=ExecutiveIntelligenceResponse)
async def executive_intelligence(payload: AutonomousAnalysisRequest):
    result = await generate_executive_intelligence(payload.doc_ids)
    return ExecutiveIntelligenceResponse(
        executive_summary=result.get("executive_summary", {}),
        business_health=result.get("business_health", {}),
        risks=[RiskItem(**r) for r in result.get("risks", [])],
        opportunities=[OpportunityItem(**o) for o in result.get("opportunities", [])],
        recommendations=[RecommendationAction(**r) for r in result.get("recommendations", [])],
        sources=result.get("sources", []),
        confidence_scores=result.get("confidence_scores", {}),
        overall_confidence=result.get("overall_confidence", 0),
    )


@router.post("/analytics/executive-intelligence-v3")
async def executive_intelligence_v3(payload: DocRequest):
    """Run the v3 Executive Intelligence Engine with narrative, root cause, business rules."""
    import numpy as np
    result = await run_executive_intelligence(payload.doc_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    def _convert(obj):
        if isinstance(obj, dict): return {k: _convert(v) for k, v in obj.items()}
        elif isinstance(obj, list): return [_convert(v) for v in obj]
        elif isinstance(obj, np.integer): return int(obj)
        elif isinstance(obj, np.floating): return float(obj)
        elif isinstance(obj, np.bool_): return bool(obj)
        elif isinstance(obj, np.ndarray): return obj.tolist()
        return obj
    return _convert(result)
