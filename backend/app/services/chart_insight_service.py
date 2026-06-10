import io
import json
import logging

import pandas as pd

from app.services.ai_service import generate_response
from app.database.database import get_session_factory
from app.models.document import Document
from sqlalchemy import select

logger = logging.getLogger(__name__)


def _chart_data_summary(df: pd.DataFrame, col: str, chart_type: str) -> str:
    clean = df[col].dropna()
    info = [f"Chart type: {chart_type}", f"Column: {col}", f"Data points: {len(clean)}"]

    if pd.api.types.is_numeric_dtype(clean):
        info.append(f"Range: [{clean.min():.2f}, {clean.max():.2f}]")
        info.append(f"Mean: {clean.mean():.2f}")
        info.append(f"Median: {clean.median():.2f}")
        if len(clean) > 1:
            info.append(f"Std dev: {clean.std():.2f}")
        if len(clean) >= 3:
            recent = clean.tail(3).tolist()
            info.append(f"Last 3 values: {recent}")
            earlier = clean.head(3).mean()
            info.append(f"First 3 mean: {earlier:.2f}")
    else:
        counts = clean.value_counts().head(10)
        info.append(f"Top categories: {dict(counts)}")

    return "\n".join(info)


def _build_chart_insight_prompt(summary: str) -> str:
    return f"""You are an AI business analyst. Analyze this chart data and provide a business insight.

Return ONLY valid JSON:
{{
  "insight": "A 2-3 sentence analysis covering: what happened, why it likely happened, and recommended action."
}}

Chart data:
{summary}
"""


async def generate_chart_insight(doc_id: int, chart_type: str, column: str) -> str:
    logger.info("Generating chart insight for doc_id=%d, column=%s", doc_id, column)
    try:
        async with get_session_factory()() as db:
            result = await db.execute(select(Document).where(Document.id == doc_id))
            doc = result.scalar_one_or_none()
    except Exception as e:
        logger.warning("DB error: %s", e)
        return "Chart insight temporarily unavailable."

    if not doc or not doc.content:
        return "Document not found."

    df = pd.read_csv(io.StringIO(doc.content)) if doc.content.count(",") > 5 else None
    if df is None or column not in df.columns:
        return "Could not parse chart data."

    summary = _chart_data_summary(df, column, chart_type)
    prompt = _build_chart_insight_prompt(summary)

    try:
        raw = generate_response(prompt)
        raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        result = json.loads(raw)
        return result.get("insight", "Chart insight temporarily unavailable.")
    except Exception as e:
        logger.warning("Chart insight generation failed: %s", e)
        return "Chart insight temporarily unavailable. Please try again shortly."
