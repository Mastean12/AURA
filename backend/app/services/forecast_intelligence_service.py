import logging

import numpy as np
import pandas as pd

from app.services.dataset_intelligence_service import analyze_dataset

logger = logging.getLogger(__name__)


def check_forecast_eligibility(df: pd.DataFrame) -> dict:
    """Verify the dataset is suitable for forecasting before proceeding."""
    ds = analyze_dataset(df)
    eligibility = {"eligible": False, "reasons": [], "target": None, "time_column": None}

    date_cols = ds.get("date_columns", [])
    kpi_cols = ds.get("kpi_columns", [])
    numeric_cols = ds.get("numeric_columns", [])

    if not date_cols:
        eligibility["reasons"].append("No time/date column found — forecasting requires a time dimension")
    else:
        eligibility["time_column"] = date_cols[0]
        # Check if the date column has enough unique values
        if df[date_cols[0]].nunique() < 3:
            eligibility["reasons"].append(f"Date column '{date_cols[0]}' has only {df[date_cols[0]].nunique()} unique values — need at least 3")

    if not kpi_cols and not numeric_cols:
        eligibility["reasons"].append("No numeric KPI or target column found for forecasting")
    else:
        target = kpi_cols[0] if kpi_cols else numeric_cols[0]
        eligibility["target"] = target
        vals = df[target].dropna()
        if len(vals) < 5:
            eligibility["reasons"].append(f"Target '{target}' has only {len(vals)} non-null values — minimum 5 required")

        # Check for constant values
        if vals.nunique() == 1:
            eligibility["reasons"].append(f"Target '{target}' is constant — cannot forecast")

        # Check for too much missing data
        missing_pct = int(df[target].isna().sum()) / max(len(df), 1) * 100
        if missing_pct > 50:
            eligibility["reasons"].append(f"Target '{target}' has {missing_pct:.0f}% missing values")

    id_cols = ds.get("identifier_columns", [])
    if eligibility["target"] and eligibility["target"] in id_cols:
        eligibility["reasons"].append(f"Target '{eligibility['target']}' is an identifier column — rejected")
        eligibility["target"] = None

    if not eligibility["reasons"]:
        eligibility["eligible"] = True

    return eligibility


def select_forecast_model(df: pd.DataFrame, target: str, time_col: str) -> dict:
    """Automatically select the best forecasting model based on data characteristics."""
    vals = df[target].dropna()
    n = len(vals)

    if n < 10:
        return {"model": "moving_average", "reason": "Small sample — using moving average",
                "complexity": "low", "suitable": True}

    # Check for seasonality using autocorrelation
    autocorr = None
    if n >= 14:
        try:
            autocorr = np.corrcoef(vals[:-7], vals[7:])[0, 1] if n > 7 else 0
        except Exception:
            autocorr = 0

    has_seasonality = autocorr is not None and abs(autocorr) > 0.3

    if has_seasonality and n >= 30:
        return {"model": "seasonal_naive", "reason": "Seasonal pattern detected — using seasonal model",
                "seasonal_period": 7, "complexity": "medium", "suitable": True}

    # Check trend direction
    x = np.arange(n)
    slope, _ = np.polyfit(x, vals.values, 1)
    trend_strength = abs(slope) * n / vals.mean() if vals.mean() > 0 else 0

    if trend_strength > 0.1 and n >= 15:
        return {"model": "linear_regression", "reason": "Strong linear trend detected",
                "complexity": "medium", "suitable": True}

    if n >= 10:
        return {"model": "exponential_smoothing", "reason": "General purpose — stable pattern",
                "complexity": "medium", "suitable": True}

    return {"model": "moving_average", "reason": "Fallback — insufficient data for complex models",
            "complexity": "low", "suitable": True}


def validate_forecast(actual: np.ndarray, predicted: np.ndarray) -> dict:
    """Validate forecast quality with standard metrics."""
    if len(actual) != len(predicted) or len(actual) == 0:
        return {"valid": False, "reason": "Empty or mismatched arrays"}

    residuals = actual - predicted
    mse = np.mean(residuals ** 2)
    rmse = np.sqrt(mse)
    mae = np.mean(np.abs(residuals))
    mape = np.mean(np.abs(residuals / (actual + 1e-10))) * 100
    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((actual - np.mean(actual)) ** 2)
    r2 = 1 - (ss_res / (ss_tot + 1e-10))

    return {
        "valid": True,
        "r2": round(float(r2), 4),
        "rmse": round(float(rmse), 4),
        "mae": round(float(mae), 4),
        "mape": round(float(mape), 2),
        "quality": "excellent" if r2 > 0.9 else "good" if r2 > 0.7 else "moderate" if r2 > 0.5 else "poor",
    }


def explain_forecast(trend_direction: str, trend_strength: float, confidence: float,
                     target: str, periods: int, model: str) -> str:
    """Generate a business-friendly explanation of the forecast."""
    direction_word = "increase" if trend_direction == "up" else "decrease" if trend_direction == "down" else "remain stable"
    confidence_word = "high confidence" if confidence > 0.8 else "moderate confidence" if confidence > 0.5 else "low confidence"

    return (
        f"{target} is projected to {direction_word} over the next {periods} periods "
        f"({confidence_word}). "
        f"Forecast generated using {model} model with trend strength of {trend_strength:.0%}. "
        f"Drivers include current momentum and historical patterns in the data."
    )
