import io
import json
import logging
import tempfile
from datetime import datetime
from pathlib import Path

import plotly.graph_objects as go
from fpdf import FPDF

from app.database.database import get_session_factory
from app.models.document import Document
from app.services.analytics_service import get_analytics
from app.services.chart_service import generate_charts as _generate_charts, _correlation_heatmap
from app.services.insights_service import generate_insights as _generate_insights
from app.services.health_service import get_dataset_health
from app.services.forecasting_service import generate_forecast
from app.services.ai_service import generate_response
from sqlalchemy import select

logger = logging.getLogger(__name__)


def _render_chart_png(chart_json: dict, width=500, height=280) -> bytes | None:
    try:
        fig = go.Figure(json.loads(json.dumps(chart_json)))
        return fig.to_image(format="png", width=width, height=height, scale=2)
    except Exception:
        return None


def _make_chart_image(chart_json: dict, width=500, height=280) -> str | None:
    data = _render_chart_png(chart_json, width, height)
    if data is None:
        return None
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    tmp.write(data)
    tmp.close()
    return tmp.name


async def generate_board_report(doc_id: int, company_name: str = "") -> bytes:
    doc_title = company_name or f"Document #{doc_id}"
    try:
        async with get_session_factory()() as db:
            result = await db.execute(select(Document).where(Document.id == doc_id))
            doc = result.scalar_one_or_none()
            if doc:
                doc_title = company_name or doc.title
    except Exception:
        doc = None

    analytics = charts = insights = health = forecast = None
    if doc and doc.content:
        try:
            analytics = await get_analytics(doc_id)
            if analytics and analytics.columns:
                first_col = analytics.columns[0].name
                charts = await _generate_charts(doc_id, first_col) or {}
                charts["correlation"] = _correlation_heatmap(
                    __import__("pandas").read_csv(io.StringIO(doc.content))
                ) if doc else None
        except Exception:
            pass
        try:
            insights = await _generate_insights(doc_id)
        except Exception:
            pass
        try:
            health = await get_dataset_health(doc_id)
        except Exception:
            pass
        try:
            num_cols = analytics.columns if analytics else []
            numeric = [c for c in num_cols if c.dtype == "numeric"]
            if numeric:
                forecast = await generate_forecast(doc_id, numeric[0].name, 12)
        except Exception:
            pass

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)

    # Cover
    pdf.add_page()
    pdf.ln(40)
    pdf.set_font("Helvetica", "B", 36)
    pdf.set_text_color(20, 30, 50)
    pdf.cell(0, 18, "Board Report", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)
    pdf.set_font("Helvetica", "", 20)
    pdf.set_text_color(59, 130, 246)
    pdf.cell(0, 12, doc_title, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 8, f"Prepared: {datetime.now().strftime('%B %d, %Y')}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "Confidential - For Board Members Only", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(30)
    pdf.set_draw_color(59, 130, 246)
    pdf.set_line_width(0.5)
    mid = pdf.w / 2
    pdf.line(mid - 30, pdf.get_y(), mid + 30, pdf.get_y())

    def _section(num: str, title: str):
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 22)
        pdf.set_text_color(20, 30, 50)
        pdf.cell(0, 14, f"{num}. {title}", new_x="LMARGIN", new_y="NEXT")
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
        for item in items:
            pdf.set_font("Helvetica", "", 10)
            pdf.set_text_color(60, 60, 60)
            pdf.cell(5)
            pdf.cell(0, 6, f"- {item}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

    # 1. Executive Summary
    _section("1", "Executive Summary")
    if insights:
        _body(insights.get("executive_summary", "No summary available."))
    else:
        _body("Analysis could not be completed.")

    # 2. Organization Health Score
    _section("2", "Organization Health Score")
    if health:
        _body(f"Overall Health: {health.get('overall', 'N/A')}/100 - {health.get('label', 'N/A')}")
        _body(f"Completeness: {health.get('completeness', 0)}/100")
        _body(f"Quality: {health.get('quality', 0)}/100")
        _body(f"Consistency: {health.get('consistency', 0)}/100")
        _body(f"Missing Data: {health.get('missing_data', 0)}/100")
        _body(health.get("explanation", ""))
    else:
        _body("Health scoring unavailable.")

    # 3. Key Findings
    _section("3", "Key Findings")
    if insights:
        _bullet(insights.get("key_findings", ["No findings identified."]))
    else:
        _body("No findings available.")

    # 4. KPI Performance
    _section("4", "KPI Performance")
    if analytics:
        _body(f"Total Records: {analytics.row_count}")
        _body(f"Total Fields: {analytics.column_count}")
        for col in analytics.columns[:10]:
            extra = ""
            if col.numeric:
                extra = f"  mean={col.numeric.get('mean','')}  range=[{col.numeric.get('min','')}, {col.numeric.get('max','')}]"
            elif col.categorical:
                tops = col.categorical.get("top_values", [])
                if tops:
                    extra = "  top: " + ", ".join(str(t["value"]) for t in tops[:3])
            _body(f"  {col.name} ({col.dtype})  missing={col.missing}/{col.total}{extra}")

    # 5. Risks
    _section("5", "Risks")
    if insights:
        _bullet(insights.get("risks", ["No risks identified."]))
    else:
        _body("Risk analysis unavailable.")

    # 6. Opportunities
    _section("6", "Opportunities")
    if insights:
        _bullet(insights.get("opportunities", ["No opportunities identified."]))
    else:
        _body("Opportunity analysis unavailable.")

    # 7. Forecasts
    _section("7", "Forecasts")
    if forecast and forecast.get("forecast"):
        _body(f"Trend: {forecast['trend_direction']} | Strength: {forecast['trend_strength']*100:.0f}%")
        _body(f"Confidence: {forecast['confidence_avg']*100:.0f}%")
        _body(forecast.get("explanation", ""))
    else:
        _body("Forecast data unavailable.")

    # 8. Strategic Recommendations
    _section("8", "Strategic Recommendations")
    if insights:
        _bullet(insights.get("recommendations", ["No recommendations available."]))
    else:
        _body("Recommendations unavailable.")

    # 9. Supporting Analytics
    _section("9", "Supporting Analytics")
    if charts:
        for chart_type in ("bar", "pie", "line"):
            chart_json = charts.get(chart_type)
            if not chart_json:
                continue
            img_path = _make_chart_image(chart_json, 480, 260)
            if img_path:
                try:
                    pdf.image(img_path, x=15, w=pdf.w - 30)
                    pdf.ln(4)
                finally:
                    Path(img_path).unlink(missing_ok=True)

    # 10. Appendix
    _section("10", "Appendix")
    _body(f"Report ID: AURA-BR-{doc_id}-{datetime.now().strftime('%Y%m%d')}")
    _body(f"Prepared by AURA Enterprise Intelligence")
    _body("Confidence scores are AI-generated estimates and should be reviewed by domain experts.")
    _body("This report is generated from uploaded organizational data and AI analysis.")

    pdf.ln(10)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 6, "AURA - Enterprise Intelligence Platform | Confidential", align="C", new_x="LMARGIN", new_y="NEXT")

    return bytes(pdf.output())
