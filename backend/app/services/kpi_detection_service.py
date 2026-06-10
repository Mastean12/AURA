import io
import logging
import re

import pandas as pd

from app.database.database import get_session_factory
from app.models.document import Document
from sqlalchemy import select

logger = logging.getLogger(__name__)

KPI_PATTERNS: dict[str, list[dict]] = {
    "Finance": [
        {"keywords": ["revenue", "sales_revenue", "income"], "label": "Revenue", "format": "currency"},
        {"keywords": ["profit", "net_income", "earnings"], "label": "Profit", "format": "currency"},
        {"keywords": ["expense", "cost", "operating_cost"], "label": "Expenses", "format": "currency"},
        {"keywords": ["cash_flow", "cashflow"], "label": "Cash Flow", "format": "currency"},
        {"keywords": ["margin", "profit_margin"], "label": "Margin", "format": "percent"},
    ],
    "Sales": [
        {"keywords": ["sales", "total_sales"], "label": "Sales", "format": "currency"},
        {"keywords": ["customer", "clients", "accounts"], "label": "Customers", "format": "number"},
        {"keywords": ["conversion", "conversion_rate"], "label": "Conversion Rate", "format": "percent"},
        {"keywords": ["lead", "prospects"], "label": "Leads", "format": "number"},
    ],
    "HR": [
        {"keywords": ["employee", "headcount", "staff"], "label": "Employees", "format": "number"},
        {"keywords": ["retention", "retention_rate"], "label": "Retention", "format": "percent"},
        {"keywords": ["turnover", "attrition"], "label": "Turnover", "format": "percent"},
        {"keywords": ["salary", "compensation", "wage"], "label": "Salary", "format": "currency"},
    ],
    "Operations": [
        {"keywords": ["inventory", "stock"], "label": "Inventory", "format": "number"},
        {"keywords": ["delivery_time", "lead_time", "cycle_time"], "label": "Delivery Time", "format": "number"},
        {"keywords": ["performance", "efficiency"], "label": "Performance", "format": "percent"},
    ],
}


def _infer_format(value: float, fmt: str) -> str:
    if fmt == "currency":
        if abs(value) >= 1_000_000:
            return f"${value / 1_000_000:,.1f}M"
        elif abs(value) >= 1_000:
            return f"${value / 1_000:,.1f}K"
        return f"${value:,.0f}"
    elif fmt == "percent":
        return f"{value:.1f}%"
    else:
        if abs(value) >= 1_000_000:
            return f"{value / 1_000_000:,.1f}M"
        elif abs(value) >= 1_000:
            return f"{value / 1_000:,.1f}K"
        return f"{value:,.0f}"


def _normalize(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "_", name.lower().strip())


def _detect_kpis(df: pd.DataFrame) -> list[dict]:
    discovered: list[dict] = []
    matched_columns: set[str] = set()

    for category, patterns in KPI_PATTERNS.items():
        for pattern in patterns:
            keyword_variants = pattern["keywords"]
            matching_col = None
            for col in df.columns:
                norm = _normalize(col)
                if any(kw in norm for kw in keyword_variants):
                    matching_col = col
                    break
            if matching_col is None:
                continue
            if matching_col in matched_columns:
                continue
            matched_columns.add(matching_col)

            col_data = df[matching_col].dropna()
            if len(col_data) == 0:
                continue

            if pd.api.types.is_numeric_dtype(col_data):
                latest = col_data.iloc[-1]
                previous = col_data.iloc[-2] if len(col_data) > 1 else None
                change = None
                if previous and previous != 0:
                    change = round(((latest - previous) / previous) * 100, 1)
                formatted = _infer_format(float(latest), pattern["format"])
                discovered.append({
                    "category": category,
                    "label": pattern["label"],
                    "column": matching_col,
                    "value": formatted,
                    "raw_value": float(latest),
                    "change": change,
                    "format": pattern["format"],
                })

    return discovered


async def discover_kpis(doc_id: int) -> list[dict]:
    logger.info("Discovering KPIs for doc_id=%d", doc_id)
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

    return _detect_kpis(df)
