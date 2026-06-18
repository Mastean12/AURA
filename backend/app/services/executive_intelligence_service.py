import io
import logging

import pandas as pd

from app.database.database import get_session_factory
from app.models.document import Document
from app.services.executive_summary_service import generate_executive_summary_enhanced
from app.services.risk_analysis_service import analyze_risks
from app.services.opportunity_analysis_service import analyze_opportunities
from app.services.business_health_service import calculate_business_health
from app.services.recommendation_engine import generate_recommendations
from app.services.executive_intelligence_v2 import generate_enhanced_executive_intelligence
from app.services.analytics_pipeline import run_full_analytics_pipeline
from sqlalchemy import select

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

    result = {
        "executive_summary": summary_result,
        "business_health": health_result,
        "risks": risks_result.get("risks", []),
        "opportunities": opps_result.get("opportunities", []),
        "recommendations": recs,
        "sources": all_sources,
        "confidence_scores": confidence_scores,
        "overall_confidence": overall_confidence,
    }

    # Enhance with v2 pipeline if single doc has tabular data
    if len(doc_ids) == 1:
        try:
            async with get_session_factory()() as db:
                r = await db.execute(select(Document).where(Document.id == doc_ids[0]))
                doc = r.scalar_one_or_none()
            if doc and doc.content and doc.content.count(",") > 5:
                df = pd.read_csv(io.StringIO(doc.content))
                if len(df.columns) >= 2:
                    v2_result = await run_full_analytics_pipeline(doc_ids[0], df)
                    ei = v2_result.get("executive_intelligence", {})
                    if ei.get("findings"):
                        result["v2_findings"] = ei.get("findings", [])
                    if ei.get("business_health"):
                        result["v2_health"] = ei.get("business_health", {})
                    result["data_quality"] = v2_result.get("data_quality", {})
                    result["dataset_intelligence"] = v2_result.get("dataset_intelligence", {})
        except Exception as e:
            logger.warning("V2 pipeline enhancement failed: %s", e)

    return result
