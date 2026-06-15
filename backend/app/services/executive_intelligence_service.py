import logging

from app.services.executive_summary_service import generate_executive_summary_enhanced
from app.services.risk_analysis_service import analyze_risks
from app.services.opportunity_analysis_service import analyze_opportunities
from app.services.business_health_service import calculate_business_health
from app.services.recommendation_engine import generate_recommendations

logger = logging.getLogger(__name__)


async def generate_executive_intelligence(doc_ids: list[int]) -> dict:
    summary_result = await generate_executive_summary_enhanced(doc_ids)
    risks_result = await analyze_risks(doc_ids)
    opps_result = await analyze_opportunities(doc_ids)
    health_result = await calculate_business_health(doc_ids)

    recs = []
    try:
        primary = doc_ids[0]
        recs_raw = await generate_recommendations(primary)
        recs = [
            {
                "title": r.get("title", ""),
                "reasoning": r.get("description", ""),
                "expected_benefit": r.get("expected_outcome", ""),
                "priority": r.get("urgency", "medium"),
                "implementation_difficulty": "medium",
                "confidence": r.get("confidence", 0.5),
            }
            for r in recs_raw[:6]
        ]
    except Exception as e:
        logger.warning("Recommendations failed: %s", e)

    all_sources = list(set(
        summary_result.get("sources", []) +
        risks_result.get("sources", []) +
        opps_result.get("sources", [])
    ))

    def _to_01(val: float) -> float:
        return round(val / 100, 2) if val > 1 else round(val, 2)

    confidence_scores = {
        "summary": _to_01(summary_result.get("confidence", 0)),
        "risks": _to_01(risks_result.get("confidence", 0)),
        "opportunities": _to_01(opps_result.get("confidence", 0)),
        "business_health": _to_01(health_result.get("overall", 0) or 0),
        "recommendations": round(sum(r.get("confidence", 0) for r in recs) / len(recs), 2) if recs else 0,
    }

    overall_confidence = round(
        sum(v for v in confidence_scores.values() if isinstance(v, (int, float))) / 5, 2
    )

    return {
        "executive_summary": summary_result,
        "business_health": health_result,
        "risks": risks_result.get("risks", []),
        "opportunities": opps_result.get("opportunities", []),
        "recommendations": recs,
        "sources": all_sources,
        "confidence_scores": confidence_scores,
        "overall_confidence": overall_confidence,
    }
