import io
import json
import logging
import re

import pandas as pd

from app.database.database import get_session_factory
from app.models.document import Document
from app.services.ai_service import generate_response_async
from app.services.kpi_detection_service import KPI_PATTERNS as BASE_KPI_PATTERNS, _infer_format, _normalize
from sqlalchemy import select

logger = logging.getLogger(__name__)

INDUSTRY_PATTERNS: dict[str, dict] = {
    "Finance": {
        "keywords": ["revenue", "expense", "profit", "margin", "cash_flow", "income", "roi", "ebitda"],
        "kpis": ["Revenue", "Expenses", "Profit Margin", "Cash Flow", "Growth Rate"],
    },
    "Sales": {
        "keywords": ["sales", "customer", "conversion", "lead", "pipeline", "deal", "quota"],
        "kpis": ["Revenue", "Conversion Rate", "Pipeline Value", "Customer Growth", "Forecast"],
    },
    "HR": {
        "keywords": ["employee", "hiring", "retention", "turnover", "salary", "compensation", "headcount"],
        "kpis": ["Employee Count", "Retention", "Turnover", "Hiring Trends", "Compensation"],
    },
    "Operations": {
        "keywords": ["inventory", "delivery", "efficiency", "productivity", "utilization", "supply_chain"],
        "kpis": ["Efficiency", "Delivery Time", "Productivity", "Resource Utilization"],
    },
    "NGO & Development": {
        "keywords": ["beneficiary", "funding", "grant", "impact", "program", "donation", "outreach"],
        "kpis": ["Beneficiaries", "Funding Utilization", "Project Impact", "Program Performance"],
    },
}


def _detect_industry(df: pd.DataFrame) -> str:
    scores: dict[str, int] = {}
    for industry, config in INDUSTRY_PATTERNS.items():
        score = 0
        for col in df.columns:
            norm = _normalize(col)
            for kw in config["keywords"]:
                if kw in norm:
                    score += 1
        scores[industry] = score
    if max(scores.values()) == 0:
        return "General Business"
    return max(scores, key=scores.get)


def _generate_industry_kpis(df: pd.DataFrame, industry: str) -> list[dict]:
    discovered = []
    matched_columns: set[str] = set()
    base_patterns = BASE_KPI_PATTERNS.get(industry, {})
    if isinstance(base_patterns, dict):
        base_patterns = []
    for pattern in (base_patterns or []):
        for col in df.columns:
            norm = _normalize(col)
            if any(kw in norm for kw in pattern["keywords"]):
                if col not in matched_columns:
                    matched_columns.add(col)
                    col_data = df[col].dropna()
                    if len(col_data) > 0 and pd.api.types.is_numeric_dtype(col_data):
                        latest = col_data.iloc[-1]
                        discovered.append({
                            "label": pattern["label"],
                            "column": col,
                            "value": _infer_format(float(latest), pattern["format"]),
                            "raw_value": float(latest),
                        })
                break

    if not discovered:
        numeric_cols = df.select_dtypes(include=["number"]).columns[:5]
        for col in numeric_cols:
            col_data = df[col].dropna()
            if len(col_data) > 0 and col not in matched_columns:
                discovered.append({
                    "label": col.replace("_", " ").title(),
                    "column": col,
                    "value": str(round(float(col_data.iloc[-1]), 2)),
                    "raw_value": float(col_data.iloc[-1]),
                })

    return discovered[:8]


async def generate_industry_dashboard(doc_id: int) -> dict:
    logger.info("Generating industry dashboard for doc_id=%d", doc_id)
    try:
        async with get_session_factory()() as db:
            result = await db.execute(select(Document).where(Document.id == doc_id))
            doc = result.scalar_one_or_none()
    except Exception as e:
        logger.warning("DB error: %s", e)
        return {"detected_industry": "Unknown", "industry_kpis": [], "industry_summary": "", "recommendations": [], "confidence": 0}

    if not doc or not doc.content:
        return {"detected_industry": "Unknown", "industry_kpis": [], "industry_summary": "", "recommendations": [], "confidence": 0}

    df = pd.read_csv(io.StringIO(doc.content)) if doc.content.count(",") > 5 else None
    if df is None or len(df.columns) < 2:
        return {"detected_industry": "Unknown", "industry_kpis": [], "industry_summary": "", "recommendations": [], "confidence": 0}

    industry = _detect_industry(df)
    kpis = _generate_industry_kpis(df, industry)

    summary_prompt = (
        f"This dataset has been classified as '{industry}' industry. "
        f"Columns: {', '.join(df.columns[:10])}. "
        f"Rows: {len(df)}. "
        "Provide a 2-sentence executive summary focusing on industry-specific observations."
    )
    rec_prompt = (
        f"For a {industry} organization with this data, provide 3 specific strategic recommendations "
        "as a JSON array of strings. Return ONLY the JSON array."
    )

    summary = ""
    recommendations: list[str] = []
    try:
        summary = await generate_response_async(summary_prompt, request_type="industry_intelligence")
    except Exception:
        summary = f"Industry analysis for {industry} organization based on {len(df.columns)} data dimensions."

    try:
        raw = await generate_response_async(rec_prompt, request_type="industry_intelligence")
        raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        recommendations = json.loads(raw) if raw.startswith("[") else []
    except Exception:
        recommendations = [f"Optimize {industry} KPIs for better performance.", "Identify growth opportunities in key metrics."]

    return {
        "detected_industry": industry,
        "industry_kpis": kpis,
        "industry_summary": summary,
        "recommendations": recommendations[:5],
        "confidence": round(0.7 + (len(kpis) / 20), 2),
    }
