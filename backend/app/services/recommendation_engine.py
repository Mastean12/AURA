import io
import json
import logging

import pandas as pd

from app.database.database import get_session_factory
from app.models.document import Document
from app.services.ai_service import generate_response
from app.services.analytics_service import get_analytics
from app.services.insights_service import generate_insights
from app.services.risk_scoring_service import calculate_risk_score
from sqlalchemy import select

logger = logging.getLogger(__name__)

CATEGORIES = [
    "Revenue Growth",
    "Cost Optimization",
    "Operational Efficiency",
    "Risk Reduction",
    "Strategic Opportunities",
]


def _df_summary_for_prompt(df: pd.DataFrame) -> str:
    info = [f"Dataset has {len(df)} rows, {len(df.columns)} columns."]
    for col in df.columns:
        dtype = "numeric" if pd.api.types.is_numeric_dtype(df[col]) else "categorical"
        missing = int(df[col].isna().sum())
        info.append(f"  {col} ({dtype}, {missing} missing)")
        if pd.api.types.is_numeric_dtype(df[col]):
            clean = df[col].dropna()
            if len(clean) > 0:
                recent = clean.tail(3).mean()
                overall_mean = clean.mean()
                info.append(f"    recent_avg={recent:.2f}, overall_avg={overall_mean:.2f}")
    return "\n".join(info)


def _build_recommendation_prompt(df_summary: str, insights_text: str, risk_text: str) -> str:
    return f"""You are an AI business strategist. Based on the dataset analysis below, generate actionable business recommendations.

Return ONLY valid JSON:
{{
  "recommendations": [
    {{
      "title": "Short action title",
      "description": "Detailed recommendation description",
      "category": "Revenue Growth | Cost Optimization | Operational Efficiency | Risk Reduction | Strategic Opportunities",
      "impact": "high | medium | low",
      "urgency": "high | medium | low",
      "confidence": 0.85,
      "source": "data analysis"
    }}
  ]
}}

Generate 4-7 diverse recommendations spanning different categories.

Dataset Analysis:
{df_summary}

Key Insights:
{insights_text}

Risk Assessment:
{risk_text}
"""


async def generate_recommendations(doc_id: int) -> list[dict]:
    logger.info("Generating recommendations for doc_id=%d", doc_id)
    try:
        async with get_session_factory()() as db:
            result = await db.execute(select(Document).where(Document.id == doc_id))
            doc = result.scalar_one_or_none()
    except Exception as e:
        logger.warning("DB error: %s", e)
        return []

    if not doc or not doc.content:
        return []

    df = pd.read_csv(io.StringIO(doc.content)) if doc.content.count(",") > 5 else None
    if df is None or len(df.columns) < 2:
        return []

    df_summary = _df_summary_for_prompt(df)

    insights_text = ""
    try:
        insights = await generate_insights(doc_id)
        if insights:
            parts = []
            if insights.get("key_findings"):
                parts.append("Findings: " + "; ".join(insights["key_findings"][:3]))
            if insights.get("risks"):
                parts.append("Risks: " + "; ".join(insights["risks"][:3]))
            if insights.get("opportunities"):
                parts.append("Opportunities: " + "; ".join(insights["opportunities"][:3]))
            insights_text = " | ".join(parts)
    except Exception as e:
        logger.warning("Insights fetch failed: %s", e)

    risk_text = ""
    try:
        risk = await calculate_risk_score(doc_id)
        if risk:
            cats = risk.get("categories", [])
            parts = [f"{c['name']}: {c['score']}/100" for c in cats]
            risk_text = ", ".join(parts)
    except Exception as e:
        logger.warning("Risk fetch failed: %s", e)

    prompt = _build_recommendation_prompt(df_summary, insights_text, risk_text)

    try:
        raw = generate_response(prompt)
        raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        result = json.loads(raw)
        recommendations = result.get("recommendations", [])
    except Exception as e:
        logger.warning("Recommendation generation failed: %s", e)
        recommendations = _fallback_recommendations(df)

    validated = []
    for rec in recommendations:
        if rec.get("category") not in CATEGORIES:
            rec["category"] = "Strategic Opportunities"
        validated.append({
            "title": rec.get("title", "Action item"),
            "description": rec.get("description", ""),
            "category": rec.get("category"),
            "impact": rec.get("impact", "medium"),
            "urgency": rec.get("urgency", "medium"),
            "confidence": min(max(float(rec.get("confidence", 0.5)), 0), 1),
            "source": rec.get("source", "data analysis"),
        })

    return validated


def _fallback_recommendations(df: pd.DataFrame) -> list[dict]:
    recs = []
    numeric_cols = df.select_dtypes(include=["number"]).columns[:3]

    for col in numeric_cols:
        values = df[col].dropna().values.astype(float)
        if len(values) < 3:
            continue
        recent = values[-3:].mean()
        earlier = values[:3].mean()
        if earlier > 0 and recent < earlier * 0.9:
            recs.append({
                "title": f"Investigate {col} decline",
                "description": f"{col} has decreased approximately {((earlier - recent) / earlier) * 100:.0f}%. Review underlying causes.",
                "category": "Risk Reduction",
                "impact": "high",
                "urgency": "high",
                "confidence": 0.75,
                "source": "trend analysis",
            })

    if not recs:
        recs.append({
            "title": "Explore dataset insights",
            "description": "Upload more data or configure AI analysis to generate specific recommendations.",
            "category": "Strategic Opportunities",
            "impact": "medium",
            "urgency": "low",
            "confidence": 0.5,
            "source": "data analysis",
        })

    return recs
