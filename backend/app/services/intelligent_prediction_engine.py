import logging
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

CLASSIFICATION_KEYWORDS = {
    "churn", "attrition", "fraud", "default", "conversion", "converted",
    "exited", "left", "stopped", "cancelled", "response", "purchased",
    "retained", "survived", "failed", "success", "approved", "rejected",
    "flagged", "complaint", "returned", "subscribed", "click", "signed_up",
    "won", "lost", "qualified", "disqualified",
}
REGRESSION_KEYWORDS = {
    "revenue", "profit", "cost", "sales", "demand", "production", "price",
    "amount", "spend", "quantity", "volume", "hours", "count", "stock",
    "inventory", "rate", "score", "value", "balance", "income", "expense",
    "margin", "growth", "distance", "duration", "time_taken",
}
CLUSTERING_KEYWORDS = {
    "segment", "cluster", "group", "cohort", "tier", "category", "type",
}
ANOMALY_KEYWORDS = {
    "anomaly", "outlier", "fraud", "irregular", "unusual", "suspicious",
    "abnormal", "exception", "intrusion", "spike", "breach",
}
RECOMMENDATION_KEYWORDS = {
    "recommend", "suggest", "preference", "rating", "like", "viewed",
    "purchased", "bought", "clicked", "watched",
}

PROBLEM_MODELS: dict[str, list[str]] = {
    "classification": ["Logistic Regression", "Random Forest", "XGBoost", "LightGBM"],
    "regression": ["Linear Regression", "Ridge", "Random Forest Regressor", "XGBoost Regressor"],
    "time_series": ["Prophet", "ARIMA", "Exponential Smoothing", "XGBoost Time Series"],
    "clustering": ["K-Means", "DBSCAN", "Hierarchical Clustering", "Gaussian Mixture"],
    "anomaly_detection": ["Isolation Forest", "DBSCAN", "LOF", "One-Class SVM"],
    "recommendation": ["Collaborative Filtering", "Matrix Factorization", "ALS", "Neural CF"],
}


def detect_problem(df: pd.DataFrame, target: str | None = None,
                   business_context: str = "") -> dict[str, Any]:
    """
    Automatically detect the prediction problem type.
    No user input required.
    """
    nrows, ncols = df.shape
    all_cols_lower = " ".join(c.lower() for c in df.columns)
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    has_time = any(any(kw in c.lower() for kw in ["date", "time", "timestamp", "year", "month", "quarter", "period"])
                   for c in df.columns)

    # Default result
    result = {
        "suggested_target": target,
        "problem_type": "classification",
        "subtype": "binary",
        "explanation": "",
        "recommended_models": PROBLEM_MODELS["classification"],
        "has_time_column": has_time,
        "row_count": nrows,
        "column_count": ncols,
        "numeric_columns": len(numeric_cols),
    }

    # ── Step 1: Check for time series ──
    if has_time and len(numeric_cols) >= 1:
        if target and any(kw in target.lower() for kw in REGRESSION_KEYWORDS):
            result["problem_type"] = "time_series"
            result["subtype"] = "forecast"
            result["explanation"] = f"'{target}' over time — time series forecasting"
            result["recommended_models"] = PROBLEM_MODELS["time_series"]
            return result
        if not target or target not in df.columns:
            first_num = numeric_cols[0]
            result["suggested_target"] = first_num
            result["problem_type"] = "time_series"
            result["subtype"] = "forecast"
            result["explanation"] = f"Time column detected with numeric '{first_num}' — time series forecasting"
            result["recommended_models"] = PROBLEM_MODELS["time_series"]
            return result

    # ── Step 2: Check for clustering ──
    if any(kw in all_cols_lower for kw in CLUSTERING_KEYWORDS):
        if target and target in df.columns and df[target].nunique() > 5:
            pass  # Not clustering if target has many values
        elif len(numeric_cols) >= 3 and nrows >= 50:
            result["problem_type"] = "clustering"
            result["subtype"] = "unsupervised"
            result["explanation"] = f"{nrows} records with {len(numeric_cols)} numeric features — clustering"
            result["recommended_models"] = PROBLEM_MODELS["clustering"]
            result["suggested_target"] = None
            return result

    # ── Step 3: Check for anomaly detection ──
    if any(kw in all_cols_lower for kw in ANOMALY_KEYWORDS):
        result["problem_type"] = "anomaly_detection"
        result["subtype"] = "unsupervised"
        result["explanation"] = "Anomaly/fraud indicators detected in columns — anomaly detection"
        result["recommended_models"] = PROBLEM_MODELS["anomaly_detection"]
        result["suggested_target"] = None
        return result

    # ── Step 4: Check for recommendation ──
    if any(kw in all_cols_lower for kw in RECOMMENDATION_KEYWORDS):
        if any(c for c in df.columns if "user" in c.lower()) and any(c for c in df.columns if "item" in c.lower() or "product" in c.lower()):
            result["problem_type"] = "recommendation"
            result["subtype"] = "collaborative_filtering"
            result["explanation"] = "User-item interaction data detected — recommendation system"
            result["recommended_models"] = PROBLEM_MODELS["recommendation"]
            result["suggested_target"] = None
            return result

    # ── Step 5: Analyze target variable ──
    if not target or target not in df.columns:
        # Try to detect best target
        target = _detect_best_target(df)
        result["suggested_target"] = target

    if target and target in df.columns:
        col = df[target].dropna()
        nunique = col.nunique()
        is_num = pd.api.types.is_numeric_dtype(col)

        if not is_num or nunique <= 2:
            # Binary or multiclass classification
            result["problem_type"] = "classification"
            result["subtype"] = "binary" if nunique == 2 else "multiclass"
            result["explanation"] = f"'{target}' has {nunique} unique values — {result['subtype']} classification"
            result["recommended_models"] = PROBLEM_MODELS["classification"]
            if nunique <= 2:
                # Also check for anomaly detection
                ratio = col.value_counts().iloc[0] / len(col) if len(col) > 0 else 1
                if ratio > 0.9:
                    result["note"] = "Highly imbalanced — consider anomaly detection or resampling"
        elif is_num:
            if has_time:
                result["problem_type"] = "time_series"
                result["subtype"] = "forecast"
                result["explanation"] = f"'{target}' with time data — time series forecasting"
                result["recommended_models"] = PROBLEM_MODELS["time_series"]
            else:
                result["problem_type"] = "regression"
                result["subtype"] = "continuous"
                result["explanation"] = f"'{target}' is numeric with {nunique} values — regression"
                result["recommended_models"] = PROBLEM_MODELS["regression"]

    return result


def _detect_best_target(df: pd.DataFrame) -> str | None:
    """Detect the best target column from available data."""
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()

    # Priority 1: Binary categorical columns (churn, fraud, etc.)
    for col in cat_cols:
        nunique = df[col].nunique()
        if nunique == 2:
            return col

    # Priority 2: Classification keywords
    for col in cat_cols:
        if any(kw in col.lower() for kw in CLASSIFICATION_KEYWORDS):
            return col

    # Priority 3: Regression keywords
    for col in numeric_cols:
        if any(kw in col.lower() for kw in REGRESSION_KEYWORDS):
            return col

    # Priority 4: Last numeric column
    if numeric_cols:
        return numeric_cols[-1]

    return None


async def run_prediction_detection(doc_id: int) -> dict[str, Any]:
    """Run full prediction type detection pipeline."""
    from app.database.database import get_session_factory
    from app.models.document import Document
    from app.services.business_context_service import detect_industry, detect_dataset_type
    from app.services.dataset_intelligence_service import analyze_dataset
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
    if df is None or len(df.columns) < 2:
        return {"error": "Dataset must be tabular"}

    # Run detection
    ds = analyze_dataset(df)
    target = ds.get("target_variable")
    industry = detect_industry(df)
    dataset_type = detect_dataset_type(df)

    result = detect_problem(df, target, dataset_type)

    return {
        "doc_id": doc_id,
        "industry": industry,
        "dataset_type": dataset_type,
        "prediction": result,
        "columns": {
            "total": len(df.columns),
            "numeric": len(df.select_dtypes(include=["number"]).columns),
            "categorical": len(df.select_dtypes(include=["object", "category"]).columns),
            "target": result.get("suggested_target"),
        },
    }
