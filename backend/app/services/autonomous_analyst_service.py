import logging

from app.database.database import get_session_factory
from app.models.document import Document
from app.services.ai_service import generate_response
from app.services.analytics_service import get_analytics
from app.services.insights_service import generate_insights
from app.services.health_service import get_dataset_health
from app.services.forecasting_service import generate_forecast
from app.services.risk_scoring_service import calculate_risk_score
from app.services.recommendation_engine import generate_recommendations
from sqlalchemy import select

logger = logging.getLogger(__name__)


async def run_autonomous_analysis(doc_ids: list[int]) -> dict:
    logger.info("Running autonomous analysis for docs: %s", doc_ids)

    primary_doc_id = doc_ids[0] if doc_ids else 0
    if not primary_doc_id:
        return {"doc_id": 0, "business_health": {}, "top_risks": [], "top_opportunities": [], "forecasts": [], "strategic_recommendations": [], "overall_confidence": 0}

    business_health = {}
    top_risks = []
    top_opportunities = []
    forecasts_list = []
    recommendations = []
    confidence = 0.5

    try:
        health = await get_dataset_health(primary_doc_id)
        business_health = {
            "overall_score": health.get("overall", 0),
            "label": health.get("label", ""),
            "completeness": health.get("completeness", 0),
            "quality": health.get("quality", 0),
        }
        confidence += 0.1
    except Exception:
        pass

    risk = {}
    try:
        risk = await calculate_risk_score(primary_doc_id)
        confidence += 0.1
    except Exception:
        pass

    insights = {}
    try:
        insights = await generate_insights(primary_doc_id)
        confidence += 0.1
    except Exception:
        pass

    risks = []
    seen_risk_titles = set()
    for r_text in insights.get("risks", []):
        title = r_text[:50]
        if title not in seen_risk_titles:
            seen_risk_titles.add(title)
            risks.append({"title": r_text[:80], "severity": "high" if "supplier" in r_text.lower() or "declin" in r_text.lower() or "cost" in r_text.lower() else "medium", "impact": "significant", "probability": "likely", "mitigation": "Review and develop mitigation plan."})
    for cat in risk.get("categories", []):
        if cat.get("score", 0) >= 50:
            title = f"{cat['name']} at {cat['score']}/100"
            if title not in seen_risk_titles:
                seen_risk_titles.add(title)
                risks.append({"title": cat.get("explanation", title)[:80], "severity": "high" if cat["score"] >= 70 else "medium", "impact": "significant", "probability": "probable", "mitigation": "; ".join(cat.get("mitigations", ["Monitor closely."]))})
    top_risks = risks[:5]

    opps = []
    seen_opp_titles = set()
    for o_text in insights.get("opportunities", []):
        title = o_text[:50]
        if title not in seen_opp_titles:
            seen_opp_titles.add(title)
            opps.append({"title": o_text[:80], "estimated_impact": "significant", "strategic_value": "high", "recommended_action": o_text[:80]})
    top_opportunities = opps[:5]

    try:
        analytics = await get_analytics(primary_doc_id)
        if analytics:
            numeric_cols = [c for c in analytics.columns if c.dtype == "numeric"]
            for col in numeric_cols[:3]:
                fc = await generate_forecast(primary_doc_id, col.name, 30)
                if fc and fc.get("forecast"):
                    forecasts_list.append({
                        "metric": col.name,
                        "trend": fc["trend_direction"],
                        "confidence": fc["confidence_avg"],
                        "horizon": "30 days",
                    })
                fc90 = await generate_forecast(primary_doc_id, col.name, 90)
                if fc90 and fc90.get("forecast"):
                    forecasts_list.append({
                        "metric": col.name,
                        "trend": fc90["trend_direction"],
                        "confidence": fc90["confidence_avg"],
                        "horizon": "90 days",
                    })
                fy = await generate_forecast(primary_doc_id, col.name, 365)
                if fy and fy.get("forecast"):
                    forecasts_list.append({
                        "metric": col.name,
                        "trend": fy["trend_direction"],
                        "confidence": fy["confidence_avg"],
                        "horizon": "1 year",
                    })
        confidence += 0.1
    except Exception:
        pass

    try:
        recs = await generate_recommendations(primary_doc_id)
        recommendations = [{"title": r.get("title", ""), "impact": r.get("impact", "medium"), "urgency": r.get("urgency", "medium"), "confidence": r.get("confidence", 0.5), "expected_outcome": r.get("description", "")[:100]} for r in recs[:8]]
        confidence += 0.1
    except Exception:
        pass

    overall_confidence = round(min(confidence, 0.95), 2)

    return {
        "doc_id": primary_doc_id,
        "business_health": business_health,
        "top_risks": top_risks,
        "top_opportunities": top_opportunities,
        "forecasts": forecasts_list[:9],
        "strategic_recommendations": recommendations,
        "overall_confidence": overall_confidence,
    }
