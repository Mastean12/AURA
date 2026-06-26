import logging
import warnings
from typing import Any

import numpy as np
import pandas as pd

from app.services.data_quality_service import run_data_quality_audit

logger = logging.getLogger(__name__)


def _safe_stat(col_data: pd.Series, func, default=0.0):
    try:
        return float(func(col_data))
    except Exception:
        return default


def compute_normality(col_data: pd.Series) -> dict:
    """Shapiro-Wilk inspired normality test using skewness and kurtosis."""
    n = len(col_data)
    if n < 8:
        return {"is_normal": None, "p_value": None, "reason": "Insufficient sample size (< 8)"}
    skew = _safe_stat(col_data, lambda x: x.skew())
    kurt = _safe_stat(col_data, lambda x: x.kurtosis())
    # If skewness is between -2 and 2 and kurtosis between -7 and 7, roughly normal
    is_normal = bool(abs(skew) < 2 and abs(kurt) < 7)
    return {"is_normal": is_normal, "skewness": round(float(skew), 3), "kurtosis": round(float(kurt), 3),
            "reason": "Approximately normal" if is_normal else "Non-normal distribution detected"}


def compute_confidence_interval(col_data: pd.Series, confidence: float = 0.95) -> dict:
    """Compute confidence interval for the mean."""
    n = len(col_data)
    if n < 2:
        return {"lower": None, "upper": None, "mean": None, "margin": None}
    from scipy.stats import t
    mean = float(col_data.mean())
    se = float(col_data.std() / float(np.sqrt(n)))
    alpha = 1.0 - confidence
    t_crit = float(t.ppf(1.0 - alpha / 2.0, n - 1))
    margin = float(t_crit * se)
    return {"lower": round(mean - margin, 4), "upper": round(mean + margin, 4),
            "mean": round(mean, 4), "margin": round(margin, 4), "confidence": float(confidence)}


def compute_anova(df: pd.DataFrame, numeric_col: str, cat_col: str) -> dict:
    """One-way ANOVA: test if a numeric column differs across categories."""
    from scipy.stats import f_oneway
    groups = [g.dropna().values for _, g in df.groupby(cat_col)[numeric_col] if len(g.dropna()) >= 5]
    if len(groups) < 2:
        return {"test": "ANOVA", "statistic": None, "p_value": None, "reason": "Need 2+ groups with 5+ samples"}
    try:
        f_stat, p_val = f_oneway(*groups)
        sig = bool(p_val < 0.05)
        return {"test": "ANOVA", "statistic": round(float(f_stat), 4), "p_value": round(float(p_val), 6),
                "significant": sig, "groups": len(groups),
                "interpretation": f"Numeric column '{numeric_col}' differs significantly across '{cat_col}' categories" if sig else f"No significant difference in '{numeric_col}' across '{cat_col}'"}
    except Exception as e:
        return {"test": "ANOVA", "error": str(e)}


def compute_chi_square(df: pd.DataFrame, col_a: str, col_b: str) -> dict:
    """Chi-square test of independence between two categorical columns."""
    from scipy.stats import chi2_contingency
    ct = pd.crosstab(df[col_a], df[col_b])
    if ct.size == 0:
        return {"test": "Chi-Square", "statistic": None, "p_value": None, "reason": "Empty contingency table"}
    try:
        chi2, p_val, dof, expected = chi2_contingency(ct)
        sig = bool(p_val < 0.05)
        return {"test": "Chi-Square", "statistic": round(float(chi2), 4), "p_value": round(float(p_val), 6),
                "dof": int(dof), "significant": sig,
                "interpretation": f"'{col_a}' and '{col_b}' are significantly related" if sig else f"No significant relationship between '{col_a}' and '{col_b}'"}
    except Exception as e:
        return {"test": "Chi-Square", "error": str(e)}


def compute_pca(df: pd.DataFrame, n_components: int = 3) -> dict:
    """Principal Component Analysis for dimensionality insight."""
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler
    numeric = df.select_dtypes(include=["number"]).dropna(how="all", axis=1).dropna()
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
