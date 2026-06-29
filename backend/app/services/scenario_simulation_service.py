import logging
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

SCENARIO_TEMPLATES = {
    "revenue_increase": {
        "label": "Revenue increases by X%",
        "variable": "revenue",
        "direction": "increase",
        "default_pct": 10,
        "category": "growth",
    },
    "revenue_decline": {
        "label": "Revenue declines by X%",
        "variable": "revenue",
        "direction": "decrease",
        "default_pct": 12,
        "category": "risk",
    },
    "cost_reduction": {
        "label": "Operational costs decrease by X%",
        "variable": "cost",
        "direction": "decrease",
        "default_pct": 8,
        "category": "efficiency",
    },
    "cost_increase": {
        "label": "Costs increase by X%",
        "variable": "cost",
        "direction": "increase",
        "default_pct": 15,
        "category": "risk",
    },
    "churn_reduction": {
        "label": "Customer churn drops by X%",
        "variable": "churn",
        "direction": "decrease",
        "default_pct": 5,
        "category": "retention",
    },
    "churn_increase": {
        "label": "Churn increases by X%",
        "variable": "churn",
        "direction": "increase",
        "default_pct": 10,
        "category": "risk",
    },
    "marketing_increase": {
        "label": "Marketing budget increases by X%",
        "variable": "marketing",
        "direction": "increase",
        "default_pct": 20,
        "category": "growth",
    },
    "marketing_decrease": {
        "label": "Marketing budget decreases by X%",
        "variable": "marketing",
        "direction": "decrease",
        "default_pct": 20,
        "category": "efficiency",
    },
    "employee_turnover_increase": {
        "label": "Employee turnover doubles",
        "variable": "turnover",
        "direction": "increase",
        "default_pct": 100,
        "category": "risk",
    },
    "sales_decline": {
        "label": "Sales decline by X%",
        "variable": "sales",
        "direction": "decrease",
        "default_pct": 12,
        "category": "risk",
    },
    "sales_growth": {
        "label": "Sales grow by X%",
        "variable": "sales",
        "direction": "increase",
        "default_pct": 15,
        "category": "growth",
    },
    "inventory_cost_increase": {
        "label": "Inventory costs increase by X%",
        "variable": "inventory",
        "direction": "increase",
        "default_pct": 15,
        "category": "risk",
    },
}


def _find_matching_column(df: pd.DataFrame, keywords: list[str]) -> str | None:
    """Find the best matching column in the dataframe."""
    for col in df.columns:
        col_lower = col.lower()
        if any(kw in col_lower for kw in keywords):
            return col
    return None


def _estimate_baseline(df: pd.DataFrame, variable: str) -> dict:
    """Estimate baseline values for a variable from the dataset."""
    col_map = {
        "revenue": ["revenue", "sales", "income", "turnover", "total"],
        "cost": ["cost", "expense", "spend", "overhead"],
        "churn": ["churn", "attrition", "cancelled", "exited"],
        "marketing": ["marketing", "campaign", "advertising", "promotion"],
        "turnover": ["turnover", "attrition", "termination", "resignation"],
        "sales": ["sales", "revenue", "orders", "deals"],
        "inventory": ["inventory", "stock", "warehouse"],
    }

    matched = col_map.get(variable, [variable])
    col = _find_matching_column(df, matched)
    baseline = {"current_value": 0, "has_data": False, "column": None}

    if col and col in df.columns:
        vals = df[col].dropna()
        if len(vals) > 0 and pd.api.types.is_numeric_dtype(vals):
            baseline["current_value"] = round(float(vals.mean()), 2)
            baseline["total"] = round(float(vals.sum()), 2)
            baseline["has_data"] = True
            baseline["column"] = col

    return baseline


async def simulate_scenario(
    doc_id: int, scenario_id: str, adjustment_pct: float
) -> dict[str, Any]:
    """Simulate a business scenario and estimate impacts."""
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
    df = pd.read_csv(io.StringIO(doc.content), on_bad_lines="skip") if doc.content.count(",") > 5 else None
    if df is None:
        return {"error": "Dataset not available"}

    template = SCENARIO_TEMPLATES.get(scenario_id)
    if not template:
        return {"error": f"Unknown scenario: {scenario_id}"}

    variable = template["variable"]
    direction = template["direction"]
    pct = adjustment_pct or template["default_pct"]
    baseline = _estimate_baseline(df, variable)

    if direction == "increase":
        current_val = baseline["current_value"]
        new_val = current_val * (1 + pct / 100)
        change_val = new_val - current_val
        change_pct = pct
    else:
        current_val = baseline["current_value"]
        new_val = current_val * (1 - pct / 100)
        change_val = new_val - current_val
        change_pct = -pct

    # Estimate financial impact
    revenue_cols = [c for c in ["revenue", "sales", "income", "total"] if c in df.columns]
    total_revenue = 0
    for rc in revenue_cols:
        vals = df[rc].dropna()
        if len(vals) > 0 and pd.api.types.is_numeric_dtype(vals):
            total_revenue += vals.sum()

    profit_cols = [c for c in ["profit", "net_income", "earnings"] if c in df.columns]
    total_profit = 0
    for pc in profit_cols:
        vals = df[pc].dropna()
        if len(vals) > 0 and pd.api.types.is_numeric_dtype(vals):
            total_profit += vals.sum()

    if total_revenue == 0:
        total_revenue = baseline["total"] or baseline["current_value"] * len(df) if baseline["has_data"] else 100000

    revenue_impact = total_revenue * (change_pct / 100) if variable in ("revenue", "sales") else total_revenue * (change_pct / 400)
    profit_impact = total_profit * (change_pct / 100) if variable in ("revenue", "sales", "cost") else revenue_impact * 0.3
    cost_impact = -revenue_impact * 0.6 if variable == "cost" else revenue_impact * 0.2

    roi = abs(revenue_impact / (abs(cost_impact) + 1)) if abs(cost_impact) > 0 else 0

    risk_score = min(100, max(0, abs(change_pct) * 3 + (30 if direction == "decrease" and variable in ("revenue", "sales") else 10)))
    confidence = min(95, max(40, 80 - abs(change_pct) * 0.5 + (10 if baseline["has_data"] else -20)))

    return {
        "scenario_id": scenario_id,
        "scenario_label": template["label"].replace("X%", f"{pct:.0f}%"),
        "category": template["category"],
        "baseline": baseline,
        "adjustment_pct": pct,
        "direction": direction,
        "current_value": round(current_val, 2) if current_val else 0,
        "simulated_value": round(new_val, 2) if new_val else 0,
        "change_pct": round(change_pct, 1),
        "revenue_impact": round(revenue_impact, 2),
        "profit_impact": round(profit_impact, 2),
        "cost_impact": round(cost_impact, 2),
        "roi": round(roi, 2),
        "risk_score": round(risk_score, 1),
        "confidence": round(confidence, 1),
        "total_revenue": round(total_revenue, 2),
    }


async def run_scenario_analysis(doc_id: int) -> dict[str, Any]:
    """Run best/expected/worst case scenario analysis."""
    best = await simulate_scenario(doc_id, "revenue_increase", 15)
    expected = await simulate_scenario(doc_id, "revenue_increase", 8)
    worst = await simulate_scenario(doc_id, "revenue_decline", 10)

    if "error" in expected:
        # Fall back to generic values
        return {
            "doc_id": doc_id,
            "scenarios": [],
            "comparison": {},
        }

    return {
        "doc_id": doc_id,
        "scenarios": [
            {"label": "Best Case", "scenario": "Revenue Growth", "change_pct": best.get("change_pct", 15),
             "revenue_impact": best.get("revenue_impact", 0), "risk_score": best.get("risk_score", 0), "confidence": best.get("confidence", 70)},
            {"label": "Expected Case", "scenario": "Moderate Growth", "change_pct": expected.get("change_pct", 8),
             "revenue_impact": expected.get("revenue_impact", 0), "risk_score": expected.get("risk_score", 0), "confidence": expected.get("confidence", 80)},
            {"label": "Worst Case", "scenario": "Revenue Decline", "change_pct": worst.get("change_pct", -10),
             "revenue_impact": worst.get("revenue_impact", 0), "risk_score": worst.get("risk_score", 0), "confidence": worst.get("confidence", 60)},
        ],
        "comparison": {
            "revenue_range": [worst.get("total_revenue", 0) * (1 + worst.get("change_pct", 0) / 100),
                              best.get("total_revenue", 0) * (1 + best.get("change_pct", 0) / 100)],
            "best_confidence": best.get("confidence", 0),
            "expected_confidence": expected.get("confidence", 0),
            "worst_confidence": worst.get("confidence", 0),
        },
    }
