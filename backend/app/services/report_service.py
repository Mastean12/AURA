import io
import json
import logging
import tempfile
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from fpdf import FPDF

from app.services.summary_service import summarize_document
from app.services.analytics_service import get_analytics
from app.services.chart_service import generate_charts as _generate_charts, _correlation_heatmap
from app.services.insights_service import generate_insights as _generate_insights
from app.services.health_service import get_dataset_health

logger = logging.getLogger(__name__)


def _render_chart_png(chart_json: dict, width=600, height=350) -> bytes | None:
    try:
        fig = go.Figure(json.loads(json.dumps(chart_json)))
        return fig.to_image(format="png", width=width, height=height, scale=2)
    except Exception as e:
        logger.warning("Chart render failed: %s", e)
        return None


def _make_chart_image(chart_json: dict, width=600, height=350) -> str | None:
    data = _render_chart_png(chart_json, width, height)
    if data is None:
        return None
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    tmp.write(data)
    tmp.close()
    return tmp.name


async def generate_report(doc_id: int) -> bytes:
    doc_title = f"Document #{doc_id}"
    try:
        from app.database.database import get_session_factory
        from app.models.document import Document
        from sqlalchemy import select
        import asyncio
        factory = get_session_factory()
        async def _fetch():
            async with factory() as db:
                result = await db.execute(select(Document).where(Document.id == doc_id))
                return result.scalar_one_or_none()
        doc = await _fetch()
        if doc:
            doc_title = doc.title
    except Exception:
        pass

    analytics = None
    charts = {}
    insights = None
    health = None
    try:
        analytics = await get_analytics(doc_id)
        if analytics and analytics.columns:
            first_col = analytics.columns[0].name
            charts = await _generate_charts(doc_id, first_col) or {}
            charts["correlation"] = _correlation_heatmap(
                pd.read_csv(io.StringIO(doc.content)) if doc else None
            ) if doc else None
    except Exception as e:
        logger.warning("Analytics/charts failed: %s", e)

    try:
        insights = await _generate_insights(doc_id)  # noqa: F811
    except Exception as e:
        logger.warning("Insights failed: %s", e)

    try:
        health = await get_dataset_health(doc_id)
    except Exception as e:
        logger.warning("Health failed: %s", e)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)

    # --- Cover Page ---
    pdf.add_page()
    pdf.ln(50)
    pdf.set_font("Helvetica", "B", 32)
    pdf.set_text_color(59, 130, 246)
    pdf.cell(0, 16, "AURA Analytics Report", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)
    pdf.set_font("Helvetica", "", 18)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 12, doc_title, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.cell(0, 8, "Confidential", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(40)
    pdf.set_draw_color(59, 130, 246)
    pdf.set_line_width(0.5)
    mid = pdf.w / 2
    pdf.line(mid - 25, pdf.get_y(), mid + 25, pdf.get_y())

    def _section_header(title: str, num: str = ""):
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 20)
        pdf.set_text_color(30, 30, 30)
        label = f"{num}. {title}" if num else title
        pdf.cell(0, 14, label, new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(59, 130, 246)
        pdf.set_line_width(0.5)
        pdf.line(10, pdf.get_y(), pdf.w - 10, pdf.get_y())
        pdf.ln(6)

    def _body(text: str):
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(60, 60, 60)
        pdf.multi_cell(0, 5.5, str(text))
        pdf.ln(2)

    def _bullet(items: list):
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(60, 60, 60)
        for item in items:
            pdf.cell(5)
            pdf.cell(0, 6, f"- {item}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

    # --- 1. Executive Summary ---
    _section_header("Executive Summary", "1")
    if insights:
        _body(insights.get("executive_summary", "No summary available."))
    else:
        _body("Executive summary could not be generated.")

    # --- 2. Dataset Overview ---
    _section_header("Dataset Overview", "2")
    if analytics:
        _body(f"Rows: {analytics.row_count}   Columns: {analytics.column_count}")
        for col in analytics.columns[:8]:
            extra = ""
            if col.numeric:
                extra = f"  mean={col.numeric.get('mean','')}  range=[{col.numeric.get('min','')}, {col.numeric.get('max','')}]"
            elif col.categorical:
                tops = col.categorical.get("top_values", [])
                if tops:
                    extra = "  top: " + ", ".join(str(t["value"]) for t in tops[:3])
            _body(f"  {col.name} ({col.dtype})  missing={col.missing}/{col.total}{extra}")

    # --- 3. Dataset Health ---
    _section_header("Dataset Health", "3")
    if health:
        _body(f"Overall Score: {health.get('overall', 'N/A')}/100 - {health.get('label', 'N/A')}")
        _body(f"Completeness: {health.get('completeness', 0)}/100")
        _body(f"Quality: {health.get('quality', 0)}/100")
        _body(f"Consistency: {health.get('consistency', 0)}/100")
        _body(f"Missing Data: {health.get('missing_data', 0)}/100")
        _body(health.get("explanation", ""))
    else:
        _body("Health scoring unavailable.")

    # --- 4. Key Findings ---
    _section_header("Key Findings", "4")
    if insights:
        _bullet(insights.get("key_findings", ["No findings identified."]))
    else:
        _body("No findings available.")

    # --- 5. KPI Summary ---
    _section_header("KPI Summary", "5")
    if analytics:
        _body(f"Total Records: {analytics.row_count}")
        _body(f"Total Fields: {analytics.column_count}")
        total_missing = sum(c.missing for c in analytics.columns)
        _body(f"Total Missing Values: {total_missing}")
        num_cols = sum(1 for c in analytics.columns if c.dtype == "numeric")
        cat_cols = sum(1 for c in analytics.columns if c.dtype == "categorical")
        _body(f"Numeric Columns: {num_cols}")
        _body(f"Categorical Columns: {cat_cols}")

    # --- 6. Visualizations ---
    _section_header("Visualizations", "6")
    for chart_type in ("bar", "pie", "line", "area", "histogram", "distribution", "correlation"):
        chart_json = charts.get(chart_type)
        if not chart_json:
            continue
        img_path = _make_chart_image(chart_json, width=500, height=300)
        if img_path:
            try:
                pdf.image(img_path, x=15, w=pdf.w - 30)
                pdf.ln(4)
            finally:
                Path(img_path).unlink(missing_ok=True)

    # --- 7. Risks ---
    _section_header("Risks", "7")
    if insights:
        _bullet(insights.get("risks", ["No risks identified."]))
    else:
        _body("Risk analysis unavailable.")

    # --- 8. Opportunities ---
    _section_header("Opportunities", "8")
    if insights:
        _bullet(insights.get("opportunities", ["No opportunities identified."]))
    else:
        _body("Opportunity analysis unavailable.")

    # --- 9. Recommendations ---
    _section_header("Recommendations", "9")
    if insights:
        _bullet(insights.get("recommendations", ["No recommendations available."]))
    else:
        _body("Recommendations unavailable.")

    # --- 10. Appendix ---
    _section_header("Appendix", "10")
    _body(f"Report ID: AURA-{doc_id}-{datetime.now().strftime('%Y%m%d-%H%M')}")
    _body(f"Generated by AURA Analytics v2")
    _body(f"AI Provider: Gemini 2.5 Flash")
    _body("Confidence scores are AI-generated estimates and should be reviewed by domain experts.")

    pdf.ln(10)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 6, "AURA - AI Unified Research Assistant | Confidential", align="C", new_x="LMARGIN", new_y="NEXT")

    return bytes(pdf.output())
