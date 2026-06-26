import io
import json
import logging
from typing import Any

import pandas as pd

from app.services.business_analytics_engine_v2 import get_business_analytics
from app.services.business_analytics_service import compute_descriptive_stats, compute_correlations
from app.services.dataset_intelligence_service import analyze_dataset
from app.services.data_quality_service import run_data_quality_audit
from app.services.ai_service import generate_response_async

logger = logging.getLogger(__name__)


def _currency(val: float) -> str:
    if abs(val) >= 1_000_000: return f"${val/1_000_000:.1f}M"
    if abs(val) >= 1_000: return f"${val/1_000:.0f}K"
    return f"${val:.0f}"


def _pct(val: float) -> str:
    return f"{val:.1f}%"


def _build_narrative_prompt(analysis: dict) -> str:
    kpis = analysis.get("kpi_summary", {}).get("kpis", [])
    trend = analysis.get("trend_analysis", {})
    comparative = analysis.get("comparative_analysis", [])
    correlations = analysis.get("correlations", [])
    dq = analysis.get("descriptive_stats", {})
    ds = analysis.get("dataset_intelligence", {})

    lines = [f"Dataset: {ds.get('dataset_type', 'Unknown')} | Industry: {ds.get('industry', 'General')}"]
    lines.append(f"Target: {ds.get('target_variable', 'N/A')}")
    if kpis:
        for k in kpis[:5]:
            lines.append(f"KPI: {k['label']}={k['value']} ({k.get('change', 'N/A')}%)")
    if trend:
        for col, t in list(trend.items())[:3]:
            lines.append(f"Trend: {col} {t['direction']} {t.get('change_pct', 0):.1f}% (current={t['current']})")
    if comparative:
        for c in comparative[:2]:
            lines.append(f"Compare: {c['kpi']} by {c['segment']} - best={c['top_segment']}({c['top_value']:.1f}) worst={c['bottom_segment']}({c['bottom_value']:.1f})")
    if correlations:
        for c in correlations[:2]:
            lines.append(f"Correlation: {c['col_a']} vs {c['col_b']} = {c['correlation']} ({c['direction']})")

    return """You are a Senior Business Intelligence Analyst and Executive Advisor at a top consulting firm.

Based on the following dataset analysis, generate a professional executive report.

Return ONLY valid JSON:
{
  "executive_summary": "3-4 sentence executive summary covering what happened, why it matters, and what leadership should do. Use specific numbers.",
  "key_findings": [
    {"title": "Finding title with specific numbers", "detail": "Evidence-based explanation", "impact": "high|medium|low", "confidence": 85}
  ],
  "root_causes": [
    {"cause": "Root cause description", "evidence": "Supporting data evidence", "impact_area": "Revenue|Cost|Operations|Customers|Risk"}
  ],
  "business_impact": {
    "revenue_impact": "Description of revenue impact with numbers",
    "cost_impact": "Description of cost impact",
    "operational_impact": "Description of operational impact",
    "customer_impact": "Description of customer impact"
  },
  "risks": [
    {"name": "Risk name", "description": "Risk with business consequence", "severity": "Critical|High|Medium|Low", "financial_exposure": "Estimated $ impact", "mitigation": "Recommended action"}
  ],
  "opportunities": [
    {"name": "Opportunity name", "description": "Opportunity with expected benefit", "impact": "high|medium|low", "estimated_value": "$ value", "action": "Recommended action"}
  ],
  "recommendations": [
    {"title": "Action title", "description": "Specific recommendation", "priority": "Critical|High|Medium|Low", "expected_outcome": "Expected business outcome", "roi": "Estimated ROI"}
  ],
  "business_health": {
    "overall": 78, "revenue_health": 82, "cost_health": 65, "growth_health": 75, "risk_health": 60, "operations_health": 80, "customer_health": 85
  },
  "confidence": 85
}

Dataset Analysis:
""" + "\n".join(lines)


async def run_executive_intelligence(doc_id: int) -> dict[str, Any]:
    """Run the complete Executive Intelligence Engine v3 pipeline."""
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

    df = pd.read_csv(io.StringIO(doc.content)) if doc.content.count(",") > 5 else None
    if df is None or len(df.columns) < 2:
        return {"error": "Dataset must be tabular"}

    # Layer 1: Business Analytics (KPI detection, trends, correlations, comparative)
    analysis = await get_business_analytics(doc_id)
    if "error" in analysis:
        return analysis

    dq = run_data_quality_audit(df)

    # Layer 2: Executive Narrative Generation
    prompt = _build_narrative_prompt(analysis)
    narrative = {}
    try:
        raw = await generate_response_async(prompt, request_type="executive_intelligence")
        raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        narrative = json.loads(raw)
    except Exception as e:
        logger.warning("Narrative generation failed: %s", e)
        narrative = {
            "executive_summary": "Analysis complete based on " + str(analysis.get("dataset_intelligence", {}).get("dataset_type", "dataset")),
            "key_findings": [{"title": f"Analysis of {len(kpis)} KPIs reveals key trends", "detail": "See KPI section for details", "impact": "medium", "confidence": 70} for kpis in [analysis.get("kpi_summary", {}).get("kpis", [])]],
            "business_health": {"overall": dq.get("overall_score", 70)},
        }

    return {
        "doc_id": doc_id,
        "executive_summary": narrative.get("executive_summary", analysis.get("dataset_intelligence", {}).get("dataset_type", "Analysis complete.")),
        "key_findings": narrative.get("key_findings", []),
        "root_causes": narrative.get("root_causes", []),
        "business_impact": narrative.get("business_impact", {}),
        "risks": narrative.get("risks", []),
        "opportunities": narrative.get("opportunities", []),
        "recommendations": narrative.get("recommendations", []),
        "business_health": narrative.get("business_health", {
            "overall": dq.get("overall_score", 70),
            "revenue_health": 70, "cost_health": 70, "growth_health": 70,
            "risk_health": 70, "operations_health": 70, "customer_health": 70,
        }),
        "confidence": narrative.get("confidence", dq.get("overall_score", 70) / 100),
        "data_quality": {"score": dq.get("overall_score"), "grade": dq.get("grade")},
        "kpi_summary": analysis.get("kpi_summary", {}),
        "charts": analysis.get("charts", []),
        "trend_analysis": analysis.get("trend_analysis", {}),
        "comparative_analysis": analysis.get("comparative_analysis", []),
        "correlations": analysis.get("correlations", []),
    }
