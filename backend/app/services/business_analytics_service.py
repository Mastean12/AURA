import logging

import numpy as np
import pandas as pd

from app.services.dataset_intelligence_service import analyze_dataset, classify_column

logger = logging.getLogger(__name__)

EXECUTIVE_QUESTIONS = {
    "Sales Analytics": [
        "Which products drive the most revenue?",
        "Which regions are underperforming?",
        "What is the revenue trend?",
        "Which customer segments are most valuable?",
        "Where should sales investment increase?",
    ],
    "Finance Analytics": [
        "What is driving costs?",
        "Are we on track for revenue targets?",
        "Where can we reduce expenses?",
        "What is the profitability trend?",
        "What financial risks exist?",
    ],
    "HR Analytics": [
        "What is driving employee turnover?",
        "Which departments have highest attrition?",
        "How effective is our hiring?",
        "What is the promotion trend?",
        "Where should we improve retention?",
    ],
    "Customer Analytics": [
        "Why are customers leaving?",
        "Which customers are most at risk?",
        "What revenue is being lost?",
        "Which factors drive churn?",
        "What is the customer lifetime value trend?",
    ],
}

EXCLUDE_FROM_CHARTS = {"identifier", "date", "text", "geographic"}


def select_charts(df: pd.DataFrame, dataset_info: dict) -> list[dict]:
    """Intelligently select which charts to generate based on column types."""
    charts = []
    columns = dataset_info.get("columns", [])

    for col_info in columns:
        col = col_info["name"]
        cls = col_info.get("classification", "")
        dtype = col_info.get("dtype", "")

        if cls in EXCLUDE_FROM_CHARTS or cls == "identifier":
            continue

        chart_set = {"column": col, "classification": cls, "reason": "", "charts": []}

        if dtype == "numeric":
            chart_set["reason"] = "Distribution and trend analysis for KPI monitoring"
            chart_set["charts"] = ["histogram", "boxplot", "trend"]

            if col_info.get("is_target"):
                chart_set["charts"].extend(["correlation"])

        elif cls == "categorical":
            chart_set["reason"] = "Frequency and segmentation analysis"
            chart_set["charts"] = ["bar", "pie"]

        elif cls == "date":
            chart_set["reason"] = "Time series and trend analysis"
            chart_set["charts"] = ["line", "area"]

        elif cls == "geographic":
            chart_set["reason"] = "Geographic distribution"
            chart_set["charts"] = ["bar"]

        if chart_set["charts"]:
            charts.append(chart_set)

    return charts


def generate_business_questions(dataset_type: str, key_columns: list[str]) -> list[str]:
    """Auto-generate business questions executives care about."""
    questions = EXECUTIVE_QUESTIONS.get(dataset_type, [])
    if not questions:
        questions = [
            f"What are the key trends in {', '.join(key_columns[:3])}?",
            "What are the biggest risks?",
            "What opportunities exist for growth?",
            "What actions should management take?",
        ]
    return questions


def compute_descriptive_stats(df: pd.DataFrame) -> dict:
    """Compute descriptive statistics for all numeric columns."""
    numeric = df.select_dtypes(include=["number"])
    if numeric.empty:
        return {}
    stats = numeric.describe(percentiles=[0.25, 0.5, 0.75, 0.9, 0.95]).to_dict()
    result = {}
    for col in numeric.columns:
        col_data = numeric[col].dropna()
        result[col] = {
            "mean": round(float(col_data.mean()), 2),
            "median": round(float(col_data.median()), 2),
            "mode": float(col_data.mode().iloc[0]) if not col_data.mode().empty else None,
            "std": round(float(col_data.std()), 2),
            "variance": round(float(col_data.var()), 2),
            "min": float(col_data.min()),
            "max": float(col_data.max()),
            "range": float(col_data.max() - col_data.min()),
            "q1": float(col_data.quantile(0.25)),
            "q3": float(col_data.quantile(0.75)),
            "iqr": float(col_data.quantile(0.75) - col_data.quantile(0.25)),
            "skewness": round(float(col_data.skew()), 3),
            "kurtosis": round(float(col_data.kurtosis()), 3),
            "missing": int(df[col].isna().sum()),
            "missing_pct": round(int(df[col].isna().sum()) / len(df) * 100, 1),
        }
    return {"stats": result, "numeric_count": len(numeric.columns)}


def compute_correlations(df: pd.DataFrame) -> dict:
    """Compute correlation matrix for numeric columns."""
    numeric = df.select_dtypes(include=["number"]).dropna(axis=1, how="all")
    if numeric.shape[1] < 2:
        return {"correlations": {}}
    corr = numeric.corr().round(3)
    strong_pairs = []
    for i in range(len(corr.columns)):
        for j in range(i + 1, len(corr.columns)):
            val = corr.iloc[i, j]
            if abs(val) >= 0.5:
                strong_pairs.append({
                    "col_a": corr.columns[i], "col_b": corr.columns[j],
                    "correlation": float(val), "direction": "positive" if val > 0 else "negative",
                    "strength": "strong" if abs(val) >= 0.7 else "moderate",
                })
    return {
        "matrix": corr.to_dict(),
        "strong_correlations": sorted(strong_pairs, key=lambda x: abs(x["correlation"]), reverse=True),
    }


def segment_analysis(df: pd.DataFrame, dataset_info: dict) -> dict:
    """Compare top vs bottom performers for key KPIs."""
    kpi_cols = dataset_info.get("kpi_columns", [])
    cat_cols = dataset_info.get("categorical_columns", [])
    if not kpi_cols or not cat_cols:
        return {}
    segments = []
    for kpi in kpi_cols[:2]:
        for cat in cat_cols[:3]:
            if df[cat].nunique() > 20:
                continue
            grouped = df.groupby(cat)[kpi].agg(["mean", "sum", "count"]).round(2)
            grouped.columns = [f"{kpi}_{c}" for c in grouped.columns]
            segments.append({
                "segment_column": cat,
                "kpi": kpi,
                "top": grouped.head(3).to_dict(orient="index") if not grouped.empty else {},
                "bottom": grouped.tail(3).to_dict(orient="index") if len(grouped) > 3 else {},
            })
    return {"segments": segments}


def run_business_analytics(df: pd.DataFrame) -> dict:
    """Run full Business Analytics Engine."""
    dataset_info = analyze_dataset(df)
    charts = select_charts(df, dataset_info)
    questions = generate_business_questions(dataset_info["dataset_type"],
                                            dataset_info.get("kpi_columns", []) or dataset_info.get("numeric_columns", []))
    stats = compute_descriptive_stats(df)
    correlations = compute_correlations(df)
    segments = segment_analysis(df, dataset_info)

    return {
        "dataset_info": dataset_info,
        "charts": charts,
        "business_questions": questions,
        "descriptive_stats": stats,
        "correlations": correlations,
        "segments": segments,
        "analysis_ready": True,
    }
