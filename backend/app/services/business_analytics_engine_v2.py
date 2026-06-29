import logging
import re
from typing import Any

import pandas as pd

from app.services.dataset_intelligence_service import analyze_dataset
from app.services.business_analytics_service import compute_descriptive_stats, compute_correlations
from app.services.kpi_detection_service import discover_kpis as _discover_kpis_raw

logger = logging.getLogger(__name__)

SKIP_PATTERNS = re.compile(
    r"(id$|_id$|uuid|email|phone|fax|password|token|secret|hash|url|link|address|name|title|headline|subject|content|text|body|description|comment|message|img|image|photo|picture|avatar|icon|thumbnail)", re.I
)


def _is_skip_column(name: str, classification: str = "") -> bool:
    if classification in ("identifier", "text"):
        return True
    return bool(SKIP_PATTERNS.search(name.strip()))


def _best_chart_type(col: str, classification: str, dtype: str, nunique: int, is_target: bool, is_time: bool) -> str:
    """Recommend the best chart type for a variable."""
    if is_time or classification == "date":
        return "line"
    if classification == "kpi" and nunique > 10:
        return "line"
    if classification in ("identifier", "text"):
        return None
    if classification == "geographic":
        return "bar"
    if dtype == "numeric":
        if nunique <= 10:
            return "bar"
        if nunique <= 30:
            return "histogram"
        return "histogram"
    if classification == "categorical":
        if nunique <= 2:
            return "metric"
        if nunique <= 10:
            return "pie"
        return "bar"
    return "bar"


async def get_business_analytics(doc_id: int) -> dict[str, Any]:
    """Run complete business analytics pipeline: KPI detection + chart recommendations."""
    from app.database.database import get_session_factory
    from app.models.document import Document
    from sqlalchemy import select

    try:
        async with get_session_factory()() as db:
            r = await db.execute(select(Document).where(Document.id == doc_id))
            doc = r.scalar_one_or_none()
    except Exception:
        doc = None
    if not doc or not doc.content:
        return {"error": "Document not found"}

    import io
    import numpy as np
    df = pd.read_csv(io.StringIO(doc.content), on_bad_lines="skip", engine="python") if doc.content.count(",") > 5 else None
    if df is None or len(df.columns) < 2:
        return {"error": "Dataset must be tabular"}

    # Clean currency columns: convert strings like "₹1,299" to float
    currency_pattern = re.compile(r"[₹$€£¥,\s]")
    for col in df.columns:
        if df[col].dtype == "object" or df[col].dtype == "str":
            try:
                cleaned = df[col].astype(str).str.replace(currency_pattern, "", regex=True).str.strip()
                numeric_vals = pd.to_numeric(cleaned, errors="coerce")
                if numeric_vals.notna().sum() >= 5:
                    df[col] = numeric_vals
            except Exception:
                pass

    ds = analyze_dataset(df)
    kpis = await _discover_kpis_raw(doc_id)
    stats = compute_descriptive_stats(df)
    correlations = compute_correlations(df)

    # KPI categories
    kpi_by_category: dict[str, list[dict]] = {"Revenue": [], "Profit": [], "Cost": [], "Growth": [], "Performance": []}
    for kpi in kpis:
        cat = kpi.get("category", "Performance")
        kpi_by_category.setdefault(cat, []).append(kpi)

    # Chart recommendations for each KPI column
    chart_recs = []
    seen_cols = set()
    for col_info in ds.get("columns", []):
        name = col_info["name"]
        cls = col_info.get("classification", "")
        if name in seen_cols or _is_skip_column(name, cls):
            continue
        seen_cols.add(name)
        dtype = col_info.get("dtype")
        nunique = col_info.get("nunique", 0)
        is_target = col_info.get("is_target", False)
        is_time = cls == "date" or name.lower() in ("date", "time", "timestamp", "year", "month", "quarter")
        chart = _best_chart_type(name, cls, dtype, nunique, is_target, is_time)
        if chart:
            chart_recs.append({
                "column": name,
                "classification": cls,
                "chart_type": chart,
                "nunique": nunique,
                "is_target": is_target,
                "business_reason": _business_reason(chart, cls, name),
            })

    # Trend analytics: find KPIs with trend data
    kpi_columns = ds.get("kpi_columns", [])
    numeric_cols = ds.get("numeric_columns", [])
    trend_cols = (kpi_columns or numeric_cols)[:5]

    trend_analysis = {}
    for col in trend_cols:
        try:
            vals = pd.to_numeric(df[col], errors='coerce').dropna().values.astype(float)
            if len(vals) >= 3:
                recent = vals[-3:].mean()
                earlier = vals[:3].mean()
                pct_change = ((recent - earlier) / earlier) * 100 if earlier else 0
                trend_analysis[col] = {
                    "current": round(float(vals[-1]), 2),
                    "average": round(float(vals.mean()), 2),
                    "change_pct": round(float(pct_change), 1),
                    "direction": "up" if pct_change > 2 else "down" if pct_change < -2 else "stable",
                }
        except Exception:
            pass

    # Comparative analysis: top vs bottom categorical segments for each KPI
    comparative = []
    cat_cols = ds.get("categorical_columns", [])[:3]
    for kpi_col in kpi_columns[:2]:
        for cat_col in cat_cols:
            if cat_col in df.columns and kpi_col in df.columns and df[cat_col].nunique() <= 10:
                grouped = df.groupby(cat_col)[kpi_col].agg(["mean", "sum", "count"]).round(2)
                if not grouped.empty:
                    comparative.append({
                        "kpi": kpi_col,
                        "segment": cat_col,
                        "top_segment": str(grouped["mean"].idxmax()) if "mean" in grouped else "",
                        "bottom_segment": str(grouped["mean"].idxmin()) if "mean" in grouped else "",
                        "top_value": float(grouped["mean"].max()) if "mean" in grouped else 0,
                        "bottom_value": float(grouped["mean"].min()) if "mean" in grouped else 0,
                    })

    # Generate actual Plotly charts for top recommendations
    from app.services.chart_service import _make_chart
    rendered_charts = []
    for rec in chart_recs[:6]:
        try:
            chart = _make_chart(df, rec["column"], rec["chart_type"], 280)
            rendered_charts.append({
                "column": rec["column"],
                "chart_type": rec["chart_type"],
                "classification": rec["classification"],
                "html": chart["html"],
                "business_reason": rec["business_reason"],
            })
        except Exception:
            pass

    return {
        "kpi_summary": {
            "total_detected": len(kpis),
            "by_category": {k: len(v) for k, v in kpi_by_category.items() if v},
            "kpis": kpis[:10],
        },
        "chart_recommendations": chart_recs[:12],
        "charts": rendered_charts,
        "trend_analysis": trend_analysis,
        "comparative_analysis": comparative[:6],
        "correlations": correlations.get("strong_correlations", [])[:8],
        "descriptive_stats": stats,
        "dataset_intelligence": ds,
    }


def _business_reason(chart_type: str, classification: str, name: str) -> str:
    reasons = {
        "line": "Track changes and trends over time",
        "bar": "Compare values across categories",
        "pie": "Show proportional distribution",
        "histogram": "Analyze value distribution and spread",
        "metric": "Display single KPI value as metric for quick reference",
    }
    return reasons.get(chart_type, f"Visualize {classification} data")
