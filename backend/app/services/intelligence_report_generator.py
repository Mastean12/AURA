import io
import logging
from datetime import datetime

import pandas as pd

from app.services.report_engine import ReportPDF, _decorate_predictive_charts
from app.services.analytics_service import get_analytics
from app.services.insights_service import generate_insights as _generate_insights
from app.services.health_service import get_dataset_health
from app.services.forecasting_service import generate_forecast
from app.services.chart_service import generate_charts as _generate_charts
from app.database.database import get_session_factory
from app.models.document import Document
from sqlalchemy import select

logger = logging.getLogger(__name__)


async def generate_intelligence_report(doc_ids: list[int], org_name: str = "",
                                       org_logo_url: str = "", org_color: str = "",
                                       workspace: str = "") -> bytes:
    if not doc_ids:
        return ReportPDF("No Data", "Intelligence Report", org_name).close()

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

    insights = {}
    health = {}
    analytics = None
    charts = {}
    forecast = None
    df = None
    try:
        insights = await _generate_insights(primary)
    except Exception:
        pass
    try:
        health = await get_dataset_health(primary)
    except Exception:
        pass
    try:
        analytics = await get_analytics(primary)
        if analytics and analytics.columns:
            first_col = analytics.columns[0].name
            charts = await _generate_charts(primary, first_col) or {}
            numeric_cols = [c for c in analytics.columns if c.dtype == "numeric"]
            if numeric_cols:
                forecast = await generate_forecast(primary, numeric_cols[0].name, 12)
    except Exception:
        pass

    try:
        async with get_session_factory()() as db:
            r = await db.execute(select(Document).where(Document.id == primary))
            d = r.scalar_one_or_none()
            if d and d.content:
                df = pd.read_csv(io.StringIO(d.content))
    except Exception:
        pass

    target = ""
    if df is not None:
        target = df.columns[-1] if len(df.columns) > 0 else ""

    exec_summary = insights.get("executive_summary", "")
    findings = insights.get("key_findings", [])
    risks_raw = insights.get("risks", [])
    opps_raw = insights.get("opportunities", [])
    recs_raw = insights.get("recommendations", [])
    confidence = insights.get("confidence_score", 50)
    health_score = health.get("overall", 0) if health else 0
    health_label = health.get("label", "N/A") if health else "N/A"

    pred_charts = {}
    if df is not None and target:
        pred_charts = _decorate_predictive_charts(df, target, None)

    try:
        color_hex = org_color.lstrip("#")
        accent = tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))
    except Exception:
        accent = (37, 99, 235)

    pdf = ReportPDF(doc_title, "Executive Intelligence Report", org_name, org_logo_url, accent)
    pdf.alias_nb_pages()

    pdf.cover_page(
        subtitle="Executive Intelligence Report",
        workspace=workspace,
    )

    if health_score >= 70:
        health_color = (16, 185, 129)
    elif health_score >= 40:
        health_color = (245, 158, 11)
    else:
        health_color = (220, 38, 38)

    if exec_summary:
        pdf.section_header("Executive Summary")
        pdf.body(exec_summary)
        pdf.space()

    y_m = pdf.get_y()
    if y_m + 25 > pdf.h - 25:
        pdf.add_page()
        y_m = pdf.get_y()

    pdf.section_header("Performance Dashboard")
    metrics = [
        ("Health Score", f"{health_score}/100", health_color),
        ("Confidence", f"{confidence}%", accent),
        ("Risks", str(len(risks_raw)), (220, 38, 38)),
        ("Opportunities", str(len(opps_raw)), (16, 185, 129)),
        ("Data Quality", f"{health.get('completeness', 0)}/100" if health else "N/A", (37, 99, 235)),
    ]
    for i, (lbl, val, clr) in enumerate(metrics):
        pdf.metric_card_colored(lbl, val, 12 + i * 37, pdf.get_y(), clr, w=34, h=18)
    pdf.ln(22)
    pdf.space()

    if findings:
        pdf.section_header("Key Findings")
        pdf.bullet(findings)
        pdf.space()

    if risks_raw:
        pdf.section_header("Risk Analysis")
        pdf.table_header(["Risk", "Likelihood", "Impact", "Priority"], [56, 22, 24, 20])
        for i, r in enumerate(risks_raw[:8]):
            sev = "High" if i < 2 else "Medium" if i < 5 else "Low"
            pdf.table_row([str(r)[:45], sev, "Medium", "High" if i < 2 else "Med"],
                          [56, 22, 24, 20], alt=(i % 2 == 0))
        pdf.space()

    if opps_raw:
        pdf.section_header("Opportunity Analysis")
        pdf.table_header(["Opportunity", "Potential Value", "ROI", "Effort", "Timeline"], [44, 24, 16, 16, 22])
        for i, o in enumerate(opps_raw[:8]):
            pdf.table_row([str(o)[:34], "TBD", "TBD", "Medium", "Q3-Q4"],
                          [44, 24, 16, 16, 22], alt=(i % 2 == 0))
        pdf.space()

    if forecast:
        pdf.section_header("Forecast")
        pdf.body(f"Trend: {forecast['trend_direction'].upper()}  |  "
                 f"Strength: {forecast['trend_strength']*100:.0f}%  |  "
                 f"Confidence: {forecast['confidence_avg']*100:.0f}%")
        if forecast.get("explanation"):
            pdf.body(forecast["explanation"])
        pdf.space()

    fc_chart = pred_charts.get("forecast_trend")
    corr_chart = pred_charts.get("correlation")
    if fc_chart or corr_chart:
        pdf.section_header("Visualizations")
        if fc_chart:
            pdf.add_chart(fc_chart, width=520, height=260)
        if corr_chart:
            if pdf.get_y() > pdf.h - 100:
                pdf.add_page()
            pdf.add_chart(corr_chart, width=300, height=240)
        pdf.space()

    if recs_raw:
        pdf.section_header("Recommended Actions")
        for i, rec in enumerate(recs_raw[:8]):
            pdf.set_font("Helvetica", "B", 8)
            pdf.set_text_color(* (20, 30, 50))
            pdf.cell(5)
            pdf.cell(0, 5, f"{i+1}. {str(rec)[:90]}", new_x="LMARGIN", new_y="NEXT")
        pdf.space()

    if len(doc_ids) > 1:
        pdf.section_header("Multi-Source Analysis")
        pdf.body(f"Analysis across {len(doc_ids)} documents.")
        for i, did in enumerate(doc_ids):
            pdf.bullet([f"Document #{did}"])
        pdf.space()

    pdf.section_header("Appendix")
    pdf.kv_row("Report Generated", datetime.now().strftime('%B %d, %Y at %H:%M'))
    if analytics:
        pdf.kv_row("Records Analyzed", str(analytics.row_count))
        pdf.kv_row("Fields Analyzed", str(analytics.column_count))
    pdf.kv_row("Documents Analyzed", str(len(doc_ids)))
    pdf.body("Prepared by: AURA Executive Intelligence Platform")
    pdf.body("Confidence scores are AI-generated estimates. Review by domain experts recommended.")

    pdf.close()
    return pdf
