import io
import logging
from datetime import datetime

import pandas as pd

from app.database.database import get_session_factory
from app.models.document import Document
from app.services.analytics_service import get_analytics
from app.services.health_service import get_dataset_health
from app.services.kpi_detection_service import discover_kpis
from app.services.data_quality_service import run_data_quality_audit
from app.services.dataset_intelligence_service import analyze_dataset
from app.services.business_analytics_service import compute_descriptive_stats, compute_correlations
from app.services.report_engine import ReportPDF
from sqlalchemy import select

logger = logging.getLogger(__name__)


async def generate_analytics_export(doc_id: int) -> bytes:
    pdf = ReportPDF(f"Analytics Export #{doc_id}", "Analytics Export")
    pdf.alias_nb_pages()
    pdf.cover_page(subtitle="Dataset Analytics Export", confidentiality="Internal Use")

    # Fetch data
    df = None
    try:
        async with get_session_factory()() as db:
            r = await db.execute(select(Document).where(Document.id == doc_id))
            doc = r.scalar_one_or_none()
            if doc and doc.content and doc.content.count(",") > 5:
                df = pd.read_csv(io.StringIO(doc.content))
    except Exception:
        doc = None

    analytics = None
    health = None
    kpis = []
    dq = None
    ds = None
    stats = None
    correlations = None

    if doc:
        try:
            analytics = await get_analytics(doc_id)
        except Exception:
            pass
        try:
            health = await get_dataset_health(doc_id)
        except Exception:
            pass
        try:
            kpis = await discover_kpis(doc_id)
        except Exception:
            pass
        if df is not None:
            try:
                dq = run_data_quality_audit(df)
            except Exception:
                pass
            try:
                ds = analyze_dataset(df)
            except Exception:
                pass
            try:
                stats = compute_descriptive_stats(df)
            except Exception:
                pass
            try:
                correlations = compute_correlations(df)
            except Exception:
                pass

    # ── Dataset Overview ──
    pdf.section_header("Dataset Overview")
    if analytics:
        pdf.kv_row("Rows", str(analytics.row_count))
        pdf.kv_row("Columns", str(analytics.column_count))
        pdf.kv_row("Dataset Type", ds.get("dataset_type", "N/A") if ds else "N/A")
        pdf.kv_row("Target Variable", ds.get("target_variable", "N/A") if ds else "N/A")
    pdf.space()

    # ── Data Quality Report ──
    if dq:
        pdf.section_header("Data Quality Report")
        pdf.kv_row("Overall Score", f"{dq['overall_score']}/100 ({dq['grade']})")
        pdf.kv_row("Completeness", f"{dq['completeness']}%")
        pdf.kv_row("Uniqueness", f"{dq['uniqueness']}%")
        pdf.kv_row("Consistency", f"{dq['consistency']}%")
        pdf.kv_row("Validity", f"{dq['validity']}%")
        pdf.kv_row("Integrity", f"{dq['integrity']}%")
        if dq.get("issues"):
            pdf.space()
            pdf.body_bold(f"Data Issues ({dq['issues_count']} found)")
            for issue in dq["issues"][:10]:
                i_type = issue.get("type", "issue")
                i_col = issue.get("column", "")
                pdf.bullet([f"{i_type}: {i_col}" if i_col else i_type])
        pdf.space()

    # ── Column Statistics ──
    if analytics and analytics.columns:
        pdf.section_header("Column Statistics")
        pdf.table_header(["Column", "Type", "Missing", "Total", "Mean", "Unique"], [50, 20, 18, 16, 28, 20])
        for col in analytics.columns[:20]:
            dtype = col.dtype[:12]
            missing = f"{col.missing}/{col.total}"
            mean = str(col.numeric.get("mean", "N/A")[:10]) if col.numeric else "—"
            unique = str(col.categorical.get("unique", "—")) if col.categorical else "—"
            pdf.table_row([col.name[:40], dtype, missing, str(col.total), mean, unique],
                          [50, 20, 18, 16, 28, 20], alt=(analytics.columns.index(col) % 2 == 0))
        pdf.space()

    # ── Descriptive Stats ──
    if stats and stats.get("stats"):
        pdf.section_header("Descriptive Statistics")
        numeric_cols = list(stats["stats"].keys())[:8]
        pdf.table_header(["Metric", "Mean", "Median", "Std", "Min", "Max", "Skew"], [40, 22, 22, 22, 22, 22, 22])
        for col in numeric_cols:
            s = stats["stats"][col]
            pdf.table_row([
                col[:35], str(s.get("mean", "")), str(s.get("median", "")),
                str(s.get("std", "")), str(s.get("min", "")), str(s.get("max", "")),
                str(s.get("skewness", ""))
            ], [40, 22, 22, 22, 22, 22, 22], alt=(numeric_cols.index(col) % 2 == 0))
        pdf.space()

    # ── KPI Summary ──
    if kpis:
        pdf.section_header("KPI Summary")
        for kpi in kpis[:10]:
            pdf.kv_row(kpi.get("label", ""), f"{kpi.get('value', '')} ({kpi.get('category', '')})")
        pdf.space()

    # ── Correlation ──
    if correlations and correlations.get("strong_correlations"):
        pdf.section_header("Strong Correlations")
        for c in correlations["strong_correlations"][:8]:
            pdf.bullet([f"{c['col_a']} vs {c['col_b']}: {c['correlation']} ({c['direction']}, {c['strength']})"])
        pdf.space()

    # ── Classifications ──
    if ds and ds.get("columns"):
        pdf.section_header("Column Classifications")
        by_type: dict[str, list[str]] = {}
        for c in ds["columns"]:
            cls = c.get("classification", "unknown")
            by_type.setdefault(cls, []).append(c["name"])
        for cls, cols in sorted(by_type.items()):
            if cols:
                pdf.kv_row(cls.title(), ", ".join(cols[:8]))
        pdf.space()

    pdf.kv_row("Report Generated", datetime.now().strftime('%B %d, %Y at %H:%M'))
    pdf.body("Prepared by: AURA Executive Intelligence Platform")
    pdf.close()
    return pdf
