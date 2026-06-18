import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def _iqr_outliers(series: pd.Series) -> int:
    q1, q3 = series.quantile(0.25), series.quantile(0.75)
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    return int(((series < lower) | (series > upper)).sum())


def _zscore_outliers(series: pd.Series) -> int:
    z = np.abs((series - series.mean()) / series.std())
    return int((z > 3).sum())


def run_data_quality_audit(df: pd.DataFrame) -> dict:
    nrows, ncols = df.shape
    total_cells = nrows * ncols

    issues = []
    missing_total = int(df.isna().sum().sum())
    missing_pct = round(missing_total / total_cells * 100, 2) if total_cells else 0

    if missing_total > 0:
        for col in df.columns:
            m = int(df[col].isna().sum())
            if m > 0:
                pct = round(m / nrows * 100, 1)
                issues.append({"type": "missing", "column": col, "count": m, "pct": pct,
                               "suggestion": "Impute with median (numeric) or mode (categorical) "
                               if pd.api.types.is_numeric_dtype(df[col]) else "Impute with mode"})

    duplicates = int(df.duplicated().sum())
    if duplicates > 0:
        issues.append({"type": "duplicates", "count": duplicates, "pct": round(duplicates / nrows * 100, 1),
                       "suggestion": f"Remove {duplicates} duplicate row(s)" if duplicates < 50
                       else "Investigate source of duplication"})

    constant_cols = [col for col in df.columns if df[col].nunique() == 1]
    for col in constant_cols:
        issues.append({"type": "constant_column", "column": col,
                       "suggestion": "Consider dropping — no variance"})

    null_cols = [col for col in df.columns if df[col].isna().all()]
    for col in null_cols:
        issues.append({"type": "null_column", "column": col,
                       "suggestion": "Drop column — entirely null"})

    for col in df.select_dtypes(include=["number"]).columns:
        col_data = df[col].dropna()
        if len(col_data) < 10:
            continue
        iqr_out = _iqr_outliers(col_data)
        z_out = _zscore_outliers(col_data)
        total_out = max(iqr_out, z_out)
        if total_out > 0 and total_out / len(col_data) > 0.01:
            issues.append({"type": "outliers", "column": col, "count": total_out,
                           "pct": round(total_out / len(col_data) * 100, 1),
                           "suggestion": f"Consider winsorizing or investigating {total_out} outlier(s)"})

    for col in df.select_dtypes(include=["object"]).columns:
        if df[col].nunique() > 50:
            continue
        vals = df[col].dropna().astype(str).str.strip().str.lower()
        unique_vals = vals.unique()
        if len(unique_vals) < len(vals):
            fuzzy = vals.value_counts()
            if len(fuzzy) < df[col].nunique():
                issues.append({"type": "inconsistent_categories", "column": col,
                               "suggestion": "Standardize category names (e.g., 'yes' vs 'Yes')"})

    # Quality scores
    completeness = round(100 - missing_pct, 1)
    uniqueness = round(100 - (duplicates / nrows * 100) if nrows else 100, 1)
    consistency = 100 - min(len([i for i in issues if i["type"] in ("inconsistent_categories", "constant_column", "null_column")]) * 5, 100)
    validity = 100 - min(len([i for i in issues if i["type"] in ("outliers", "invalid_types")]) * 3, 100)
    integrity = 100 - min((missing_pct + (duplicates / nrows * 100)) / 2, 100)

    overall = round((completeness + uniqueness + consistency + validity + integrity) / 5, 1)
    overall = max(0, min(100, overall))

    return {
        "overall_score": overall,
        "completeness": completeness,
        "uniqueness": uniqueness,
        "consistency": consistency,
        "validity": validity,
        "integrity": integrity,
        "total_rows": nrows,
        "total_columns": ncols,
        "missing_cells": missing_total,
        "missing_pct": missing_pct,
        "duplicate_rows": duplicates,
        "constant_columns": constant_cols,
        "null_columns": null_cols,
        "issues": issues,
        "issues_count": len(issues),
        "grade": "Excellent" if overall >= 90 else "Good" if overall >= 75 else "Fair" if overall >= 60 else "Poor",
    }
