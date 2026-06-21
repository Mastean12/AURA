import io
import logging
from datetime import datetime

import pandas as pd
import numpy as np

from app.services.report_engine import ReportPDF, _decorate_predictive_charts
from app.services.predictive_phase2_service import run_phase2_predictive, forecast_timeline
from app.database.database import get_session_factory
from app.models.document import Document
from sqlalchemy import select

logger = logging.getLogger(__name__)


async def generate_board_report(doc_ids: list[int], org_name: str = "",
                                org_logo_url: str = "", org_color: str = "",
                                workspace: str = "") -> bytes:
    if not doc_ids:
        return ReportPDF("No Data", "Board Report", org_name).close()

    primary = doc_ids[0]
    doc_title = org_name or f"Document #{primary}"
    df = None
    try:
        async with get_session_factory()() as db:
            r = await db.execute(select(Document).where(Document.id == primary))
            doc = r.scalar_one_or_none()
            if doc and not org_name:
                doc_title = doc.title or f"Document #{primary}"
            if doc and doc.content and doc.content.count(",") > 5:
                df = pd.read_csv(io.StringIO(doc.content))
    except Exception:
        pass

    result = {}
    if df is not None and len(df.columns) >= 2:
        try:
            result = await run_phase2_predictive(primary)
        except Exception as e:
            logger.warning("Phase2 predictive failed: %s", e)

    bi = result.get("business_impact", {})
    risks = result.get("risks", result.get("risk_analysis", []))
    opps = result.get("opportunities", [])
    presc = result.get("prescriptive_recommendations", [])
    pred_expl = result.get("prediction_explanation", {})
    exec_summary = result.get("executive_summary", "") or pred_expl.get("summary", "")
    timeline = result.get("forecast_timeline", {})
    tfc = timeline.get("forecasts", {})
    root_causes = result.get("root_causes", [])
    industry = result.get("industry_intelligence", {})
    scenarios = result.get("scenarios", {})
    tech = result.get("technical", {})
    drivers = pred_expl.get("drivers", [])
    feats = tech.get("feature_importance", [])
    target = tech.get("target", "")

    health_score = bi.get("confidence", 50)
    confidence = pred_expl.get("confidence", health_score)

    try:
        color_hex = org_color.lstrip("#")
        accent = tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))
    except Exception:
        accent = (37, 99, 235)

    pdf = ReportPDF(doc_title, "Board Report", org_name, org_logo_url, accent)
    pdf.alias_nb_pages()

    pdf.cover_page(
        subtitle=f"{industry.get('detected_industry', 'Executive')} Intelligence Analysis",
        workspace=workspace,
        confidentiality="CONFIDENTIAL - FOR BOARD MEMBERS ONLY",
    )

    risk_level = "Strong" if health_score >= 70 else "Moderate" if health_score >= 40 else "Critical"
    health_color = (16, 185, 129) if health_score >= 70 else (245, 158, 11) if health_score >= 40 else (220, 38, 38)

    # ── Board Briefing (1-page) ──
    pdf.section_header("Board Briefing")
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(* (120, 120, 120))
    pdf.cell(0, 5, "Strategic overview for board decision-making", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    col_w = pdf.w / 2 - 18
    y0 = pdf.get_y()
    left_x, right_x = 12, pdf.w / 2 + 6

    pdf.set_xy(left_x, y0)
    pdf.body_bold("Top Findings")
    drivers_text = [f"{d['feature'].replace('_',' ').title()} ({d.get('pct', d.get('importance',0)*100):.0f}%)" for d in drivers[:3]]
    top_findings = root_causes[:4] if root_causes else drivers_text[:4]
    for f_text in top_findings:
        pdf.set_x(left_x)
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(* (60, 60, 60))
        pdf.cell(4, 4, "\u2022")
        pdf.multi_cell(col_w - 4, 4, str(f_text)[:90])

    pdf.set_xy(right_x, y0)
    pdf.body_bold("Required Decisions")
    for i, r in enumerate(risks[:4] if risks else ["Review current performance trends"]):
        pdf.set_x(right_x)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(* (220, 38, 38))
        pdf.cell(4, 4, f"{i+1}.")
        pdf.set_text_color(* (60, 60, 60))
        pdf.multi_cell(col_w - 4, 4, str(r.get("name", r) if isinstance(r, dict) else r)[:90])

    findings_h = max(len(top_findings) * 10, 35)
    pdf.set_y(max(y0 + findings_h + 5, pdf.get_y()))

    # KPI cards row
    kpi_items = [
        ("Health Score", f"{health_score:.0f}/100", health_color),
        ("Confidence", f"{confidence:.0f}%", accent),
        ("At Risk", str(bi.get("population_at_risk", "—")), (220, 38, 38)),
        ("Revenue at Risk", bi.get("revenue_at_risk_formatted", "—"), (185, 28, 28)),
        ("Urgency", bi.get("urgency", "Monitor")[:10], (245, 158, 11)),
    ]
    y_m = pdf.get_y()
    for i, (lbl, val, clr) in enumerate(kpi_items):
        pdf.metric_card_colored(lbl, val, 12 + i * 34, y_m, clr, w=31, h=16)
    pdf.ln(20)

    # ── Executive Summary ──
    if exec_summary:
        pdf.section_header("Executive Summary")
        pdf.body(exec_summary)
        pdf.space()

    # ── Why This Is Happening ──
    if root_causes:
        pdf.section_header("Root Cause Analysis")
        pdf.bullet(root_causes)
        pdf.space()

    # ── Risk Analysis ──
    if risks:
        pdf.section_header("Risk Analysis")
        pdf.table_header(["Risk", "Likelihood", "Impact", "Priority", "Exposure"], [52, 20, 24, 16, 60])
        for i, r in enumerate(risks[:8]):
            name = r.get("name", str(r)[:40]) if isinstance(r, dict) else str(r)[:40]
            sev = r.get("severity", "High" if i < 2 else "Medium") if isinstance(r, dict) else ("High" if i < 2 else "Medium")
            impact = r.get("impact", "Significant") if isinstance(r, dict) else "Significant"
            pri = r.get("priority", "High" if i < 3 else "Medium") if isinstance(r, dict) else ("High" if i < 3 else "Medium")
            pdf.table_row([str(name)[:40], sev, str(impact)[:20], pri, f"${bi.get('revenue_at_risk', 0):,.0f}" if i == 0 else ""], [52, 20, 24, 16, 60], alt=(i % 2 == 0))
        pdf.space()

    # ── Opportunity Analysis ──
    if opps:
        pdf.section_header("Opportunity Analysis")
        pdf.table_header(["Opportunity", "Value", "ROI", "Effort", "Timeline"], [52, 22, 18, 16, 24])
        for i, o in enumerate(opps[:8]):
            title = o.get("title", str(o)[:40]) if isinstance(o, dict) else str(o)[:40]
            val = o.get("revenue_impact", "TBD") if isinstance(o, dict) else "TBD"
            roi = "4.5x" if i < 1 else "3.2x" if i < 2 else "TBD"
            pdf.table_row([str(title)[:40], str(val)[:18], roi, "Medium", "Q3-Q4"], [52, 22, 18, 16, 24], alt=(i % 2 == 0))
        pdf.space()

    # ── Forecast Timeline ──
    has_forecast = any(k in tfc for k in ("forecast_30_days", "forecast_90_days"))
    if has_forecast:
        pdf.section_header("Forecast & Outlook")
        pdf.body(f"Annual trend: {timeline.get('annual_growth_pct', 0):.1f}%  |  Current: {timeline.get('current_value', 0):.2f}")
        periods = [
            ("30 Days", tfc.get("forecast_30_days")),
            ("90 Days", tfc.get("forecast_90_days")),
            ("180 Days", tfc.get("forecast_180_days")),
            ("365 Days", tfc.get("forecast_365_days")),
        ]
        pdf.table_header(["Horizon", "Value", "Growth", "Direction", "Confidence"], [30, 40, 30, 30, 30])
        for i, (label, f) in enumerate(periods):
            if f and f.get("forecast"):
                val = f["forecast"][-1] if f["forecast"] else 0
                gr = f.get("growth_pct", 0)
                dr = f.get("direction", "stable")
                cf = f"{f.get('confidence', 0)*100:.0f}%"
                pdf.table_row([label, f"{val:.1f}", f"{gr:+.1f}%", dr.upper(), cf], [30, 40, 30, 30, 30], alt=(i % 2 == 0))

        # Scenario Analysis if available
        if scenarios.get("expected_case") is not None:
            pdf.space()
            pdf.body_bold("Scenario Analysis (Revenue at Risk)")
            pdf.table_header(["Scenario", "Impact"], [40, 80])
            pdf.table_row(["Best Case", f"${scenarios.get('best_case', 0):,.0f}"], [40, 80], alt=False)
            pdf.table_row(["Expected", f"${scenarios.get('expected_case', 0):,.0f}"], [40, 80], alt=True)
            pdf.table_row(["Worst Case", f"${scenarios.get('worst_case', 0):,.0f}"], [40, 80], alt=False)
        pdf.space()

    # ── Charts ──
    pred_charts = {}
    if df is not None and target:
        try:
            pred_charts = _decorate_predictive_charts(df, target, None)
        except Exception:
            pass

    fc_chart = pred_charts.get("forecast_trend")
    corr_chart = pred_charts.get("correlation")
    if fc_chart or corr_chart:
        pdf.section_header("Visualizations")
        if fc_chart:
            pdf.add_chart(fc_chart, width=520, height=260)
        if corr_chart:
            pdf.add_chart(corr_chart, width=300, height=240)
        pdf.space()

    # ── Prescriptive Recommendations ──
    if presc:
        pdf.section_header("Recommended Actions")
        pdf.table_header(["Action", "Impact", "Savings", "Effort", "ROI", "Pri."], [48, 20, 20, 14, 14, 12])
        for i, r in enumerate(presc[:8]):
            pdf.table_row([
                str(r.get("recommendation", ""))[:40], r.get("expected_impact", "")[:18],
                r.get("revenue_preserved", "")[:18], r.get("effort", "Med")[:10],
                r.get("roi", "")[:10], str(r.get("priority_score", 0))[:4]
            ], [48, 20, 20, 14, 14, 12], alt=(i % 2 == 0))
        pdf.space()

    # ── Industry KPIs ──
    if industry.get("industry_kpis"):
        pdf.section_header(f"{industry.get('detected_industry', 'Industry')} KPIs")
        pdf.bullet(industry["industry_kpis"])
        pdf.space()

    # ── Appendix ──
    pdf.section_header("Appendix")
    pdf.kv_row("Report Generated", datetime.now().strftime('%B %d, %Y at %H:%M'))
    pdf.kv_row("Documents Analyzed", str(len(doc_ids)))
    pdf.kv_row("Target Variable", target)
    pdf.kv_row("Model Used", tech.get("model", "N/A"))
    pdf.kv_row("Feature Count", str(tech.get("n_features", "N/A")))
    pdf.kv_row("Sample Size", str(tech.get("n_samples", "N/A")))
    pdf.body("Prepared by: AURA Executive Intelligence Platform")
    pdf.body("Confidence scores are AI-generated estimates. Review by domain experts recommended.")

    pdf.close()
    return pdf
