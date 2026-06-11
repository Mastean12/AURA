import logging

from app.services.report_engine import ReportPDF
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
        "risks": [{"name": r, "severity": "Medium", "probability": "Medium", "potential_impact": "", "mitigation": ""} for r in insights.get("risks", [])],
        "opportunities": [{"name": o, "expected_impact": "Medium", "priority": "Medium", "recommended_action": ""} for o in insights.get("opportunities", [])],
        "recommendations": [{"title": r, "priority": "Medium", "expected_benefit": ""} for r in insights.get("recommendations", [])],
        "sources": [f"Document #{did}" for did in doc_ids],
        "confidence_scores": {"overall": insights.get("confidence_score", 50) / 100},
        "overall_confidence": insights.get("confidence_score", 50) / 100,
    }


async def generate_executive_briefing_pdf(doc_ids: list[int], company_name: str = "") -> bytes:
    if not doc_ids:
        return ReportPDF("No Data", "Executive Briefing").close()

    doc_title = company_name
    try:
        async with get_session_factory()() as db:
            result = await db.execute(select(Document).where(Document.id == doc_ids[0]))
            doc = result.scalar_one_or_none()
            if doc and not company_name:
                doc_title = doc.title or f"Document #{doc_ids[0]}"
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

    pdf = ReportPDF(doc_title or "Executive Briefing", "Executive Briefing")
    pdf.alias_nb_pages()
    pdf.cover_page(subtitle=f"Prepared for {company_name}" if company_name else "AI-Powered Executive Briefing")

    pdf.section("1", "Executive Summary")
    if exec_summary.get("summary"):
        pdf.body(exec_summary["summary"])
    if exec_summary.get("business_impact"):
        pdf.body(f"Business Impact: {exec_summary['business_impact']}")
    if exec_summary.get("strategic_implications"):
        pdf.body(f"Strategic Implications: {exec_summary['strategic_implications']}")
    if exec_summary.get("key_findings"):
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(20, 30, 50)
        pdf.cell(0, 6, "Key Findings", new_x="LMARGIN", new_y="NEXT")
        pdf.bullet(exec_summary["key_findings"])

    pdf.section("2", "Business Health Score")
    if health:
        pdf.body(f"Overall Score: {health.get('overall', 'N/A')}/100  Level: {health.get('level', 'N/A')}")
        y = pdf.get_y() + 4
        metrics = [("Financial Health", health.get("financial_health", 0)), ("Operational Health", health.get("operational_health", 0)),
                   ("Growth Potential", health.get("growth_potential", 0)), ("Risk Exposure", health.get("risk_exposure", 0)),
                   ("Data Quality", health.get("data_quality", 0))]
        for i, (lbl, val) in enumerate(metrics):
            pdf.metric_card(lbl, f"{val}/100", 15 + i * 48, y)

    pdf.section("3", "Top Risks")
    if risks:
        pdf.table_header(["Risk", "Severity", "Prob.", "Impact / Mitigation"], [55, 20, 20, 90])
        for r in risks[:6]:
            pdf.risk_row(r.get("name", ""), r.get("severity", "Medium"), r.get("probability", "Medium"),
                         r.get("potential_impact", "")[:50])
    else:
        pdf.body("No significant risks identified.")

    pdf.section("4", "Top Opportunities")
    if opps:
        pdf.table_header(["Opportunity", "Impact", "Priority", "Action"], [55, 22, 20, 88])
        for o in opps[:6]:
            pdf.opportunity_row(o.get("name", ""), o.get("expected_impact", "Medium"), o.get("priority", "Medium"),
                                o.get("recommended_action", "")[:50])
    else:
        pdf.body("No opportunities identified.")

    pdf.section("5", "Recommended Actions")
    if recs:
        pdf.table_header(["Recommendation", "Priority", "Benefit"], [70, 22, 93])
        for r in recs[:6]:
            pdf.rec_row(r.get("title", ""), r.get("priority", "Medium"), r.get("expected_benefit", "")[:50])
    else:
        pdf.body("No recommendations available.")

    pdf.section("6", "Conclusion")
    pdf.body(f"Overall Confidence: {int(confidence * 100) if isinstance(confidence, float) else confidence}%")
    pdf.body(f"Generated from {len(sources)} source document(s).")
    for s in sources:
        pdf.bullet([s])
    pdf.body("Confidence scores are AI-generated estimates. Review by domain experts recommended.")

    return pdf.close()
