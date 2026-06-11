import io
import logging
from datetime import datetime

import pandas as pd

from app.services.report_engine import ReportPDF
from app.services.analytics_service import get_analytics
from app.services.chart_service import generate_charts as _generate_charts, _correlation_heatmap
from app.services.forecasting_service import generate_forecast
from app.services.insights_service import generate_insights as _generate_insights
from app.services.health_service import get_dataset_health
from app.database.database import get_session_factory
from app.models.document import Document
from sqlalchemy import select

try:
    from app.services.executive_intelligence_service import generate_executive_intelligence
    HAS_INTELLIGENCE = True
except ImportError:
    HAS_INTELLIGENCE = False

logger = logging.getLogger(__name__)


async def _get_intelligence(doc_ids: list[int]) -> dict:
    if HAS_INTELLIGENCE:
        try:
            return await generate_executive_intelligence(doc_ids)
        except Exception as e:
            logger.warning("Intelligence service failed: %s", e)

    primary = doc_ids[0]
    insights = {}
    health = {}
    try:
        insights = await _generate_insights(primary)
    except Exception:
        pass
    try:
        health = await get_dataset_health(primary)
    except Exception:
        pass
    return {
        "executive_summary": {"summary": insights.get("executive_summary", ""), "key_findings": insights.get("key_findings", [])},
        "business_health": {"overall": health.get("overall", 0), "level": health.get("label", "N/A").lower(),
                            "financial_health": 0, "operational_health": 0, "growth_potential": 0,
                            "risk_exposure": 0, "data_quality": health.get("completeness", 0)},
        "risks": [{"name": r, "severity": "Medium", "probability": "Medium", "mitigation": ""} for r in insights.get("risks", [])],
        "opportunities": [{"name": o, "expected_impact": "Medium", "priority": "Medium", "recommended_action": ""} for o in insights.get("opportunities", [])],
        "recommendations": [{"title": r, "priority": "Medium", "expected_benefit": ""} for r in insights.get("recommendations", [])],
        "sources": [f"Document #{did}" for did in doc_ids],
        "confidence_scores": {"overall": insights.get("confidence_score", 50) / 100},
        "overall_confidence": insights.get("confidence_score", 50) / 100,
    }


async def generate_board_report(doc_ids: list[int], company_name: str = "") -> bytes:
    if not doc_ids:
        return ReportPDF("No Data", "Board Report").close()

    primary = doc_ids[0]
    doc_title = company_name or f"Document #{primary}"
    try:
        async with get_session_factory()() as db:
            result = await db.execute(select(Document).where(Document.id == primary))
            doc = result.scalar_one_or_none()
            if doc and not company_name:
                doc_title = doc.title or f"Document #{primary}"
    except Exception:
        pass

    intelligence = await _get_intelligence(doc_ids)
    health = intelligence.get("business_health", {})
    risks = intelligence.get("risks", [])
    opps = intelligence.get("opportunities", [])
    recs = intelligence.get("recommendations", [])
    exec_summary = intelligence.get("executive_summary", {})
    sources = intelligence.get("sources", [])
    confidence = intelligence.get("overall_confidence", 0)

    analytics = charts = forecast = None
    try:
        analytics = await get_analytics(primary)
        if analytics and analytics.columns:
            first_col = analytics.columns[0].name
            charts = await _generate_charts(primary, first_col) or {}
            numeric = [c for c in analytics.columns if c.dtype == "numeric"]
            if numeric:
                forecast = await generate_forecast(primary, numeric[0].name, 12)
    except Exception:
        pass

    pdf = ReportPDF(doc_title, "Board Report")
    pdf.alias_nb_pages()
    pdf.cover_page(subtitle="Comprehensive Board Intelligence Report", note="Confidential - For Board Members Only")

    pdf.section("", "Table of Contents")
    toc = ["1  Executive Summary", "2  Organization Health Assessment", "3  KPI Performance Dashboard",
           "4  Risk Analysis", "5  Opportunity Analysis", "6  Forecasting",
           "7  Strategic Recommendations", "8  Scenario Analysis", "9  Supporting Analytics", "10  Appendices"]
    for item in toc:
        pdf.body(f"  {item}")

    pdf.section("1", "Executive Summary")
    if exec_summary.get("summary"):
        pdf.body(exec_summary["summary"])
    if exec_summary.get("key_findings"):
        pdf.bullet(exec_summary["key_findings"])
    pdf.body(f"Intelligence Confidence: {int(confidence * 100) if isinstance(confidence, float) else confidence}%")

    pdf.section("2", "Organization Health Assessment")
    if health:
        pdf.body(f"Score: {health.get('overall', 'N/A')}/100  Level: {health.get('level', 'N/A')}")
        y = pdf.get_y() + 4
        metrics = [("Financial Health", health.get("financial_health", 0)), ("Operational Health", health.get("operational_health", 0)),
                   ("Growth Potential", health.get("growth_potential", 0)), ("Risk Exposure", health.get("risk_exposure", 0)),
                   ("Data Quality", health.get("data_quality", 0))]
        for i, (lbl, val) in enumerate(metrics):
            pdf.metric_card(lbl, f"{val}/100", 15 + i * 48, y)

    pdf.section("3", "KPI Performance Dashboard")
    if analytics:
        pdf.kv_row("Total Records", str(analytics.row_count))
        pdf.kv_row("Total Fields", str(analytics.column_count))
        for col in analytics.columns[:10]:
            extra = ""
            if col.numeric:
                extra = f"mean={col.numeric.get('mean','')} range=[{col.numeric.get('min','')}, {col.numeric.get('max','')}]"
            pdf.body(f"  {col.name} ({col.dtype}) missing={col.missing}/{col.total} {extra}")

    pdf.section("4", "Risk Analysis")
    if risks:
        pdf.table_header(["Risk", "Severity", "Prob.", "Impact / Mitigation"], [50, 18, 20, 97])
        for r in risks[:8]:
            pdf.risk_row(r.get("name", ""), r.get("severity", "Medium"), r.get("probability", "Medium"),
                         r.get("mitigation", r.get("potential_impact", ""))[:55])
    else:
        pdf.body("No significant risks identified.")

    pdf.section("5", "Opportunity Analysis")
    if opps:
        pdf.table_header(["Opportunity", "Impact", "Priority", "Action"], [50, 20, 18, 97])
        for o in opps[:8]:
            pdf.opportunity_row(o.get("name", ""), o.get("expected_impact", "Medium"), o.get("priority", "Medium"),
                                o.get("recommended_action", "")[:55])
    else:
        pdf.body("No opportunities identified.")

    pdf.section("6", "Forecasting")
    if forecast:
        pdf.body(f"Trend: {forecast['trend_direction'].upper()}  Strength: {forecast['trend_strength']*100:.0f}%")
        pdf.body(f"Confidence: {forecast['confidence_avg']*100:.0f}%")
        pdf.body(forecast.get("explanation", ""))
    else:
        pdf.body("Forecast data unavailable.")

    pdf.section("7", "Strategic Recommendations")
    if recs:
        pdf.table_header(["Recommendation", "Priority", "Benefit"], [70, 22, 93])
        for r in recs[:10]:
            pdf.rec_row(r.get("title", ""), r.get("priority", "Medium"), r.get("expected_benefit", "")[:55])
    else:
        pdf.body("No recommendations generated.")

    pdf.section("8", "Scenario Analysis")
    pdf.body("Based on current data trends and identified risks, three scenarios emerge:")
    pdf.body("  Optimistic: Continuation of positive trends with proactive risk management.")
    pdf.body("  Base Case: Moderate growth with controlled risk exposure.")
    pdf.body("  Pessimistic: Risk events materialize without mitigation actions.")

    pdf.section("9", "Supporting Analytics")
    if charts:
        for ct in ("bar", "pie", "line"):
            if charts.get(ct):
                pdf.add_chart(charts[ct])

    pdf.section("10", "Appendices")
    pdf.body(f"Report ID: {pdf._report_id}")
    pdf.body(f"Documents Analyzed: {len(doc_ids)}")
    for s in sources:
        pdf.bullet([s])
    pdf.body("Generated by AURA Enterprise Intelligence Platform.")
    pdf.body("Confidence scores are AI-generated estimates. Review by domain experts recommended.")

    return pdf.close()
