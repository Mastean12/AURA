import logging

import pandas as pd

from app.services.analytics_service import _parse_tabular, get_analytics

logger = logging.getLogger(__name__)


def _score_to_color(score: int) -> str:
    if score >= 80:
        return "green"
    elif score >= 50:
        return "yellow"
    return "red"


def _score_to_label(score: int) -> str:
    if score >= 80:
        return "Excellent"
    elif score >= 50:
        return "Moderate"
    return "Poor"


def _explain(completeness: int, quality: int, consistency: int, missing: int, overall: int) -> str:
    parts = []
    if overall >= 80:
        parts.append("Dataset quality is high with minimal missing data and no major structural issues.")
    elif overall >= 50:
        parts.append("Dataset has moderate quality issues that should be reviewed.")
    else:
        parts.append("Dataset requires significant cleaning before reliable analysis.")
    if missing < 60:
        parts.append(f"Missing data score ({missing}/100) indicates gaps that may affect analysis.")
    if consistency < 60:
        parts.append("Data consistency issues detected — check for duplicate rows or mixed types.")
    return " ".join(parts)


def _calculate_health(df: pd.DataFrame) -> dict:
    total_cells = len(df) * len(df.columns)
    missing_cells = int(df.isna().sum().sum())
    completeness = round((1 - missing_cells / total_cells) * 100) if total_cells > 0 else 100

    dupes = int(df.duplicated().sum())
    dup_pct = dupes / len(df) if len(df) > 0 else 0
    quality = round(max(0, 100 - dup_pct * 100 - (missing_cells / total_cells) * 50))

    empty_cols = sum(1 for c in df.columns if df[c].dropna().empty)
    consistency = round(max(0, 100 - empty_cols * 20 - dup_pct * 50))

    missing_score = round(max(0, 100 - (missing_cells / total_cells) * 100))

    overall = round((completeness + quality + consistency + missing_score) / 4)

    return {
        "completeness": completeness,
        "quality": quality,
        "consistency": consistency,
        "missing_data": missing_score,
        "overall": overall,
        "color": _score_to_color(overall),
        "label": _score_to_label(overall),
        "explanation": _explain(completeness, quality, consistency, missing_score, overall),
    }


async def get_dataset_health(doc_id: int) -> dict:
    try:
        analytics = await get_analytics(doc_id)
    except Exception as e:
        logger.warning("Analytics unavailable: %s", e)
        return {
            "completeness": 0, "quality": 0, "consistency": 0,
            "missing_data": 0, "overall": 0, "color": "red",
            "label": "Unavailable", "explanation": "Could not analyze dataset health.",
        }

    try:
        from app.database.database import get_session_factory
        from app.models.document import Document
        from sqlalchemy import select
        import asyncio

        async def _fetch():
            async with get_session_factory()() as db:
                result = await db.execute(select(Document).where(Document.id == doc_id))
                return result.scalar_one_or_none()

        doc = await _fetch()
    except Exception:
        doc = None

    if not doc or not doc.content:
        return {
            "completeness": 0, "quality": 0, "consistency": 0,
            "missing_data": 0, "overall": 0, "color": "red",
            "label": "No Data", "explanation": "No dataset content found.",
        }

    df = _parse_tabular(doc.content)
    if df is None:
        return {
            "completeness": 0, "quality": 0, "consistency": 0,
            "missing_data": 0, "overall": 0, "color": "red",
            "label": "Non-tabular", "explanation": "Dataset is not tabular; health scoring requires structured data.",
        }

    return _calculate_health(df)
