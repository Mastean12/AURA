import io
import logging

import pandas as pd

from app.services.report_engine import ReportPDF
from app.services.executive_report_framework import build_executive_report
from app.services.predictive_phase2_service import run_phase2_predictive
from app.database.database import get_session_factory
from app.models.document import Document
from sqlalchemy import select

logger = logging.getLogger(__name__)


async def generate_board_report(doc_ids: list[int], org_name: str = "",
                                org_logo_url: str = "", org_color: str = "",
                                workspace: str = "") -> bytes:
    if not doc_ids:
        return ReportPDF("No Data", "Board Report", org_name)

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
    target = ""
    if df is not None and len(df.columns) >= 2:
        try:
            result = await run_phase2_predictive(primary)
        except Exception as e:
            logger.warning("Phase2 predictive failed: %s", e)

    tech = result.get("technical", {})
    target = tech.get("target", df.columns[-1] if df is not None and len(df.columns) > 0 else "")

    try:
        color_hex = org_color.lstrip("#")
        accent = tuple(int(color_hex[i:i+2], 16) for i in (0, 2, 4))
    except Exception:
        accent = (37, 99, 235)

    pdf = ReportPDF(doc_title, "Board Report", org_name, org_logo_url, accent)
    pdf.alias_nb_pages()
    pdf = build_executive_report(pdf, result, df, target, "board_report", doc_ids, workspace)
    pdf.close()
    return pdf
