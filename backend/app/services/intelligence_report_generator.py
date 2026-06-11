import logging

from app.services.report_engine import ReportPDF
from app.services.insights_service import generate_insights
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
    try:
        insights = await generate_insights(primary)
    except Exception:
        pass
    return {
        "executive_summary": {"summary": insights.get("executive_summary", ""), "key_findings": insights.get("key_findings", [])},
        "business_health": {"overall": 0, "level": "N/A"},
        "risks": [{"name": r, "severity": "Medium", "probability": "Medium", "mitigation": ""} for r in insights.get("risks", [])],
        "opportunities": [{"name": o, "expected_impact": "Medium", "priority": "Medium", "recommended_action": ""} for o in insights.get("opportunities", [])],
        "recommendations": [{"title": r, "priority": "Medium", "expected_benefit": ""} for r in insights.get("recommendations", [])],
        "sources": [f"Document #{did}" for did in doc_ids],
        "confidence_scores": {"overall": insights.get("confidence_score", 50) / 100},
        "overall_confidence": insights.get("confidence_score", 50) / 100,
    }


async def generate_intelligence_report(doc_ids: list[int]) -> bytes:
    if not doc_ids:
        return ReportPDF("No Data", "Intelligence Report").close()

    title = f"Intelligence Report ({len(doc_ids)} documents)"
    intelligence = await _get_intelligence(doc_ids)
    health = intelligence.get("business_health", {})
    risks = intelligence.get("risks", [])
    opps = intelligence.get("opportunities", [])
    recs = intelligence.get("recommendations", [])
    exec_summary = intelligence.get("executive_summary", {})
    sources = intelligence.get("sources", [])
    confidence = intelligence.get("overall_confidence", 0)

    all_insights = []
    for did in doc_ids:
        try:
            ins = await generate_insights(did)
            all_insights.append(ins)
        except Exception:
            pass

    pdf = ReportPDF(title, "Intelligence Report")
    pdf.alias_nb_pages()
    pdf.cover_page(subtitle=f"Analysis of {len(doc_ids)} document(s) | Multi-Source Intelligence")

    pdf.section("1", "Executive Summary")
    if exec_summary.get("summary"):
        pdf.body(exec_summary["summary"])
    if exec_summary.get("key_findings"):
        pdf.bullet(exec_summary["key_findings"])

    pdf.section("2", "Key Findings & Evidence Analysis")
    combined = []
    for ins in all_insights:
        combined.extend(ins.get("key_findings", []))
    if combined:
        pdf.bullet(combined[:10])
    else:
        pdf.body("No specific findings identified across documents.")

    pdf.section("3", "Comparative Analysis")
    if len(doc_ids) >= 2:
        pdf.body(f"Analysis across {len(doc_ids)} documents.")
        for ins in all_insights[:3]:
            s = ins.get("executive_summary", "")[:200]
            if s:
                pdf.body(f"  \u2022 {s}")
    else:
        pdf.body("Single-document analysis. Upload more documents for comparative insights.")

    pdf.section("4", "Strategic Implications")
    if risks:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(20, 30, 50)
        pdf.cell(0, 6, "Risk Summary", new_x="LMARGIN", new_y="NEXT")
        pdf.table_header(["Risk", "Severity", "Probability", "Mitigation"], [55, 20, 22, 88])
        for r in risks[:5]:
            pdf.risk_row(r.get("name", ""), r.get("severity", "Medium"), r.get("probability", "Medium"), r.get("mitigation", "")[:50])
    if opps:
        pdf.ln(2)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, "Opportunity Summary", new_x="LMARGIN", new_y="NEXT")
        pdf.table_header(["Opportunity", "Impact", "Priority", "Action"], [55, 22, 20, 88])
        for o in opps[:5]:
            pdf.opportunity_row(o.get("name", ""), o.get("expected_impact", "Medium"), o.get("priority", "Medium"), o.get("recommended_action", "")[:50])

    pdf.section("5", "Recommendations")
    if recs:
        pdf.table_header(["Recommendation", "Priority", "Benefit"], [70, 22, 93])
        for r in recs[:8]:
            pdf.rec_row(r.get("title", ""), r.get("priority", "Medium"), r.get("expected_benefit", "")[:50])
    else:
        pdf.body("No recommendations generated.")

    pdf.section("6", "Supporting Evidence")
    pdf.body(f"Sources analyzed: {len(sources)}")
    for s in sources:
        pdf.bullet([s])
    pdf.body(f"Overall Confidence: {int(confidence * 100) if isinstance(confidence, float) else confidence}%")

    return pdf.close()
