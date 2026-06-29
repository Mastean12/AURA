import logging
import re
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ── Pattern definitions ──
IDENTIFIER_PATTERNS = re.compile(r"^(id|.*_id|.*id|code|key|uuid|ref|reference|account.*num)", re.I)
DATE_PATTERNS = re.compile(r"^(date|time|timestamp|year|month|day|quarter|period|created_at|updated_at)", re.I)
GEO_PATTERNS = re.compile(r"^(country|region|city|state|address|zip|postal|latitude|longitude|location)", re.I)
CURRENCY_PATTERNS = re.compile(r"^(price|amount|cost|fee|charge|salary|wage|budget|revenue|income|expense)", re.I)

REVENUE_PATTERNS = re.compile(r"^(revenue|sales|income|turnover|gross|total.*amount)", re.I)
COST_PATTERNS = re.compile(r"^(cost|expense|spend|cogs|overhead|operating.*cost)", re.I)
PROFIT_PATTERNS = re.compile(r"^(profit|margin|net.*income|ebitda|earnings)", re.I)
PRICE_PATTERNS = re.compile(r"(price|amount|fee|charge|salary|wage|budget|subscription)", re.I)
RATING_PATTERNS = re.compile(r"(rating|score|rank|star|review.*score)", re.I)
COUNT_PATTERNS = re.compile(r"(count|num|quantity|total|stock|inventory|frequency)", re.I)
PCT_PATTERNS = re.compile(r"(percent|pct|rate|ratio|discount|interest|margin|growth)", re.I)
KPI_PATTERNS_R2 = re.compile(r"^(score|rate|ratio|percent|index|count|amount|value|total|balance|growth|roi|kpi)", re.I)

TARGET_PATTERNS = {
    "churn": re.compile(r"churn|attrition|exit|left|stopped|cancel", re.I),
    "fraud": re.compile(r"fraud|default|risk|bad", re.I),
    "revenue": re.compile(r"revenue|sales_amount|income", re.I),
    "profit": re.compile(r"profit|net.*income|margin", re.I),
    "retention": re.compile(r"retention|retained|stayed", re.I),
    "conversion": re.compile(r"conversion|converted|signed_up", re.I),
    "satisfaction": re.compile(r"satisfaction|nps|csat|rating|score", re.I),
}

# ── Business Context → Industry mapping ──
BUSINESS_CONTEXT_KEYWORDS = {
    "Sales Analytics": ["revenue", "sales", "deal", "pipeline", "customer", "product", "region", "discount", "order"],
    "Finance Analytics": ["revenue", "expense", "profit", "cash", "asset", "liability", "budget", "forecast", "tax"],
    "HR Analytics": ["employee", "hiring", "salary", "attrition", "turnover", "promotion", "performance", "headcount"],
    "Customer Analytics": ["customer", "churn", "satisfaction", "support", "ticket", "feedback", "segment", "loyalty"],
    "Marketing Analytics": ["campaign", "click", "impression", "conversion", "lead", "acquisition", "channel", "roi"],
    "Operations Analytics": ["inventory", "supplier", "delivery", "production", "shipment", "logistics", "cycle_time"],
    "Supply Chain Analytics": ["supplier", "procurement", "warehouse", "freight", "lead_time", "stock", "vendor"],
    "Healthcare Analytics": ["patient", "diagnosis", "treatment", "readmission", "hospital", "claim", "provider"],
    "Banking Analytics": ["account", "loan", "deposit", "transaction", "balance", "interest", "credit", "fraud"],
    "Education Analytics": ["student", "course", "grade", "enrollment", "teacher", "class", "attendance", "exam"],
    "Government Analytics": ["citizen", "tax", "budget", "service", "compliance", "regulation", "population"],
    "Customer Support Analytics": ["ticket", "support", "complaint", "resolution", "csat", "sla", "priority"],
    "General Analytics": [],
}

CONTEXT_TO_INDUSTRY = {
    "Sales Analytics": "Sales",
    "Finance Analytics": "Finance",
    "Banking Analytics": "Banking",
    "Healthcare Analytics": "Healthcare",
    "Retail Analytics": "Retail",
    "Manufacturing Analytics": "Manufacturing",
    "Supply Chain Analytics": "Supply Chain",
    "HR Analytics": "Human Resources",
    "Marketing Analytics": "Marketing",
    "Education Analytics": "Education",
    "Government Analytics": "Government",
    "Customer Support Analytics": "Customer Support",
    "Operations Analytics": "General Business",
    "Customer Analytics": "General Business",
    "General Analytics": "General Business",
}


def classify_column(name: str, dtype: str, nunique: int, nrows: int,
                    sample_values: pd.Series | None = None) -> dict[str, Any]:
    col_lower = name.lower().strip()
    result = {"name": name, "dtype": dtype, "cardinality": "high" if nunique > 50 else "low",
              "nunique": nunique, "classification": "categorical", "is_target": False}

    if IDENTIFIER_PATTERNS.match(col_lower):
        result["classification"] = "identifier"
        return result

    if DATE_PATTERNS.match(col_lower) or dtype in ("datetime64[ns]", "datetime"):
        result["classification"] = "date"
        return result

    if GEO_PATTERNS.match(col_lower):
        result["classification"] = "geographic"
        return result

    is_numeric = dtype in ("int64", "float64", "int32", "float32", "int", "float")
    is_str = dtype == "str" or dtype == "object"

    # Check if a string column contains numeric data with currency symbols
    if is_str and sample_values is not None and nunique > 1:
        try:
            cleaned = sample_values.astype(str).str.replace(r"[₹$€£¥, ]", "", regex=True).str.strip()
            numeric_count = pd.to_numeric(cleaned, errors="coerce").notna().sum()
            if numeric_count >= 3:
                is_numeric = True
                result["dtype"] = "numeric"
                result["is_currency"] = True
        except Exception:
            pass

    if is_numeric:
        result["dtype"] = "numeric"
        if REVENUE_PATTERNS.match(col_lower) or PRICE_PATTERNS.search(col_lower):
            result["classification"] = "kpi"; result["kpi_type"] = "revenue"
        elif COST_PATTERNS.match(col_lower):
            result["classification"] = "kpi"; result["kpi_type"] = "cost"
        elif PROFIT_PATTERNS.match(col_lower):
            result["classification"] = "kpi"; result["kpi_type"] = "profit"
        elif KPI_PATTERNS_R2.match(col_lower) or RATING_PATTERNS.search(col_lower) or COUNT_PATTERNS.search(col_lower) or PCT_PATTERNS.search(col_lower):
            result["classification"] = "kpi"; result["kpi_type"] = "metric"
        elif nunique <= 10 and not result.get("is_currency"):
            result["classification"] = "categorical"; result["cardinality"] = "low"
        else:
            result["classification"] = "numeric"
            result["cardinality"] = "high" if nunique > 100 else "low"

        if CURRENCY_PATTERNS.search(col_lower):
            result["is_currency"] = True

        for target_type, pattern in TARGET_PATTERNS.items():
            if pattern.search(col_lower):
                result["is_target"] = True; result["target_type"] = target_type; break
    else:
        # Check if column name suggests it's a KPI even if data is string (e.g., corrupted CSV)
        if REVENUE_PATTERNS.match(col_lower) or COST_PATTERNS.match(col_lower) or PROFIT_PATTERNS.match(col_lower):
            result["classification"] = "kpi"; result["kpi_type"] = "probable"
            result["dtype"] = "numeric"
        elif KPI_PATTERNS_R2.match(col_lower) or RATING_PATTERNS.search(col_lower) or COUNT_PATTERNS.search(col_lower) or PCT_PATTERNS.search(col_lower) or PRICE_PATTERNS.search(col_lower):
            result["classification"] = "kpi"; result["kpi_type"] = "probable"
            result["dtype"] = "numeric"
        else:
            if nunique == nrows and nrows > 100:
                result["classification"] = "identifier"
            elif nunique <= 30:
                result["classification"] = "categorical"; result["cardinality"] = "low"
            elif nunique <= 100:
                result["classification"] = "categorical"; result["cardinality"] = "medium"
            else:
                result["classification"] = "text"; result["cardinality"] = "high"
        for target_type, pattern in TARGET_PATTERNS.items():
            if pattern.search(col_lower):
                result["is_target"] = True; result["target_type"] = target_type; break

    return result


def detect_business_context(df: pd.DataFrame) -> str:
    all_cols = " ".join(df.columns.str.lower())
    scores: dict[str, int] = {}
    for context, keywords in BUSINESS_CONTEXT_KEYWORDS.items():
        if not keywords:
            continue
        score = sum(1 for kw in keywords if kw in all_cols)
        scores[context] = score
    if not scores:
        return "General Analytics"
    return max(scores, key=scores.get)


def detect_industry(business_context: str) -> str:
    return CONTEXT_TO_INDUSTRY.get(business_context, "General Business")


def detect_target_variable(columns: list[dict[str, Any]], df: pd.DataFrame) -> dict[str, Any]:
    targets = [c for c in columns if c.get("is_target")]
    if targets:
        return {"target_variable": targets[0]["name"], "target_type": targets[0].get("target_type", "unknown"),
                "detection_method": "pattern_match"}
    numeric_cols = [c for c in columns if c.get("dtype") == "numeric"]
    if numeric_cols:
        candidates = [c for c in numeric_cols if c.get("classification") == "kpi"]
        if candidates:
            return {"target_variable": candidates[0]["name"],
                    "target_type": candidates[0].get("kpi_type", "metric"),
                    "detection_method": "kpi_based"}
        return {"target_variable": numeric_cols[-1]["name"],
                "target_type": "numeric", "detection_method": "fallback_last_numeric"}
    return {"target_variable": None, "target_type": None, "detection_method": "none"}


def detect_relationships(df: pd.DataFrame, columns: list[dict]) -> list[dict]:
    """Map strong correlations between actual numeric columns."""
    numeric_cols = []
    for c in columns:
        if c.get("dtype") == "numeric" and c["name"] in df.columns and pd.api.types.is_numeric_dtype(df[c["name"]]):
            numeric_cols.append(c["name"])
    if len(numeric_cols) < 2:
        return []
    corr = df[numeric_cols].corr().round(3)
    relationships = []
    for i in range(len(numeric_cols)):
        for j in range(i + 1, len(numeric_cols)):
            val = corr.iloc[i, j]
            if abs(val) >= 0.3:
                relationships.append({
                    "variable_a": numeric_cols[i],
                    "variable_b": numeric_cols[j],
                    "correlation": float(val),
                    "direction": "positive" if val > 0 else "negative",
                    "strength": "strong" if abs(val) >= 0.7 else "moderate" if abs(val) >= 0.5 else "weak",
                })
    return sorted(relationships, key=lambda r: abs(r["correlation"]), reverse=True)[:15]


def analyze_dataset(df: pd.DataFrame) -> dict[str, Any]:
    """Run full Dataset Intelligence Engine v2 analysis."""
    nrows, ncols = df.shape
    columns = []
    for col in df.columns:
        nunique = int(df[col].nunique())
        dtype = str(df[col].dtype)
        sv = df[col].dropna().head(10) if pd.api.types.is_numeric_dtype(df[col]) else df[col].dropna().head(5)
        columns.append(classify_column(col, dtype, nunique, nrows, sv))

    business_context = detect_business_context(df)
    industry = detect_industry(business_context)
    target_info = detect_target_variable(columns, df)
    relationships = detect_relationships(df, columns)

    def _truly_numeric(col_name: str) -> bool:
        return col_name in df.columns and pd.api.types.is_numeric_dtype(df[col_name])

    return {
        "row_count": nrows,
        "column_count": ncols,
        "industry": industry,
        "dataset_type": business_context,
        "target_variable": target_info["target_variable"],
        "target_type": target_info["target_type"],
        "identifier_columns": [c["name"] for c in columns if c["classification"] == "identifier"],
        "kpi_columns": [c["name"] for c in columns if c.get("classification") == "kpi" and _truly_numeric(c["name"])],
        "kpi_details": [{"name": c["name"], "type": c.get("kpi_type", "metric")} for c in columns if c.get("classification") == "kpi" and _truly_numeric(c["name"])],
        "currency_columns": [c["name"] for c in columns if c.get("is_currency")],
        "date_columns": [c["name"] for c in columns if c["classification"] == "date"],
        "numeric_columns": [c["name"] for c in columns if c["classification"] == "numeric" and _truly_numeric(c["name"])],
        "probable_kpi_columns": [c["name"] for c in columns if c.get("classification") == "kpi" and not _truly_numeric(c["name"])],
        "categorical_columns": [c["name"] for c in columns if c["classification"] == "categorical"],
        "geographic_columns": [c["name"] for c in columns if c["classification"] == "geographic"],
        "text_columns": [c["name"] for c in columns if c["classification"] == "text"],
        "high_cardinality_columns": [c["name"] for c in columns if c.get("cardinality") == "high"],
        "relationships": relationships,
        "columns": columns,
    }
