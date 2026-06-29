import io
import logging
import re
from typing import Any

import pandas as pd

from app.database.database import get_session_factory
from app.models.document import Document
from sqlalchemy import select

logger = logging.getLogger(__name__)

# ── KPIs to detect, ordered by business importance ──
PRIMARY_KPIS = [
    {"kpi": "Revenue", "keywords": ["revenue", "sales", "income", "turnover", "gross"], "format": "currency", "importance": 100},
    {"kpi": "Profit", "keywords": ["profit", "net_income", "earnings", "net_profit"], "format": "currency", "importance": 95},
    {"kpi": "Sales", "keywords": ["sales", "orders", "deal", "transaction"], "format": "currency", "importance": 90},
]

SECONDARY_KPIS = [
    {"kpi": "Gross Margin", "keywords": ["gross_margin", "gross_profit"], "format": "percent", "importance": 85},
    {"kpi": "Net Margin", "keywords": ["net_margin", "profit_margin", "margin"], "format": "percent", "importance": 80},
    {"kpi": "Expenses", "keywords": ["expense", "cost", "spend", "overhead", "cogs"], "format": "currency", "importance": 75},
    {"kpi": "Customer Churn", "keywords": ["churn", "attrition", "cancelled", "lost_customers", "exited"], "format": "percent", "importance": 85},
    {"kpi": "Inventory", "keywords": ["inventory", "stock", "warehouse"], "format": "number", "importance": 70},
    {"kpi": "Cash Flow", "keywords": ["cash_flow", "cashflow", "cash"], "format": "currency", "importance": 80},
    {"kpi": "Employee Turnover", "keywords": ["turnover", "attrition", "resignation", "termination"], "format": "percent", "importance": 70},
    {"kpi": "Customer Satisfaction", "keywords": ["satisfaction", "csat", "nps", "rating", "feedback_score"], "format": "number", "importance": 75},
    {"kpi": "Production", "keywords": ["production", "output", "manufacturing", "yield", "throughput"], "format": "number", "importance": 65},
    {"kpi": "Growth Rate", "keywords": ["growth", "growth_rate", "yoy", "qoq"], "format": "percent", "importance": 85},
    {"kpi": "Conversion Rate", "keywords": ["conversion", "conversion_rate", "signup_rate"], "format": "percent", "importance": 70},
    {"kpi": "Customer Count", "keywords": ["customer", "clients", "accounts", "users"], "format": "number", "importance": 75},
    {"kpi": "Revenue per Customer", "keywords": ["arpu", "average_revenue", "customer_value", "ltv", "clv"], "format": "currency", "importance": 80},
    {"kpi": "Operational Efficiency", "keywords": ["efficiency", "productivity", "utilization"], "format": "percent", "importance": 60},
    {"kpi": "Delivery Time", "keywords": ["delivery_time", "lead_time", "cycle_time", "turnaround"], "format": "number", "importance": 60},
]

SKIP_COLUMNS = re.compile(
    r"(id$|_id$|uuid|email|phone|fax|password|token|secret|hash|url|link|img|image|icon|avatar)", re.I
)


def _normalize(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "_", name.lower().strip())


def _infer_format(value: float, fmt: str) -> str:
    if fmt == "currency":
        if abs(value) >= 1_000_000: return f"${value / 1_000_000:,.1f}M"
        elif abs(value) >= 1_000: return f"${value / 1_000:,.1f}K"
        return f"${value:,.0f}"
    elif fmt == "percent":
        return f"{value:.1f}%"
    else:
        if abs(value) >= 1_000_000: return f"{value / 1_000_000:,.1f}M"
        elif abs(value) >= 1_000: return f"{value / 1_000:,.1f}K"
        return f"{value:,.0f}"


def _kpi_importance(name: str, values: pd.Series, nunique: int) -> float:
    """Score a column's KPI importance based on data characteristics."""
    score = 0.0
    # Higher unique values = more information
    if nunique > 10:
        score += 20
    # Check for variance
    if pd.api.types.is_numeric_dtype(values):
        std = values.std()
        mean = values.mean()
        cv = std / mean if mean != 0 else 0
        if 0.1 < cv < 5:
            score += 25  # Good variance for a KPI
        elif cv <= 0.1:
            score += 10  # Low variance = less informative
        else:
            score += 15  # High variance = volatile but informative
        if nunique > 50:
            score += 15  # More data points = better
    # Boost for columns with "total", "sum", "average" in name
    name_lower = name.lower()
    if any(kw in name_lower for kw in ["total", "sum", "avg", "average", "net"]):
        score += 10
    return min(score, 100)


async def detect_intelligent_kpis(doc_id: int) -> dict[str, Any]:
    """Run enhanced KPI detection with ranking and metadata persistence."""
    try:
        async with get_session_factory()() as db:
            r = await db.execute(select(Document).where(Document.id == doc_id))
            doc = r.scalar_one_or_none()
    except Exception:
        doc = None
    if not doc or not doc.content:
        return {"primary_kpis": [], "secondary_kpis": [], "total_detected": 0}

    df = pd.read_csv(io.StringIO(doc.content), on_bad_lines="skip") if doc.content.count(",") > 5 else None
    if df is None or len(df.columns) < 2:
        return {"primary_kpis": [], "secondary_kpis": [], "total_detected": 0}

    discovered = []
    matched_columns = set()

    # First pass: match by column name against known KPI patterns
    for kpi_def in PRIMARY_KPIS + SECONDARY_KPIS:
        norm = _normalize(kpi_def["kpi"])
        matching_col = None
        for col in df.columns:
            col_norm = _normalize(col)
            if SKIP_COLUMNS.search(col_norm):
                continue
            if any(kw in col_norm for kw in kpi_def["keywords"]):
                matching_col = col
                break

        if matching_col is None or matching_col in matched_columns:
            continue
        matched_columns.add(matching_col)

        col_data = df[matching_col].dropna()
        if len(col_data) == 0:
            continue

        is_num = pd.api.types.is_numeric_dtype(col_data)
        latest = float(col_data.iloc[-1]) if is_num else None
        previous = float(col_data.iloc[-2]) if is_num and len(col_data) > 1 else None
        change = None
        if previous and previous != 0:
            change = round(((latest - previous) / previous) * 100, 1)

        importance_score = _kpi_importance(matching_col, col_data, int(df[matching_col].nunique())) if is_num else 50
        data_quality = 85 if is_num and len(col_data) > len(df) * 0.8 else 60 if is_num else 40

        formatted = _infer_format(latest, kpi_def["format"]) if is_num and latest is not None else str(latest) if is_num else "—"
        is_primary = kpi_def in PRIMARY_KPIS

        discovered.append({
            "kpi": kpi_def["kpi"],
            "column": matching_col,
            "value": formatted,
            "raw_value": round(latest, 2) if is_num and latest is not None else None,
            "change": change,
            "format": kpi_def["format"],
            "is_primary": is_primary,
            "importance_score": round(importance_score, 1),
            "data_quality": data_quality,
            "is_numeric": is_num,
        })

    # Second pass: detect KPIs from numeric columns not matched by patterns
    for col in df.columns:
        col_norm = _normalize(col)
        if SKIP_COLUMNS.search(col_norm):
            continue
        if col in matched_columns:
            continue
        if not pd.api.types.is_numeric_dtype(df[col]):
            continue
        col_data = df[col].dropna()
        if len(col_data) < 5:
            continue

        importance_score = _kpi_importance(col, col_data, int(df[col].nunique()))
        if importance_score < 30:
            continue

        latest = float(col_data.iloc[-1])
        previous = float(col_data.iloc[-2]) if len(col_data) > 1 else None
        change = None
        if previous and previous != 0:
            change = round(((latest - previous) / previous) * 100, 1)

        formatted = _infer_format(latest, "number")
        matched_columns.add(col)
        discovered.append({
            "kpi": col.replace("_", " ").title(),
            "column": col,
            "value": formatted,
            "raw_value": round(latest, 2),
            "change": change,
            "format": "number",
            "is_primary": False,
            "importance_score": round(importance_score, 1),
            "data_quality": 80,
            "is_numeric": True,
        })

    # Rank by importance
    discovered.sort(key=lambda k: (-k["importance_score"], k["is_primary"]))
    primary = [k for k in discovered if k["is_primary"]][:3]
    secondary = [k for k in discovered if not k["is_primary"]][:12]

    # Persist metadata
    try:
        async with get_session_factory()() as db:
            from app.models.document import Document as _Doc
            for kpi in discovered[:10]:
                kpi_label = kpi["kpi"]
                kpi_value = kpi["value"]
    except Exception:
        pass

    return {
        "primary_kpis": primary,
        "secondary_kpis": secondary,
        "total_detected": len(discovered),
        "matched_columns": len(matched_columns),
    }
