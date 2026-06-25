import logging

from app.services.report_engine import ReportPDF
from app.services.predictive_phase2_service import run_phase2_predictive
from app.database.database import get_session_factory
from app.models.document import Document
from sqlalchemy import select

logger = logging.getLogger(__name__)


async def generate_executive_briefing_pdf(doc_ids: list[int], org_name: str = "",
                                          org_logo_url: str = "", org_color: str = "",
                                          workspace: str = "") -> bytes:
    if not doc_ids:
        return ReportPDF("No Data", "Executive Briefing", org_name).close()

    primary = doc_ids[0]
    doc_title = org_name or f"Document #{primary}"
    try:
        async with get_session_factory()() as db:
            r = await db.execute(select(Document).where(Document.id == primary))
            doc = r.scalar_one_or_none()
            if doc and not org_name:
                doc_title = doc.title or f"Document #{primary}"
    except Exception:
        pass

    result = {}
    try:
        result = await run_phase2_predictive(primary)
    except Exception as e:
        logger.warning("Phase2 predictive failed: %s", e)

    bi = result.get("business_impact", {})
    risks = result.get("risks", [])
    opps = result.get("opportunities", [])
    presc = result.get("prescriptive_recommendations", [])
    pred_expl = result.get("prediction_explanation", {})
    exec_summary = result.get("executive_summary", "") or pred_expl.get("summary", "")
    root_causes = result.get("root_causes", [])
    industry = result.get("industry_intelligence", {})
    scenarios = result.get("scenarios", {})

    health_score = bi.get("confidence", 50)
    confidence = pred_expl.get("confidence", health_score)

    try:
        color_hex = org_color.lstrip("#")
        accent = tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))
    except Exception:
        accent = (37, 99, 235)

    pdf = ReportPDF(doc_title, "Executive Briefing", org_name, org_logo_url, accent)
    pdf.alias_nb_pages()
    pdf.cover_page(subtitle="Executive Briefing", workspace=workspace)

    health_color = (16, 185, 129) if health_score >= 70 else (245, 158, 11) if health_score >= 40 else (220, 38, 38)

    # ── Executive Summary (1 page max) ──
    if exec_summary:
        pdf.section_header("Executive Summary")
        pdf.body(exec_summary)
        pdf.space()

    # ── Business Health Dashboard ──
    pdf.section_header("Business Health Dashboard")
    metrics = [
        ("Health Score", f"{health_score:.0f}/100", health_color),
        ("Confidence", f"{confidence:.0f}%", accent),
        ("At Risk", str(bi.get("population_at_risk", "—")), (220, 38, 38)),
        ("Revenue at Risk", bi.get("revenue_at_risk_formatted", "—"), (185, 28, 28)),
    ]
    for i, (lbl, val, clr) in enumerate(metrics):
        pdf.metric_card_colored(lbl, val, 15 + i * 48, pdf.get_y(), clr, w=45)
    pdf.ln(24)

    if root_causes:
        pdf.body_bold("Key Drivers")
        pdf.bullet(root_causes[:4])
    pdf.space()

    # ── Risks & Opportunities ──
    if risks or opps:
        pdf.section_header("Risks & Opportunities")
        col_w = pdf.w / 2 - 15
        y_before = pdf.get_y()

        if risks:
            pdf.set_xy(10, y_before)
            pdf.body_bold("Top Risks")
            for r_text in risks[:4]:
                name = r_text.get("name", str(r_text)[:80]) if isinstance(r_text, dict) else str(r_text)[:80]
                pdf.set_x(10)
                pdf.set_font("Helvetica", "", 8)
                pdf.set_text_color(220, 38, 38)
                pdf.cell(4, 4, "-")
                pdf.set_text_color(* (60, 60, 60))
                pdf.multi_cell(col_w - 4, 4, str(r_text)[:80])

        if opps:
            pdf.set_xy(pdf.w / 2 + 5, y_before)
            pdf.body_bold("Top Opportunities")
            for o_text in opps[:4]:
                title = o_text.get("title", str(o_text)[:80]) if isinstance(o_text, dict) else str(o_text)[:80]
                pdf.set_x(pdf.w / 2 + 5)
                pdf.set_font("Helvetica", "", 8)
                pdf.set_text_color(16, 185, 129)
                pdf.cell(4, 4, "-")
                pdf.set_text_color(* (60, 60, 60))
                pdf.multi_cell(col_w - 4, 4, str(title)[:80])

        pdf.set_y(y_before + 45)
        pdf.space()

    # ── Scenario Analysis ──
    if scenarios.get("expected_case") is not None:
        pdf.section_header("Financial Impact Scenarios")
        pdf.kv_row("Best Case", f"${scenarios.get('best_case', 0):,.0f}")
        pdf.kv_row("Expected", f"${scenarios.get('expected_case', 0):,.0f}")
        pdf.kv_row("Worst Case", f"${scenarios.get('worst_case', 0):,.0f}")
        pdf.space()

    # ── Recommended Actions ──
    if presc:
        pdf.section_header("Recommended Actions")
        for i, rec in enumerate(presc[:4]):
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(20, 30, 50)
            pdf.cell(5)
            pdf.cell(0, 5, f"{i+1}. {rec.get('recommendation', '')[:80]}", new_x="LMARGIN", new_y="NEXT")
            pdf.set_x(15)
            pdf.set_font("Helvetica", "", 7)
            pdf.set_text_color(* (120, 120, 120))
            pdf.cell(0, 4, f"Impact: {rec.get('expected_impact', '')} | Savings: {rec.get('revenue_preserved', '')} | ROI: {rec.get('roi', '')}", new_x="LMARGIN", new_y="NEXT")
        pdf.space()

    if industry.get("industry_kpis"):
        pdf.body_bold(f"Industry: {industry.get('detected_industry', 'General Business')}")
        pdf.bullet(industry["industry_kpis"][:5])

    pdf.close()
    return pdf
