import json
import logging
import time

import pandas as pd

from app.services.ai_service import generate_response_async
from app.database.database import get_session_factory
from app.models.document import Document
from app.services.cache_service import compute_doc_hash, get_cached, set_cached
from sqlalchemy import select

logger = logging.getLogger(__name__)


def _df_to_summary(df: pd.DataFrame) -> str:
    info = [f"Rows: {len(df)}, Columns: {len(df.columns)}"]
    for col in df.columns:
        dtype = "numeric" if pd.api.types.is_numeric_dtype(df[col]) else "categorical"
        missing = int(df[col].isna().sum())
        info.append(f"  {col} ({dtype}) missing={missing}/{len(df)}")
        if pd.api.types.is_numeric_dtype(df[col]):
            clean = df[col].dropna()
            if len(clean) > 0:
                info.append(f"    range=[{clean.min()}, {clean.max()}], mean={clean.mean():.2f}")
        else:
            tops = df[col].dropna().value_counts().head(5)
            info.append(f"    top: {dict(tops)}")
    return "\n".join(info)


def _build_insights_prompt(df_summary: str) -> str:
    return f"""You are an AI business analyst. Analyze this dataset and return ONLY valid JSON:

{{
  "executive_summary": "2-3 sentence executive overview",
  "key_findings": ["finding 1", "finding 2", "finding 3"],
  "risks": ["risk 1", "risk 2"],
  "opportunities": ["opportunity 1", "opportunity 2"],
  "recommendations": ["recommendation 1", "recommendation 2"],
  "confidence_score": 85
}}

Dataset analysis:
{df_summary}
"""


def _build_executive_summary_prompt(df_summary: str) -> str:
    return f"""You are an AI executive analyst. Analyze this dataset and return ONLY valid JSON with a concise executive summary.

{{
  "summary": "2-3 sentence executive summary covering key business implications.",
  "confidence": 0.91
}}

Dataset analysis:
{df_summary}
"""


async def _get_doc(doc_id: int) -> tuple:
    try:
        async with get_session_factory()() as db:
            result = await db.execute(select(Document).where(Document.id == doc_id))
            doc = result.scalar_one_or_none()
            if doc:
                return doc.id, doc.content
    except Exception as e:
        logger.warning("DB error: %s", e)
    return doc_id, None


async def _get_df(content: str):
    if not content or content.count(",") <= 5:
        return None
    df = pd.read_csv(pd.io.common.StringIO(content))
    return df if len(df.columns) >= 2 else None


async def generate_insights(doc_id: int) -> dict:
    real_id, content = await _get_doc(doc_id)
    doc_hash = compute_doc_hash(content or "")

    cached = await get_cached(real_id, doc_hash, "insights")
    if cached:
        logger.info("Cache hit: insights for doc_id=%d", real_id)
        return cached

    logger.info("Generating insights for doc_id=%d", real_id)
    if not content:
        return {"executive_summary": "Document not found.", "key_findings": [], "risks": [],
                "opportunities": [], "recommendations": [], "confidence_score": 0}

    df = await _get_df(content)
    if df is None:
        return {"executive_summary": "Dataset could not be parsed.", "key_findings": [], "risks": [],
                "opportunities": [], "recommendations": [], "confidence_score": 0}

    df_summary = _df_to_summary(df)
    prompt = _build_insights_prompt(df_summary)

    try:
        raw = await generate_response_async(prompt, request_type="insights")
        raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        result = json.loads(raw)
    except Exception as e:
        logger.warning("Insights generation failed: %s", e)
        result = {"executive_summary": "Could not generate AI insights.", "key_findings": [], "risks": [],
                  "opportunities": [], "recommendations": [], "confidence_score": 0}

    result.setdefault("executive_summary", "")
    result.setdefault("key_findings", [])
    result.setdefault("risks", [])
    result.setdefault("opportunities", [])
    result.setdefault("recommendations", [])
    result.setdefault("confidence_score", 0)

    await set_cached(real_id, doc_hash, "insights", result)
    return result


async def generate_executive_summary(doc_id: int) -> dict:
    real_id, content = await _get_doc(doc_id)
    doc_hash = compute_doc_hash(content or "")

    cached = await get_cached(real_id, doc_hash, "executive_summary")
    if cached:
        logger.info("Cache hit: executive_summary for doc_id=%d", real_id)
        return cached

    logger.info("Generating executive summary for doc_id=%d", real_id)
    if not content:
        return {"summary": "Document not found.", "confidence": 0.0}

    df = await _get_df(content)
    if df is None:
        return {"summary": "Dataset could not be parsed as tabular data.", "confidence": 0.0}

    df_summary = _df_to_summary(df)
    prompt = _build_executive_summary_prompt(df_summary)

    try:
        raw = await generate_response_async(prompt, request_type="executive_summary")
        raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        result = json.loads(raw)
    except Exception as e:
        logger.warning("Executive summary generation failed: %s", e)
        result = {"summary": "AI analysis temporarily unavailable. Please try again shortly.", "confidence": 0.0}

    result.setdefault("summary", "")
    result.setdefault("confidence", 0.0)

    await set_cached(real_id, doc_hash, "executive_summary", result)
    return result


async def clear_cache(doc_id: int | None = None):
    from app.services.cache_service import invalidate_cache
    try:
        await invalidate_cache(doc_id)
    except Exception as e:
        logger.warning("Cache clear failed: %s", e)
