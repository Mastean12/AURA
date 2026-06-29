import logging
import re
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ── Pattern definitions ──
IDENTIFIER_PATTERNS = re.compile(
    r"^(id|.*_id|.*id$|code|key|uuid|ref|reference|account.*num|phone|fax|email)", re.I
)

def is_identifier_column(name: str) -> bool:
    return bool(IDENTIFIER_PATTERNS.match(name))

def filter_feature_columns(X: pd.DataFrame) -> pd.DataFrame:
    """Remove identifier columns by name pattern and constant columns from feature matrix."""
    keep = ~X.columns.to_series().apply(lambda c: bool(IDENTIFIER_PATTERNS.match(c)))
    X = X.loc[:, keep]
    X = X.loc[:, X.nunique() > 1]
    return X
TIME_PATTERNS = re.compile(
    r"^(date|time|timestamp|year|month|day|quarter|period|created_at|updated_at|datetime)", re.I
)
GEO_PATTERNS = re.compile(
    r"^(country|region|city|state|address|zip|postal|latitude|longitude|location|province|territory)", re.I
)
BOOLEAN_PATTERNS = re.compile(
    r"^(is_|has_|flag|active|enabled|disabled|verified|approved|confirmed|completed|paid|sent|delivered)", re.I
)
PERCENTAGE_PATTERNS = re.compile(
    r"(percent|pct|rate|ratio|discount|interest|margin|growth|roi|yield)", re.I
)
CURRENCY_PATTERNS = re.compile(
    r"(price|amount|cost|fee|charge|salary|wage|budget|revenue|income|expense|subscription|payment)", re.I
)


def _infer_category(name: str, nunique: int, nrows: int, 
                    is_numeric: bool, col_data: pd.Series | None = None) -> dict[str, Any]:
    """Classify a column into the 10 required categories."""
    col_lower = name.lower().strip()
    result = {"name": name, "nunique": nunique, "cardinality": "high" if nunique > 50 else "low"}
    
    # 1. Identifier check (pattern-based)
    if IDENTIFIER_PATTERNS.match(col_lower):
        result["category"] = "Identifier"
        return result
    
    # 2. Time check
    if TIME_PATTERNS.match(col_lower):
        result["category"] = "Time"
        return result
    
    # 3. Geographic check
    if GEO_PATTERNS.match(col_lower):
        result["category"] = "Geographic"
        return result
    
    # 4. Boolean check
    if is_numeric and nunique == 2:
        result["category"] = "Boolean"
        return result
    if BOOLEAN_PATTERNS.match(col_lower):
        result["category"] = "Boolean"
        return result
    
    # 5. Percentage check (name-based)
    if PERCENTAGE_PATTERNS.search(col_lower) and is_numeric:
        result["category"] = "Percentage"
        return result
    
    # 6. Currency check (name-based)
    if CURRENCY_PATTERNS.search(col_lower) and is_numeric:
        result["category"] = "Currency"
        return result
    
    # 7-8. Numeric: Continuous vs Discrete
    if is_numeric:
        if nunique <= 20:
            result["category"] = "Discrete Numeric"
        else:
            result["category"] = "Continuous Numeric"
        return result
    
    # 9. Identifier fallback (high cardinality text = likely identifier)
    if nunique == nrows and nrows > 100:
        result["category"] = "Identifier"
        return result
    
    # 10. Text vs Categorical
    if nunique <= 30:
        result["category"] = "Categorical"
    elif nunique <= 100:
        result["category"] = "Categorical"
    else:
        result["category"] = "Text"
    
    return result


def detect_primary_keys(df: pd.DataFrame) -> list[str]:
    """Detect columns that appear to be primary keys (unique + non-null)."""
    pks = []
    for col in df.columns:
        nunique = df[col].nunique()
        non_null = df[col].notna().sum()
        if nunique == non_null and nunique == len(df) and len(df) > 1:
            pks.append(col)
    return pks


def detect_foreign_keys(df: pd.DataFrame, pk_columns: list[str]) -> list[dict]:
    """Detect columns that reference primary keys from other columns."""
    fks = []
    for col in df.columns:
        if col in pk_columns:
            continue
        vals = set(df[col].dropna().unique())
        for pk in pk_columns:
            pk_vals = set(df[pk].dropna().unique())
            if vals == pk_vals:
                fks.append({"column": col, "references": pk, "match_pct": 100.0})
            elif len(vals) > 0 and len(pk_vals) > 0:
                overlap = len(vals & pk_vals) / max(len(vals), len(pk_vals)) * 100
                if overlap > 80:
                    fks.append({"column": col, "references": pk, "match_pct": round(overlap, 1)})
    return fks


def detect_duplicate_identifiers(df: pd.DataFrame, identifier_cols: list[str]) -> list[dict]:
    """Detect identifier columns that contain duplicate values."""
    dupes = []
    for col in identifier_cols:
        if col not in df.columns:
            continue
        dupe_count = int(df[col].duplicated().sum())
        if dupe_count > 0:
            dupes.append({"column": col, "duplicate_count": dupe_count, 
                          "duplicate_pct": round(dupe_count / len(df) * 100, 1) if len(df) > 0 else 0})
    return dupes


def column_intelligence_analysis(df: pd.DataFrame) -> dict[str, Any]:
    """Run full Column Intelligence Engine analysis."""
    nrows, ncols = df.shape
    columns = []
    
    for col in df.columns:
        nunique = int(df[col].nunique())
        is_num = pd.api.types.is_numeric_dtype(df[col])
        info = _infer_category(col, nunique, nrows, is_num, df[col])
        
        # Enrich with stats
        info["missing"] = int(df[col].isna().sum())
        info["missing_pct"] = round(info["missing"] / nrows * 100, 1) if nrows else 0
        info["dtype"] = str(df[col].dtype)
        
        if is_num:
            col_data = df[col].dropna()
            if len(col_data) > 0:
                info["min"] = round(float(col_data.min()), 4)
                info["max"] = round(float(col_data.max()), 4)
                info["mean"] = round(float(col_data.mean()), 4)
                info["std"] = round(float(col_data.std()), 4)
                info["is_skewed"] = abs(col_data.skew()) > 1.5
        
        if nunique == 2 and is_num:
            info["boolean_labels"] = sorted(df[col].unique().tolist())
        
        columns.append(info)
    
    primary_keys = detect_primary_keys(df)
    identifiers = [c for c in columns if c.get("category") == "Identifier"]
    identifier_col_names = [c["name"] for c in identifiers]
    foreign_keys = detect_foreign_keys(df, primary_keys)
    duplicate_ids = detect_duplicate_identifiers(df, identifier_col_names)
    
    # Count by category
    category_counts: dict[str, int] = {}
    for c in columns:
        cat = c.get("category", "Unknown")
        category_counts[cat] = category_counts.get(cat, 0) + 1
    
    return {
        "row_count": nrows,
        "column_count": ncols,
        "columns": columns,
        "primary_keys": primary_keys,
        "foreign_keys": foreign_keys,
        "duplicate_identifiers": duplicate_ids,
        "category_summary": category_counts,
    }
