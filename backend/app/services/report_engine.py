import json
import logging
import tempfile
from datetime import datetime
from pathlib import Path

import plotly.graph_objects as go
from fpdf import FPDF

logger = logging.getLogger(__name__)

BLUE = (37, 99, 235)
DARK = (20, 30, 50)
MID = (60, 60, 60)
LIGHT = (120, 120, 120)
WHITE = (255, 255, 255)
BG_LIGHT = (245, 247, 250)


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
    def __init__(self, title: str, report_type: str = "Report"):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=20)
        self._title = title
        self._type = report_type
        self._report_id = f"AURA-{report_type[:2].upper()}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    def header(self):
        if self.page_no() > 1:
            self.set_font("Helvetica", "", 7)
            self.set_text_color(*LIGHT)
            self.cell(0, 6, f"AURA {self._type} | {self._title[:40]}", new_x="LMARGIN", new_y="NEXT")
            self.set_draw_color(220, 220, 220)
            self.line(10, self.get_y(), self.w - 10, self.get_y())
            self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*LIGHT)
        self.cell(0, 10, f"Confidential | {self._report_id} | Page {self.page_no()}/{{nb}}", align="C")

    def cover_page(self, subtitle: str = "", note: str = "Confidential"):
        self.add_page()
        self.ln(35)
        self.set_fill_color(*DARK)
        self.rect(0, 0, self.w, 80, "F")
        self.set_y(20)
        self.set_font("Helvetica", "B", 32)
        self.set_text_color(*WHITE)
        self.cell(0, 18, self._type, align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(4)
        self.set_font("Helvetica", "", 18)
        self.set_text_color(147, 197, 253)
        self.cell(0, 12, self._title, align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(30)

        if subtitle:
            self.set_font("Helvetica", "", 11)
            self.set_text_color(*MID)
            self.cell(0, 8, subtitle, align="C", new_x="LMARGIN", new_y="NEXT")

        self.ln(8)
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*LIGHT)
        self.cell(0, 7, f"Prepared: {datetime.now().strftime('%B %d, %Y')}", align="C", new_x="LMARGIN", new_y="NEXT")
        self.cell(0, 7, note, align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(25)

        self.set_draw_color(*BLUE)
        self.set_line_width(0.5)
        mid = self.w / 2
        self.line(mid - 25, self.get_y(), mid + 25, self.get_y())

    def section(self, num: str, title: str):
        self.add_page()
        self.set_font("Helvetica", "B", 20)
        self.set_text_color(*DARK)
        label = f"{num}  {title}" if num else title
        self.cell(0, 14, label, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(*BLUE)
        self.set_line_width(0.4)
        self.line(10, self.get_y(), self.w - 10, self.get_y())
        self.ln(5)

    def body(self, text: str):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*MID)
        self.multi_cell(0, 5.5, str(text))
        self.ln(1)

    def bullet(self, items: list[str]):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*MID)
        for item in items:
            self.cell(5)
            self.cell(0, 6, f"- {item}", new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def kv_row(self, key: str, value: str):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(*LIGHT)
        self.cell(50, 6, key)
        self.set_text_color(*MID)
        self.cell(0, 6, value, new_x="LMARGIN", new_y="NEXT")

    def metric_card(self, label: str, value: str, x: float, y: float, w: float = 45, h: float = 22):
        self.set_xy(x, y)
        self.set_fill_color(*BG_LIGHT)
        self.rect(x, y, w, h, "F")
        self.set_xy(x + 3, y + 3)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*LIGHT)
        self.cell(w - 6, 4, label)
        self.set_xy(x + 3, y + 10)
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(*DARK)
        self.cell(w - 6, 6, str(value))

    def risk_row(self, name: str, severity: str, prob: str, impact: str):
        colors = {"High": (220, 38, 38), "Medium": (245, 158, 11), "Low": (37, 99, 235)}
        c = colors.get(severity, MID)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*DARK)
        self.cell(50, 6, name[:30])
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*c)
        self.cell(16, 6, severity, align="C")
        self.set_text_color(*MID)
        self.cell(16, 6, prob, align="C")
        self.cell(0, 6, impact[:50], new_x="LMARGIN", new_y="NEXT")

    def opportunity_row(self, name: str, impact: str, priority: str, action: str):
        colors = {"High": (16, 185, 129), "Medium": (37, 99, 235), "Low": (245, 158, 11)}
        c = colors.get(impact, MID)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*DARK)
        self.cell(50, 6, name[:30])
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*c)
        self.cell(18, 6, impact, align="C")
        self.set_text_color(*MID)
        self.cell(16, 6, priority, align="C")
        self.cell(0, 6, action[:50], new_x="LMARGIN", new_y="NEXT")

    def rec_row(self, title: str, priority: str, benefit: str):
        colors = {"High": (220, 38, 38), "Medium": (245, 158, 11), "Low": (37, 99, 235)}
        c = colors.get(priority, MID)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*DARK)
        self.cell(50, 6, title[:35])
        self.set_font("Helvetica", "", 8)
        self.set_text_color(*c)
        self.cell(16, 6, priority, align="C")
        self.set_text_color(*MID)
        self.cell(0, 6, benefit[:55], new_x="LMARGIN", new_y="NEXT")

    def add_chart(self, chart_json: dict, width=480, height=260):
        img_path = make_chart_image(chart_json, width, height)
        if img_path:
            try:
                self.image(img_path, x=15, w=self.w - 30)
                self.ln(4)
            finally:
                Path(img_path).unlink(missing_ok=True)

    def table_header(self, cols: list[str], widths: list[int]):
        self.set_fill_color(*DARK)
        self.set_text_color(*WHITE)
        self.set_font("Helvetica", "B", 8)
        for i, col in enumerate(cols):
            self.cell(widths[i], 7, col, border=1, fill=True, align="C")
        self.ln()

    def table_row(self, cells: list[str], widths: list[int], bold: bool = False):
        self.set_font("Helvetica", "B" if bold else "", 8)
        self.set_text_color(*MID)
        fill = False
        for i, cell in enumerate(cells):
            self.cell(widths[i], 6, str(cell)[:25], border=1, align="C", fill=fill)
        self.ln()

    def close(self):
        self.ln(10)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*LIGHT)
        self.cell(0, 6, f"{self._title} | AURA Enterprise Intelligence | Confidential", align="C", new_x="LMARGIN", new_y="NEXT")
        return bytes(self.output())
