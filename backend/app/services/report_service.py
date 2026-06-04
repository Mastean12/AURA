import io
import json
import logging
import tempfile
from datetime import datetime
from pathlib import Path

import plotly.graph_objects as go
from fpdf import FPDF

from app.services.summary_service import summarize_document
from app.services.analytics_service import get_analytics
from app.services.chart_service import generate_charts

logger = logging.getLogger(__name__)

REPORT_TYPES = [1, 2, 3]


def _render_chart_png(chart_json: dict) -> bytes | None:
    try:
        fig = go.Figure(json.loads(json.dumps(chart_json)))
        return fig.to_image(format="png", width=600, height=350, scale=2)
    except Exception as e:
        logger.warning("Chart render failed: %s", e)
        return None


def _make_chart_image(chart_json: dict) -> str | None:
    data = _render_chart_png(chart_json)
    if data is None:
        return None
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    tmp.write(data)
    tmp.close()
    return tmp.name


async def generate_report(doc_id: int) -> bytes:
    content_parts: dict[int, list[dict]] = {}
    for st in REPORT_TYPES:
        try:
            resp = await summarize_document(doc_id, st)
            content_parts[st] = resp.content
        except Exception as e:
            logger.warning("Summary type %d failed: %s", st, e)
            content_parts[st] = [{"error": str(e)}]

    analytics = None
    charts = {}
    try:
        analytics = await get_analytics(doc_id)
        if analytics and analytics.columns:
            first_col = analytics.columns[0].name
            charts = generate_charts(doc_id, first_col) or {}
    except Exception as e:
        logger.warning("Analytics/charts failed: %s", e)

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

        doc = asyncio.run(_fetch())
        if doc:
            doc_title = doc.title
    except Exception as e:
        logger.warning("Failed to fetch doc title: %s", e)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=20)

    # --- Cover page ---
    pdf.add_page()
    pdf.ln(60)
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(59, 130, 246)
    pdf.cell(0, 14, "AURA Report", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)
    pdf.set_font("Helvetica", "", 16)
    pdf.set_text_color(160, 160, 160)
    pdf.cell(0, 10, doc_title, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, datetime.now().strftime("%B %d, %Y"), align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(30)
    pdf.set_draw_color(59, 130, 246)
    pdf.set_line_width(0.5)
    mid = pdf.w / 2
    pdf.line(mid - 20, pdf.get_y(), mid + 20, pdf.get_y())

    # --- Helper ---
    def _section_header(title: str):
        pdf.add_page()
        pdf.set_font("Helvetica", "B", 18)
        pdf.set_text_color(30, 30, 30)
        pdf.cell(0, 12, title, new_x="LMARGIN", new_y="NEXT")
        pdf.set_draw_color(59, 130, 246)
        pdf.set_line_width(0.4)
        pdf.line(10, pdf.get_y(), pdf.w - 10, pdf.get_y())
        pdf.ln(6)

    def _body(text: str):
        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(60, 60, 60)
        pdf.multi_cell(0, 5.5, text)
        pdf.ln(3)

    # --- 1. Executive Summary ---
    _section_header("1. Executive Summary")
    items = content_parts.get(1, [])
    for item in items:
        title = item.get("title") or item.get("summary", "")
        if title:
            pdf.set_font("Helvetica", "B", 11)
            pdf.set_text_color(30, 30, 30)
            pdf.cell(0, 7, str(title)[:80], new_x="LMARGIN", new_y="NEXT")
        summary = item.get("summary", "")
        if summary:
            _body(str(summary))
        pts = item.get("key_points", [])
        if isinstance(pts, list):
            for pt in pts:
                pdf.set_font("Helvetica", "", 10)
                pdf.set_text_color(60, 60, 60)
                pdf.cell(5)
                pdf.cell(0, 6, f"- {pt}", new_x="LMARGIN", new_y="NEXT")

    # --- 2. Key Findings ---
    _section_header("2. Key Findings")
    items = content_parts.get(2, [])
    for item in items:
        findings = item.get("findings", [])
        if isinstance(findings, list):
            for f in findings:
                pdf.set_font("Helvetica", "B", 10)
                pdf.set_text_color(30, 30, 30)
                pdf.cell(0, 7, str(f.get("finding", ""))[:100], new_x="LMARGIN", new_y="NEXT")
                sig = f.get("significance", "")
                if sig:
                    pdf.set_font("Helvetica", "", 9)
                    pdf.set_text_color(130, 130, 130)
                    pdf.cell(10)
                    pdf.cell(0, 6, f"Significance: {sig}", new_x="LMARGIN", new_y="NEXT")
                pdf.ln(2)

    # --- 3. Charts & Analytics ---
    _section_header("3. Charts & Analytics")
    if analytics:
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(30, 30, 30)
        pdf.cell(0, 7, f"Rows: {analytics.row_count}   Columns: {analytics.column_count}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)
        for col in analytics.columns[:6]:
            pdf.set_font("Helvetica", "", 9)
            pdf.set_text_color(60, 60, 60)
            extra = ""
            if col.numeric:
                extra = f"  mean={col.numeric.get('mean','')}  min={col.numeric.get('min','')}  max={col.numeric.get('max','')}"
            elif col.categorical:
                tops = col.categorical.get("top_values", [])
                if tops:
                    extra = "  top: " + ", ".join(str(t["value"]) for t in tops[:3])
            pdf.cell(0, 6, f"  {col.name} ({col.dtype})  missing={col.missing}/{col.total}{extra}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

    for chart_type in ("bar", "pie", "line"):
        chart_json = charts.get(chart_type)
        if not chart_json:
            continue
        img_path = _make_chart_image(chart_json)
        if img_path:
            try:
                pdf.image(img_path, x=10, w=pdf.w - 20)
                pdf.ln(4)
            finally:
                Path(img_path).unlink(missing_ok=True)

    # --- 4. Recommendations ---
    _section_header("4. Recommendations")
    items = content_parts.get(3, [])
    for item in items:
        recs = item.get("recommendations", [])
        if isinstance(recs, list):
            for r in recs:
                pdf.set_font("Helvetica", "B", 10)
                pdf.set_text_color(30, 30, 30)
                pdf.cell(0, 7, str(r.get("recommendation", ""))[:100], new_x="LMARGIN", new_y="NEXT")
                priority = r.get("priority", "")
                impact = r.get("impact", "")
                pdf.set_font("Helvetica", "", 9)
                pdf.set_text_color(130, 130, 130)
                parts = []
                if priority:
                    parts.append(f"Priority: {priority}")
                if impact:
                    parts.append(f"Impact: {impact}")
                if parts:
                    pdf.cell(10)
                    pdf.cell(0, 6, "  ".join(parts), new_x="LMARGIN", new_y="NEXT")
                pdf.ln(2)

    # --- Footer ---
    pdf.ln(10)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(180, 180, 180)
    pdf.cell(0, 6, "Generated by AURA - AI Unified Research Assistant", align="C", new_x="LMARGIN", new_y="NEXT")

    return bytes(pdf.output())
