import logging
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

logger = logging.getLogger(__name__)


def validate_chart(df: pd.DataFrame, col: str, chart_type: str) -> dict[str, Any]:
    """
    Statistically validate a column before chart rendering.
    Returns validation result with confidence score and rejection reason.
    """
    data = df[col].dropna()
    n = len(data)
    result = {
        "column": col,
        "chart_type": chart_type,
        "valid": True,
        "confidence": 50.0,
        "warnings": [],
        "rejection_reason": None,
    }

    if n < 3:
        result["valid"] = False
        result["rejection_reason"] = "Insufficient data points (< 3)"
        result["confidence"] = 0
        return result

    is_num = pd.api.types.is_numeric_dtype(data)
    missing = int(df[col].isna().sum())
    missing_pct = round(missing / len(df) * 100, 1) if len(df) > 0 else 0

    # ── 1. Correlation validation ──
    if chart_type in ("scatter", "heatmap") and is_num:
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        others = [c for c in numeric_cols if c != col]
        if not others:
            result["valid"] = False
            result["rejection_reason"] = "No paired numeric column for scatter/heatmap"
            result["confidence"] = 0
            return result
        paired = others[0]
        common = df[[col, paired]].dropna()
        if len(common) < 10:
            result["warnings"].append("Correlation: insufficient paired samples (< 10)")
            result["confidence"] -= 15
        else:
            r, p = scipy_stats.pearsonr(common[col], common[paired])
            if abs(r) < 0.1:
                result["warnings"].append(f"Correlation: very weak relationship (r={r:.3f})")
                result["confidence"] -= 10
            elif abs(r) >= 0.7:
                result["confidence"] += 15
            if p > 0.05:
                result["warnings"].append(f"Correlation: not statistically significant (p={p:.4f})")
                result["confidence"] -= 10

    # ── 2. Distribution analysis ──
    if chart_type in ("histogram", "box") and is_num:
        if len(data) < 5:
            result["warnings"].append("Distribution: small sample size (< 5)")
            result["confidence"] -= 15
        else:
            skew = abs(data.skew())
            if skew > 2:
                result["warnings"].append(f"Distribution: highly skewed (skew={skew:.2f})")
                result["confidence"] -= 10
            elif skew < 0.5:
                result["confidence"] += 5

            # Check for bimodality (Hartigan's dip test approximation)
            from scipy.stats import gaussian_kde
            try:
                kde = gaussian_kde(data)
                x_grid = np.linspace(data.min(), data.max(), 50)
                y = kde(x_grid)
                peaks = sum(1 for i in range(1, len(y) - 1) if y[i] > y[i - 1] and y[i] > y[i + 1])
                if peaks > 1:
                    result["warnings"].append(f"Distribution: bimodal/multimodal ({peaks} peaks detected)")
            except Exception:
                pass

    # ── 3. Outlier detection ──
    if is_num:
        q1, q3 = data.quantile(0.25), data.quantile(0.75)
        iqr = q3 - q1
        outlier_mask = (data < (q1 - 1.5 * iqr)) | (data > (q3 + 1.5 * iqr))
        outlier_count = int(outlier_mask.sum())
        outlier_pct = round(outlier_count / n * 100, 1) if n else 0

        if outlier_pct > 20:
            result["warnings"].append(f"Outliers: {outlier_pct}% values are outliers — chart may be misleading")
            result["confidence"] -= 20
        elif outlier_pct > 10:
            result["warnings"].append(f"Outliers: {outlier_pct}% outliers detected")
            result["confidence"] -= 10
        elif outlier_pct > 0:
            result["confidence"] += 5

    # ── 4. Missing value analysis ──
    if missing_pct > 50:
        result["warnings"].append(f"Missing data: {missing_pct}% missing — chart may be unreliable")
        result["valid"] = False
        result["rejection_reason"] = f"Excessive missing data ({missing_pct}%)"
        result["confidence"] = 0
        return result
    elif missing_pct > 20:
        result["warnings"].append(f"Missing data: {missing_pct}% missing")
        result["confidence"] -= 15
    elif missing_pct > 5:
        result["confidence"] -= 5

    # ── 5. Normality testing ──
    if chart_type in ("box", "histogram") and is_num and n >= 8:
        try:
            _, p_norm = scipy_stats.shapiro(data.sample(min(5000, n)))
            if p_norm < 0.05:
                result["warnings"].append(f"Normality: data is non-normal (Shapiro p={p_norm:.4f})")
            else:
                result["confidence"] += 5
        except Exception:
            pass

    # ── 6. Time series validation ──
    if chart_type in ("line", "area"):
        date_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
        if not date_cols:
            result["warnings"].append("Time series: no datetime column found — using row index")
            result["confidence"] -= 10

        if n < 5:
            result["warnings"].append("Time series: insufficient time points (< 5)")
            result["confidence"] -= 15
        elif n < 10:
            result["confidence"] -= 5
        else:
            result["confidence"] += 10

        # Check for regular intervals
        if date_cols:
            try:
                deltas = df[date_cols[0]].dropna().diff().dropna()
                if len(deltas) > 1:
                    cv = deltas.std().total_seconds() / deltas.mean().total_seconds() if deltas.mean().total_seconds() > 0 else 99
                    if cv > 0.5:
                        result["warnings"].append(f"Time series: irregular intervals (CV={cv:.2f})")
                        result["confidence"] -= 5
            except Exception:
                pass

    # ── 7. Categorical validation ──
    if chart_type in ("bar", "pie"):
        nunique = data.nunique()
        if nunique > 30:
            result["warnings"].append(f"Categorical: too many categories ({nunique}) — chart may be cluttered")
            result["confidence"] -= 15
        elif nunique == 1:
            result["valid"] = False
            result["rejection_reason"] = "Constant column — no variation to display"
            result["confidence"] = 0
            return result
        elif nunique <= 10:
            result["confidence"] += 10

        # Check for highly imbalanced categories
        if nunique > 1 and nunique <= 20:
            counts = data.value_counts()
            top_pct = counts.iloc[0] / n * 100
            if top_pct > 95:
                result["warnings"].append(f"Categorical: highly imbalanced (top category = {top_pct:.0f}%)")
                result["confidence"] -= 10

    # ── Final confidence calculation ──
    result["confidence"] = round(max(0, min(100, result["confidence"])), 1)

    # Reject low-confidence charts
    if result["confidence"] < 20 and result["valid"]:
        result["valid"] = False
        result["rejection_reason"] = f"Statistical confidence too low ({result['confidence']}%)"

    return result


async def validate_all_charts(df: pd.DataFrame, charts: list[dict]) -> dict[str, Any]:
    """
    Validate all pending chart visualizations.
    Returns validated charts and a summary.
    """
    validated = []
    rejected = []

    for chart in charts:
        col = chart.get("column", "")
        chart_type = chart.get("chart_type", "")
        if col not in df.columns:
            rejected.append({**chart, "valid": False, "rejection_reason": "Column not found"})
            continue

        validation = validate_chart(df, col, chart_type)
        if validation["valid"]:
            chart["validation"] = validation
            chart["confidence"] = validation["confidence"]
            validated.append(chart)
        else:
            chart["valid"] = False
            chart["rejection_reason"] = validation["rejection_reason"]
            chart["validation"] = validation
            rejected.append(chart)

    avg_confidence = round(sum(c.get("confidence", 0) for c in validated) / len(validated), 1) if validated else 0

    return {
        "total_submitted": len(charts),
        "validated": len(validated),
        "rejected": len(rejected),
        "average_confidence": avg_confidence,
        "charts": validated,
        "rejected_charts": rejected,
    }
