from fastapi import APIRouter

from app.models.schemas import (
    AutonomousAnalysisRequest,
    ExecutiveIntelligenceResponse,
    RiskItem,
    OpportunityItem,
    RecommendationAction,
)
from app.services.executive_intelligence_service import generate_executive_intelligence

router = APIRouter(tags=["executive"])


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
