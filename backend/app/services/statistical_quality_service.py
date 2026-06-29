import logging
import warnings
from typing import Any

import numpy as np
import pandas as pd

import scipy.cluster.hierarchy as sch
from scipy.stats import pearsonr
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

from app.services.column_intelligence_service import filter_feature_columns


def compute_pca(df: pd.DataFrame, n_components: int = 3) -> dict:
    """Principal Component Analysis for dimensionality insight."""
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler
    numeric = df.select_dtypes(include=["number"]).dropna(how="all", axis=1).dropna()
    numeric = filter_feature_columns(numeric)
    if numeric.shape[1] < 3 or numeric.shape[0] < 10:
        return {"error": "Need 3+ numeric columns and 10+ rows for PCA"}
    cols = numeric.columns[:min(15, numeric.shape[1])].tolist()
    X = numeric[cols].values
    try:
        X_scaled = StandardScaler().fit_transform(X)
        pca = PCA().fit(X_scaled)
        var_ratio = pca.explained_variance_ratio_.tolist()
        cumulative = np.cumsum(var_ratio).tolist()
        n_for_80 = next((i + 1 for i, v in enumerate(cumulative) if v >= 0.8), len(var_ratio))
        top_features = {}
        for i in range(min(2, len(cols))):
            loadings = np.abs(pca.components_[i])
            top_idx = np.argsort(loadings)[-3:][::-1]
            top_features[f"PC{i+1}"] = [cols[j] for j in top_idx]
        return {
            "explained_variance_ratio": [round(v, 4) for v in var_ratio[:n_components]],
            "cumulative_variance": [round(v, 4) for v in cumulative[:n_components]],
            "components_for_80pct": n_for_80,
            "total_components": len(var_ratio),
            "top_features_per_component": top_features,
        }
    except Exception as e:
        return {"error": str(e)}


def feature_engineering_suggestions(df: pd.DataFrame, target: str = "") -> list[dict]:
    """Generate suggestions for feature engineering based on data patterns."""
    suggestions = []
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()

    for col in numeric_cols:
        col_data = df[col].dropna()
        if len(col_data) < 10:
            continue
        # Check for skewness
        skew = _safe_stat(col_data, lambda x: x.skew())
        if abs(skew) > 1.5:
            suggestions.append({
                "column": col, "type": "transformation",
                "suggestion": f"Apply log or Box-Cox transformation (skewness={skew:.2f})",
                "expected_benefit": "Normalize distribution, improve model performance",
                "priority": "high" if abs(skew) > 3 else "medium",
            })
        # Check for outliers
        q1, q3 = col_data.quantile(0.25), col_data.quantile(0.75)
        iqr = q3 - q1
        outlier_count = int(((col_data < (q1 - 1.5 * iqr)) | (col_data > (q3 + 1.5 * iqr))).sum())
        if outlier_count > 0 and outlier_count / len(col_data) > 0.02:
            suggestions.append({
                "column": col, "type": "outlier_treatment",
                "suggestion": f"Winsorize or cap {outlier_count} outliers ({outlier_count/len(col_data)*100:.1f}%)",
                "expected_benefit": "Reduce influence of extreme values",
                "priority": "medium",
            })

    # Date feature extraction
    for col in df.select_dtypes(include=["datetime64", "datetime"]).columns:
        suggestions.append({
            "column": col, "type": "feature_extraction",
            "suggestion": f"Extract year, month, day, weekday, quarter from '{col}'",
            "expected_benefit": "Create time-based features for trend analysis",
            "priority": "medium",
        })

    # Interaction features suggestion
    if len(numeric_cols) >= 3:
        from app.services.business_analytics_service import compute_correlations
        corr_result = compute_correlations(df)
        strong_pairs = corr_result.get("strong_correlations", [])
        if strong_pairs:
            top = strong_pairs[0]
            suggestions.append({
                "column": f"{top['col_a']} x {top['col_b']}", "type": "interaction",
                "suggestion": f"Create ratio or interaction feature: {top['col_a']} / {top['col_b']}",
                "expected_benefit": f"Capture combined effect (correlation={top['correlation']})",
                "priority": "low",
            })

    return suggestions[:10]


def compute_statistical_confidence(dq_score: float, n_rows: int, n_cols: int, normality_count: int, total_tested: int) -> dict:
    """Compute overall statistical confidence score (0-100)."""
    data_quality_weight = min(dq_score / 100, 1) * 0.30
    sample_size_weight = min(n_rows / 1000, 1) * 0.25
    feature_count_weight = min(n_cols / 20, 1) * 0.15
    normality_weight = (normality_count / max(total_tested, 1)) * 0.15
    completeness_weight = 0.15

    score = round((data_quality_weight + sample_size_weight + feature_count_weight + normality_weight + completeness_weight) * 100, 1)
    score = max(0, min(100, score))
    grade = "Excellent" if score >= 80 else "Good" if score >= 60 else "Moderate" if score >= 40 else "Poor"
    return {"score": score, "grade": grade, "sample_size_adequate": bool(n_rows >= 100), "feature_count_adequate": bool(n_cols >= 3)}


async def run_full_quality_analysis(doc_id: int, df: pd.DataFrame) -> dict[str, Any]:
    """Run complete data quality + statistical analysis pipeline."""
    dq = run_data_quality_audit(df)
    normality_results = {}
    anova_results = []
    chi2_results = []

    for col in df.select_dtypes(include=["number"]).columns:
        col_data = df[col].dropna()
        if len(col_data) >= 8:
            normality_results[col] = compute_normality(col_data)

    # ANOVA: test numeric columns against categorical with <=10 categories
    numeric = df.select_dtypes(include=["number"]).columns[:5]
    categorical = [c for c in df.select_dtypes(include=["object", "category"]).columns if df[c].nunique() <= 10][:3]
    for n_col in numeric[:3]:
        for c_col in categorical:
            result = compute_anova(df, n_col, c_col)
            if result.get("p_value") is not None:
                anova_results.append(result)

    # Chi-Square: pairwise categorical tests
    cat_cols = [c for c in df.select_dtypes(include=["object", "category"]).columns if df[c].nunique() <= 10][:5]
    for i in range(len(cat_cols)):
        for j in range(i + 1, len(cat_cols)):
            result = compute_chi_square(df, cat_cols[i], cat_cols[j])
            if result.get("p_value") is not None:
                chi2_results.append(result)

    # PCA
    pca = compute_pca(df)

    # Feature engineering suggestions
    fe_suggestions = feature_engineering_suggestions(df)

    # Statistical confidence
    normal_count = sum(1 for v in normality_results.values() if v.get("is_normal"))
    conf = compute_statistical_confidence(dq["overall_score"], len(df), len(df.columns), normal_count, len(normality_results))

    return {
        "data_quality": dq,
        "statistical_confidence": conf,
        "normality": normality_results,
        "anova": anova_results[:5],
        "chi_square": chi2_results[:5],
        "pca": pca,
        "feature_engineering_suggestions": fe_suggestions,
        "doc_id": doc_id,
    }
