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
    from app.services.dataset_intelligence_service import analyze_dataset
    from app.services.data_quality_service import run_data_quality_audit
    from app.services.business_analytics_service import run_business_analytics, compute_descriptive_stats
    from app.services.forecast_intelligence_service import check_forecast_eligibility

    ds = analyze_dataset(df)
    dq = run_data_quality_audit(df)
    ba = run_business_analytics(df)

    lines = [
        f"Dataset: {ds['row_count']} rows x {ds['column_count']} columns",
        f"Type: {ds['dataset_type']}",
        f"Target: {ds['target_variable'] or 'None detected'}",
        f"Data Quality Score: {dq['overall_score']}/100 ({dq['grade']})",
        f"KPIs: {', '.join(ds['kpi_columns'][:5]) or 'None'}",
    ]

    if dq.get("issues"):
        top_issues = dq["issues"][:3]
        lines.append(f"Data Issues: {'; '.join(i['type'] + ' in ' + (i.get('column','') or '') for i in top_issues)}")

    if ba.get("business_questions"):
        lines.append(f"Key Questions: {' | '.join(ba['business_questions'][:3])}")

    if ba.get("correlations", {}).get("strong_correlations"):
        strong = ba["correlations"]["strong_correlations"][:3]
        for s in strong:
            lines.append(f"  Correlation: {s['col_a']} vs {s['col_b']} = {s['correlation']} ({s['direction']})")

    cols_summary = []
    for col_info in ds.get("columns", [])[:15]:
        cls = col_info.get("classification", "")
        if cls == "identifier":
            continue
        cols_summary.append(f"  {col_info['name']} ({cls})")

    lines.append("Key Columns:")
    lines.extend(cols_summary[:10])

    return "\n".join(lines)


def _build_insights_prompt(df_summary: str) -> str:
    return f"""You are an AI Senior Business Intelligence Analyst and Executive Advisor. Based on the dataset analysis below, generate strategic business insights.

Return ONLY valid JSON:
{{
  "executive_summary": "2-3 sentence executive overview covering what happened, why it matters, and what leadership should know.",
  "key_findings": ["Finding 1 with specific numbers", "Finding 2 with business impact", "Finding 3"],
  "risks": ["Risk 1 with business consequence", "Risk 2"],
  "opportunities": ["Opportunity 1 with expected benefit", "Opportunity 2"],
  "recommendations": ["Specific actionable recommendation 1", "Recommendation 2"],
  "confidence_score": 85
}}

Dataset Analysis:
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
