import io
import json
import logging
import tempfile
from datetime import datetime
from pathlib import Path

import plotly.graph_objects as go
import numpy as np
from fpdf import FPDF

logger = logging.getLogger(__name__)

DARK = (20, 30, 50)
MID = (60, 60, 60)
LIGHT = (120, 120, 120)
WHITE = (255, 255, 255)
BG_LIGHT = (245, 247, 250)

ROW_COLORS = [
    (245, 247, 250),
    (255, 255, 255),
]


def render_chart_png(chart_json: dict, width=500, height=280) -> bytes | None:
    try:
        fig = go.Figure(json.loads(json.dumps(chart_json)))
        return fig.to_image(format="png", width=width, height=height, scale=2)
    except Exception:
        return None


def make_chart_image(chart_json: dict, width=500, height=280) -> str | None:
    data = render_chart_png(chart_json, width, height)
    if data is None:
        return None
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    tmp.write(data)
    tmp.close()
    return tmp.name


class ReportPDF(FPDF):
    def __init__(self, title: str, report_type: str = "Report",
                 org_name: str = "", org_logo_url: str = "",
                 accent_color: tuple = (37, 99, 235)):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=20)
        self._title = title
        self._type = report_type
        self._org_name = org_name
        self._org_logo_url = org_logo_url
        self._accent = accent_color
        self._accent_light = (
            min(accent_color[0] + 100, 255),
            min(accent_color[1] + 100, 255),
            min(accent_color[2] + 100, 255),
        )
        ts = datetime.now().strftime('%Y%m%d-%H%M%S')
        safe_title = ''.join(c if c.isalnum() or c in ' -_' else '' for c in title)[:40]
        safe_org = ''.join(c if c.isalnum() or c in ' -_' else '' for c in org_name)[:20]
        safe_type = report_type.replace(' ', '_')
        self._filename = f"{safe_org}_{safe_title}_{safe_type}_{ts}.pdf".replace('__', '_').strip('_')
        self._report_id = f"EXEC-{ts}"

    def _sanitize(self, text: str) -> str:
        return text.encode('latin-1', 'replace').decode('latin-1')

    def header(self):
        if self.page_no() > 1:
            self.set_font("Helvetica", "", 7)
            self.set_text_color(*LIGHT)
            org = self._org_name if self._org_name else "AURA Executive Intelligence"
            self.cell(0, 6, self._sanitize(f"{org}  |  {self._type}"), new_x="LMARGIN", new_y="NEXT")
            self.set_draw_color(*self._accent)
            self.set_line_width(0.3)
            self.line(10, self.get_y(), self.w - 10, self.get_y())
            self.ln(3)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*LIGHT)
        label = f"Confidential  |  {self._report_id}  |  Page {self.page_no()}/{{nb}}"
        self.cell(0, 10, label, align="C")

    def cover_page(self, subtitle: str = "", workspace: str = "",
                   confidentiality: str = "CONFIDENTIAL"):
        self.add_page()
        self.ln(20)
        accent = self._accent
        self.set_fill_color(*DARK)
        self.rect(0, 0, self.w, 85, "F")
        self.set_y(18)
        if self._org_name:
            self.set_font("Helvetica", "B", 26)
            self.set_text_color(*WHITE)
            self.cell(0, 14, self._sanitize(self._org_name.upper()), align="C", new_x="LMARGIN", new_y="NEXT")
            self.ln(4)
        self.set_font("Helvetica", "", 16)
        self.set_text_color(*self._accent_light)
        self.cell(0, 10, self._sanitize(self._type), align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(6)
        self.set_font("Helvetica", "B", 20)
        self.set_text_color(*WHITE)
        self.cell(0, 12, self._sanitize(self._title), align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(30)
        if subtitle:
            self.set_font("Helvetica", "", 11)
            self.set_text_color(*MID)
            self.cell(0, 7, self._sanitize(subtitle), align="C", new_x="LMARGIN", new_y="NEXT")
            self.ln(2)
        if workspace:
            self.set_font("Helvetica", "", 10)
            self.set_text_color(*LIGHT)
            self.cell(0, 6, f"Workspace: {self._sanitize(workspace)}", align="C", new_x="LMARGIN", new_y="NEXT")
            self.ln(2)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*LIGHT)
        self.cell(0, 6, f"Prepared: {datetime.now().strftime('%B %d, %Y')}", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(10)
        self.set_draw_color(*accent)
        self.set_line_width(0.5)
        mid = self.w / 2
        self.line(mid - 25, self.get_y(), mid + 25, self.get_y())
        self.ln(6)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*LIGHT)
        self.cell(0, 6, self._sanitize(confidentiality), align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(4)
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*LIGHT)
        self.cell(0, 5, "Prepared by: AURA Executive Intelligence Platform", align="C", new_x="LMARGIN", new_y="NEXT")

    def section_header(self, title: str, num: str = ""):
        if self.get_y() > self.h - 50:
            self.add_page()
        self.ln(2)
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(*DARK)
        label = f"{num}. {title}" if num else title
        self.cell(0, 10, self._sanitize(label), new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*self._accent)
        self.set_line_width(0.4)
        self.line(10, self.get_y(), self.w - 10, self.get_y())
        self.ln(3)

    def body(self, text: str):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*MID)
        self.multi_cell(0, 5, self._sanitize(str(text)))
        self.ln(1)

    def body_bold(self, text: str):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*DARK)
        self.multi_cell(0, 5, self._sanitize(str(text)))
        self.ln(1)

    def bullet(self, items: list[str]):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*MID)
        for item in items:
            self.cell(4)
            self.cell(0, 5, f"- {self._sanitize(str(item))}", new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def kv_row(self, key: str, value: str):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*LIGHT)
        self.cell(55, 5, self._sanitize(key))
        self.set_text_color(*MID)
        self.cell(0, 5, self._sanitize(str(value)), new_x="LMARGIN", new_y="NEXT")

    def metric_card(self, label: str, value: str, x: float, y: float, w: float = 48, h: float = 22):
        self.set_xy(x, y)
        self.set_fill_color(*BG_LIGHT)
        self.rect(x, y, w, h, "F")
        self.set_xy(x + 3, y + 3)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*LIGHT)
        self.cell(w - 6, 4, self._sanitize(label))
        self.set_xy(x + 3, y + 10)
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(*DARK)
        self.cell(w - 6, 6, self._sanitize(str(value)))

    def metric_card_colored(self, label: str, value: str, x: float, y: float,
                            color: tuple = None, w: float = 48, h: float = 22):
        c = color or self._accent
        self.set_xy(x, y)
        self.set_fill_color(*c)
        self.rect(x, y, w, h, "F")
        text_color = WHITE if sum(c) < 400 else DARK
        self.set_xy(x + 3, y + 3)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*text_color)
        self.cell(w - 6, 4, self._sanitize(label))
        self.set_xy(x + 3, y + 10)
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(*text_color)
        self.cell(w - 6, 6, self._sanitize(str(value)))

    def risk_row(self, name: str, severity: str, likelihood: str, impact: str):
        sev_colors = {"Critical": (185, 28, 28), "High": (220, 38, 38),
                      "Medium": (245, 158, 11), "Low": (37, 99, 235)}
        c = sev_colors.get(severity, MID)
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*DARK)
        self.cell(44, 5, self._sanitize(name[:30]))
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*c)
        self.cell(16, 5, severity, align="C")
        self.set_text_color(*MID)
        self.cell(16, 5, likelihood, align="C")
        self.set_text_color(*MID)
        self.cell(0, 5, self._sanitize(str(impact)[:55]), new_x="LMARGIN", new_y="NEXT")

    def opportunity_row(self, name: str, value: str, roi: str, effort: str, timeline: str):
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*DARK)
        self.cell(40, 5, self._sanitize(name[:28]))
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*self._accent)
        self.cell(18, 5, self._sanitize(str(value)[:14]), align="C")
        self.set_text_color(*MID)
        self.cell(14, 5, self._sanitize(str(roi)[:10]), align="C")
        self.set_text_color(*MID)
        self.cell(14, 5, self._sanitize(str(effort)[:10]), align="C")
        self.set_text_color(*MID)
        self.cell(0, 5, self._sanitize(str(timeline)[:20]), new_x="LMARGIN", new_y="NEXT")

    def rec_action_row(self, risk: str, action: str, impact: str, savings: str, effort: str, priority: str):
        pri_colors = {"Critical": (185, 28, 28), "High": (220, 38, 38),
                      "Medium": (245, 158, 11), "Low": (16, 185, 129)}
        c = pri_colors.get(priority, MID)
        self.set_font("Helvetica", "B", 8)
        self.set_text_color(*DARK)
        self.cell(34, 5, self._sanitize(str(risk)[:22]))
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*MID)
        self.cell(0, 5, self._sanitize(str(action)[:50]), new_x="LMARGIN", new_y="NEXT")
        self.set_x(10)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*LIGHT)
        self.cell(34, 4, "")
        self.cell(20, 4, self._sanitize(str(impact)[:14]), align="C")
        self.cell(20, 4, self._sanitize(str(savings)[:14]), align="C")
        self.cell(14, 4, self._sanitize(str(effort)[:10]), align="C")
        self.set_text_color(*c)
        self.cell(14, 4, self._sanitize(priority), align="C")
        self.ln(3)

    def table_header(self, cols: list[str], widths: list[int]):
        self.set_fill_color(*DARK)
        self.set_text_color(*WHITE)
        self.set_font("Helvetica", "B", 7)
        for i, col in enumerate(cols):
            self.cell(widths[i], 6, self._sanitize(col), border=1, fill=True, align="C")
        self.ln()

    def table_row(self, cells: list[str], widths: list[int], bold: bool = False, alt: bool = False):
        self.set_font("Helvetica", "B" if bold else "", 7)
        self.set_text_color(*MID)
        if alt:
            self.set_fill_color(*ROW_COLORS[0])
        for i, cell in enumerate(cells):
            self.cell(widths[i], 5.5, self._sanitize(str(cell))[:30], border=1, align="C", fill=alt)
        self.ln()

    def add_chart(self, chart_json: dict, width=480, height=260):
        img_path = make_chart_image(chart_json, width, height)
        if img_path:
            try:
                if self.get_y() + height / 3.5 > self.h - 25:
                    self.add_page()
                self.image(img_path, x=15, w=self.w - 30)
                self.ln(3)
            finally:
                Path(img_path).unlink(missing_ok=True)

    def add_chart_compact(self, chart_json: dict, x: float, y: float, w: float, h: float):
        img_path = make_chart_image(chart_json, int(w * 4), int(h * 4))
        if img_path:
            try:
                self.image(img_path, x=x, y=y, w=w, h=h)
            finally:
                Path(img_path).unlink(missing_ok=True)

    def space(self, lines: int = 1):
        self.ln(lines * 3)

    def close(self):
        if self.page_no() < 2:
            self.add_page()
        self.ln(8)
        self.set_draw_color(*self._accent)
        self.set_line_width(0.3)
        self.line(10, self.get_y(), self.w - 10, self.get_y())
        self.ln(4)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*LIGHT)
        self.cell(0, 5, f"{self._sanitize(self._title)}  |  {self._type}", align="C", new_x="LMARGIN", new_y="NEXT")
        self.cell(0, 5, "Prepared by: AURA Executive Intelligence Platform  |  Confidential", align="C", new_x="LMARGIN", new_y="NEXT")

    def to_bytes(self) -> bytes:
        return bytes(self.output())

    def filename(self) -> str:
        return self._filename

    def validate(self) -> list[str]:
        errors = []
        if not self._title:
            errors.append("Report title is missing")
        if self.page_no() < 2:
            errors.append("Report has no content pages")
        return errors


def _decorate_predictive_charts(df, target: str, forecast_data: dict = None) -> dict:
    import pandas as pd
    charts = {}
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    if target in numeric_cols:
        numeric_cols.remove(target)
    if not numeric_cols:
        return charts
    try:
        vals = pd.to_numeric(df[target], errors='coerce').dropna()
        if len(vals) < 3:
            return charts
        x = np.arange(len(vals))
        coeffs = np.polyfit(x, vals.values, min(2, len(vals) - 1))
        fitted = np.polyval(coeffs, x)
        future_x = np.arange(len(vals), len(vals) + 30)
        forecast = np.polyval(coeffs, future_x)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=list(x), y=list(vals.values), mode='lines+markers',
                                 name='Historical', line=dict(color='#2563eb')))
        fig.add_trace(go.Scatter(x=list(future_x), y=list(forecast), mode='lines',
                                 name='30-Day Forecast', line=dict(color='#f59e0b', dash='dash')))
        fig.add_trace(go.Scatter(x=list(future_x), y=list(forecast * 1.1), mode='lines',
                                 name='Upper Bound', line=dict(color='#f59e0b', width=0), showlegend=False))
        fig.add_trace(go.Scatter(x=list(future_x), y=list(forecast * 0.9), mode='lines',
                                 fill='tonexty', fillcolor='rgba(245,158,11,0.1)',
                                 name='Lower Bound', line=dict(color='#f59e0b', width=0), showlegend=False))
        fig.update_layout(template='plotly_white', margin=dict(l=10, r=10, t=10, b=10),
                          height=260, hovermode='x unified')
        charts["forecast_trend"] = fig.to_dict()
    except Exception:
        pass
    if len(numeric_cols) >= 2 and len(vals) >= 5:
        try:
            corr_df = df[numeric_cols[:6] + [target]].select_dtypes(include=["number"]).corr()
            fig2 = go.Figure(data=go.Heatmap(z=corr_df.values, x=corr_df.columns, y=corr_df.columns,
                                             colorscale='RdBu', zmin=-1, zmax=1))
            fig2.update_layout(template='plotly_white', margin=dict(l=10, r=10, t=10, b=10),
                               height=240, width=240)
            charts["correlation"] = fig2.to_dict()
        except Exception:
            pass
    return charts
