import logging

from app.database.database import get_session_factory
from app.models.document import Document
from app.services.ai_service import generate_response
from app.services.insights_service import generate_insights
from app.services.health_service import get_dataset_health
from app.services.risk_scoring_service import calculate_risk_score
from app.services.forecasting_service import generate_forecast
from app.services.analytics_service import get_analytics
from sqlalchemy import select

logger = logging.getLogger(__name__)


async def generate_executive_briefing(doc_id: int, company_name: str = "") -> dict:
    logger.info("Generating executive briefing for doc_id=%d", doc_id)
    try:
        async with get_session_factory()() as db:
            result = await db.execute(select(Document).where(Document.id == doc_id))
            doc = result.scalar_one_or_none()
    except Exception:
        doc = None

    if not doc:
        return {"summary": "Document not found.", "business_health": "", "critical_risks": [], "growth_opportunities": [], "forecast_outlook": "", "recommended_actions": [], "confidence": 0}

    insights = {}
    health = {}
    risk = {}
    forecast_text = ""
    has_numeric = False

    try:
        insights = await generate_insights(doc_id)
    except Exception:
        pass
    try:
        health = await get_dataset_health(doc_id)
    except Exception:
        pass
    try:
        risk = await calculate_risk_score(doc_id)
    except Exception:
        pass
    try:
        analytics = await get_analytics(doc_id)
        if analytics:
            numeric_cols = [c for c in analytics.columns if c.dtype == "numeric"]
            if numeric_cols:
                has_numeric = True
                fc = await generate_forecast(doc_id, numeric_cols[0].name, 90)
                if fc and fc.get("forecast"):
                    forecast_text = f"Forecast for {numeric_cols[0].name}: {fc['trend_direction']} trend with {fc['confidence_avg']*100:.0f}% confidence."
    except Exception:
        pass

    exec_summary = insights.get("executive_summary", "Analysis complete. See detailed findings below.")
    health_score = health.get("overall", 0)
    health_label = health.get("label", "Unknown")
    business_health_text = f"Overall business health score: {health_score}/100 ({health_label})."

    risks = insights.get("risks", [])
    opps = insights.get("opportunities", [])
    recs = insights.get("recommendations", [])

    if not risks:
        for cat in risk.get("categories", []):
            if cat.get("score", 0) >= 40:
                risks.append(f"{cat['name']} score: {cat['score']}/100 - {cat.get('explanation', '')[:80]}")

    outlook = forecast_text if forecast_text else "Insufficient data for forecasting."
    if not exec_summary:
        exec_summary = f"Organization health is at {health_score}/100. Key areas require attention."

    confidence = round((0.5 + (0.1 if insights else 0) + (0.1 if health else 0) + (0.1 if risk else 0) + (0.1 if has_numeric else 0)), 2)

    return {
        "summary": exec_summary,
        "business_health": business_health_text,
        "critical_risks": risks[:5],
        "growth_opportunities": opps[:5],
        "forecast_outlook": outlook,
        "recommended_actions": recs[:5],
        "confidence": min(confidence, 0.95),
    }
