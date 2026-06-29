import io
import json
import logging

import numpy as np
import pandas as pd

from app.database.database import get_session_factory
from app.models.document import Document
from app.services.predictive_engine_v2 import run_predictive_analysis
from app.services.data_quality_service import run_data_quality_audit
from app.services.ai_service import generate_response_async
from sqlalchemy import select

logger = logging.getLogger(__name__)


def _estimate_revenue(df: pd.DataFrame, target: str) -> float:
    """Estimate annual revenue from available numeric columns."""
    numeric = df.select_dtypes(include=["number"])
    for col in ["revenue", "sales", "income", "totalcharges", "amount", "value"]:
        match = [c for c in numeric.columns if col.lower() in c.lower()]
        if match:
            total = numeric[match[0]].sum()
            return round(float(total), 2)
    # Fallback: estimate from MonthlyCharges-like columns
    for col in numeric.columns:
        vals = numeric[col].dropna()
        if "charge" in col.lower() or "fee" in col.lower() or "price" in col.lower():
            return round(float(vals.mean() * len(df) * 12), 2)
    return 0


async def generate_executive_prediction(doc_id: int) -> dict:
    """Run full predictive pipeline + translate into business decisions."""
    # Load data
    try:
        async with get_session_factory()() as db:
            result = await db.execute(select(Document).where(Document.id == doc_id))
            doc = result.scalar_one_or_none()
    except Exception:
        doc = None
    if not doc or not doc.content:
        return {"error": "Document not found"}

    df = pd.read_csv(io.StringIO(doc.content), on_bad_lines="skip") if doc.content.count(",") > 5 else None
    if df is None or len(df.columns) < 2:
        return {"error": "Dataset must be tabular"}

    dq = run_data_quality_audit(df)
    tech = await run_predictive_analysis(doc_id, df, dq.get("overall_score", 80))

    if "error" in tech:
        return tech

    target = tech.get("target", "unknown")
    task = tech.get("problem", {}).get("task", "unknown")
    confidence_pct = tech.get("confidence", {}).get("confidence", 50)
    importance = tech.get("feature_importance", [])
    risk = tech.get("risk", {})
    model_name = tech.get("model", {}).get("name", "unknown")
    metrics = tech.get("model", {}).get("metrics", {})

    # Business Impact
    total_rows = len(df)
    n_positive = int(df[target].sum()) if pd.api.types.is_numeric_dtype(df[target]) else int((df[target] == df[target].value_counts().index[0]).sum())
    pct_positive = round(n_positive / total_rows * 100, 1) if total_rows else 0
    revenue = _estimate_revenue(df, target)
    revenue_at_risk = round(revenue * (pct_positive / 100), 2)

    impact_level = "Critical" if revenue_at_risk > 1_000_000 else "High" if revenue_at_risk > 100_000 else "Medium" if revenue_at_risk > 10_000 else "Low"
    urgency = "Immediate Action Required" if impact_level == "Critical" else "Short-Term Priority" if impact_level == "High" else "Monitor"

    executive_summary = ""
    try:
        top_features_str = "; ".join([f["feature"] for f in importance[:5]]) if importance else "None identified"
        prompt = (
            f"Dataset: {len(df)} rows, target={target}, task={task}. "
            f"Top drivers: {top_features_str}. "
            f"At-risk population: {pct_positive}% ({n_positive} records). "
            f"Revenue at risk: ${revenue_at_risk:,.0f}. "
            f"Model: {model_name}, confidence: {confidence_pct}%. "
            f"Provide a 2-sentence executive summary predicting outcomes, explaining key drivers, "
            f"and stating recommended urgency."
        )
        raw = await generate_response_async(prompt, request_type="executive_prediction")
        executive_summary = raw[:500]
    except Exception as e:
        logger.warning("Executive summary gen failed: %s", e)
        executive_summary = (
            f"Prediction analysis indicates {pct_positive}% of records ({n_positive:,}) are "
            f"at risk based on {target}. Top drivers: {top_features_str}. "
            f"Revenue at risk: ${revenue_at_risk:,.0f}. Confidence: {confidence_pct}%."
        )

    # Root Cause Analysis (business language)
    root_causes = []
    for feat in importance[:6]:
        name = feat["feature"]
        pct = round(min(feat["importance"], 1) * 100, 1)
        business_name = name.replace("_", " ").title()
        if pct > 15:
            root_causes.append(f"{business_name} — {pct}% influence — key driver of {target}")
        elif pct > 5:
            root_causes.append(f"{business_name} — {pct}% influence — contributes to {target}")

    # Scenario Analysis
    base_impact = revenue_at_risk
    scenarios = {
        "best_case": round(base_impact * 0.6, 2),
        "expected_case": round(base_impact, 2),
        "worst_case": round(base_impact * 1.4, 2),
    }

    # Action Recommendations
    recommendations = []
    if importance:
        top_feat = importance[0]["feature"]
        rec_top = top_feat.replace("_", " ").title()
        recommendations.append({
            "priority": 1, "action": f"Target high-risk {rec_top} segments",
            "expected_churn_reduction": f"{round(importance[0]['importance'] * 20, 1)}%",
            "revenue_impact": f"${round(base_impact * 0.3):,}",
            "effort": "Medium",
        })
    if len(importance) > 1:
        rec2 = importance[1]["feature"].replace("_", " ").title()
        recommendations.append({
            "priority": 2, "action": f"Optimize {rec2} strategy",
            "expected_churn_reduction": f"{round(importance[1]['importance'] * 15, 1)}%",
            "revenue_impact": f"${round(base_impact * 0.2):,}",
            "effort": "Medium",
        })
    if len(importance) > 2:
        rec3 = importance[2]["feature"].replace("_", " ").title()
        recommendations.append({
            "priority": 3, "action": f"Review {rec3} policies",
            "expected_churn_reduction": f"{round(importance[2]['importance'] * 10, 1)}%",
            "revenue_impact": f"${round(base_impact * 0.15):,}",
            "effort": "Low",
        })

    # Opportunities
    opportunities = []
    if importance and importance[0]["importance"] > 0.1:
        opp_feat = importance[0]["feature"].replace("_", " ").title()
        opportunities.append({
            "title": f"{opp_feat} Optimization Opportunity",
            "description": f"Improving {opp_feat} could reduce {target} risk by approximately "
                          f"{round(min(importance[0]['importance'] * 30, 25), 1)}%",
            "revenue_impact": f"${round(base_impact * 0.35):,}",
        })
    opportunities.append({
        "title": "Predictive Retention Program",
        "description": f"Implement early warning system for {target} based on identified risk factors",
        "revenue_impact": f"${round(base_impact * 0.25):,}",
    })

    # Risk summary
    risks = []
    risks.append({
        "name": f"{target.replace('_', ' ').title()} Risk",
        "severity": risk.get("level", "moderate").capitalize(),
        "impact": f"${revenue_at_risk:,.0f} potential loss",
        "confidence": f"{confidence_pct}%",
        "affected": f"{n_positive:,} records ({pct_positive}%)",
    })

    return {
        "executive_summary": executive_summary,
        "business_impact": {
            "revenue_at_risk": revenue_at_risk,
            "revenue_at_risk_formatted": f"${revenue_at_risk:,.0f}",
            "population_at_risk": n_positive,
            "population_at_risk_pct": pct_positive,
            "total_population": total_rows,
            "impact_level": impact_level,
            "urgency": urgency,
            "confidence": confidence_pct,
        },
        "root_causes": root_causes,
        "scenarios": scenarios,
        "recommendations": recommendations,
        "opportunities": opportunities,
        "risks": risks,
        "technical": {
            "target": target,
            "task": task,
            "model": model_name,
            "metrics": metrics,
            "metrics_display": {
                "accuracy": metrics.get("accuracy"), "precision": metrics.get("precision"),
                "recall": metrics.get("recall"), "f1": metrics.get("f1"),
                "r2": metrics.get("r2"), "rmse": metrics.get("rmse"),
                "mae": metrics.get("mae"), "mape": metrics.get("mape"),
            },
            "feature_importance": importance[:10],
            "confidence_breakdown": tech.get("confidence", {}).get("breakdown"),
            "risk_score": risk.get("score"),
            "data_quality": {"score": dq.get("overall_score"), "grade": dq.get("grade")},
        },
    }
