import json
import logging

import pandas as pd

from app.services.ai_service import generate_response_async
from app.services.dataset_intelligence_service import analyze_dataset
from app.services.data_quality_service import run_data_quality_audit
from app.services.business_analytics_service import run_business_analytics, compute_descriptive_stats

logger = logging.getLogger(__name__)


def _df_summary_for_prompt(df: pd.DataFrame) -> str:
    ds = analyze_dataset(df)
    dq = run_data_quality_audit(df)
    stats = compute_descriptive_stats(df)

    lines = [
        f"Dataset: {ds['row_count']} rows x {ds['column_count']} columns",
        f"Type: {ds['dataset_type']}",
        f"Target: {ds['target_variable'] or 'None detected'}",
        f"Data Quality Score: {dq['overall_score']}/100 ({dq['grade']})",
        f"KPIs: {', '.join(ds['kpi_columns'][:5]) or 'None'}",
        f"Categories: {', '.join(ds['categorical_columns'][:5]) or 'None'}",
        f"Dates: {', '.join(ds['date_columns'][:3]) or 'None'}",
        "",
        "Columns:",
    ]
    for col in ds["columns"][:15]:
        lines.append(f"  {col['name']} ({col['classification']}, {col['dtype']})")
    if stats:
        numeric = list(stats.get("stats", {}).keys())[:5]
        for col in numeric:
            s = stats["stats"][col]
            lines.append(f"  {col}: mean={s['mean']}, median={s['median']}, range=[{s['min']}, {s['max']}]")
    return "\n".join(lines)


def _build_executive_prompt(df_summary: str) -> str:
    return f"""You are an AI Executive Advisor and Senior Business Intelligence Analyst.

Based on the following dataset analysis, generate strategic business intelligence.

Return ONLY valid JSON:
{{
  "executive_summary": "2-3 sentence executive summary covering what happened, why it matters, and what leadership should know.",
  "findings": [
    {{"title": "Finding title", "detail": "Detailed finding with specific numbers where possible", "impact": "high|medium|low", "confidence": 85}}
  ],
  "risks": [
    {{"title": "Risk title", "detail": "Risk description with business impact", "severity": "high|medium|low", "probability": "high|medium|low", "mitigation": "Recommended action"}}
  ],
  "opportunities": [
    {{"title": "Opportunity title", "detail": "Opportunity description with expected benefit", "impact": "high|medium|low", "effort": "low|medium|high", "action": "Recommended action"}}
  ],
  "recommendations": [
    {{"title": "Recommendation title", "detail": "Specific actionable recommendation", "priority": "high|medium|low", "expected_outcome": "Expected business outcome"}}
  ],
  "business_health": {{
    "overall": 78,
    "revenue_score": 82,
    "growth_score": 75,
    "risk_score": 65,
    "operations_score": 80,
    "customer_score": 85,
    "data_quality_score": 90
  }},
  "confidence": 85
}}

Generate 3-5 items for findings, risks, opportunities, and recommendations each.

Dataset Analysis:
{df_summary}
"""


async def generate_enhanced_executive_intelligence(doc_id: int, df: pd.DataFrame) -> dict:
    """Run the enhanced 5-layer executive intelligence pipeline."""
    logger.info("Running enhanced executive intelligence for doc_id=%d", doc_id)

    # Layers 1-3: Dataset Intelligence + Data Quality + Business Analytics
    dataset_info = analyze_dataset(df)
    quality = run_data_quality_audit(df)
    analytics = run_business_analytics(df)

    df_summary = _df_summary_for_prompt(df)
    prompt = _build_executive_prompt(df_summary)

    try:
        raw = await generate_response_async(prompt, request_type="executive_intelligence")
        raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        result = json.loads(raw)
    except Exception as e:
        logger.warning("Executive intelligence generation failed: %s", e)
        result = {}

    return {
        "dataset_intelligence": dataset_info,
        "data_quality": quality,
        "business_analytics": analytics,
        "executive_intelligence": {
            "executive_summary": result.get("executive_summary", "Analysis complete."),
            "findings": result.get("findings", []),
            "risks": result.get("risks", []),
            "opportunities": result.get("opportunities", []),
            "recommendations": result.get("recommendations", []),
            "business_health": result.get("business_health", {
                "overall": quality["overall_score"], "data_quality_score": quality["overall_score"],
            }),
            "confidence": result.get("confidence", quality["overall_score"]),
        },
    }
