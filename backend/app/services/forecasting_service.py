import io
import logging
import math

import numpy as np
import pandas as pd

from app.database.database import get_session_factory
from app.models.document import Document
from app.services.ai_service import generate_response_async
from sqlalchemy import select

logger = logging.getLogger(__name__)


def _linear_regression(x: np.ndarray, y: np.ndarray) -> tuple[float, float, float]:
    n = len(x)
    x_mean = np.mean(x)
    y_mean = np.mean(y)
    numerator = np.sum((x - x_mean) * (y - y_mean))
    denominator = np.sum((x - x_mean) ** 2)
    slope = numerator / denominator if denominator != 0 else 0
    intercept = y_mean - slope * x_mean
    y_pred = slope * x + intercept
    residuals = y - y_pred
    mse = np.mean(residuals ** 2)
    rmse = math.sqrt(mse) if mse > 0 else 0
    return slope, intercept, rmse


def _detect_seasonality(values: np.ndarray) -> tuple[int, float]:
    n = len(values)
    if n < 14:
        return 1, 0
    best_period = 1
    best_strength = 0
    for period in [7, 12, 30]:
        if n < period * 2:
            continue
        autocov = np.corrcoef(values[:-period], values[period:])[0, 1]
        strength = abs(autocov) if not np.isnan(autocov) else 0
        if strength > best_strength:
            best_strength = strength
            best_period = period
    return best_period, best_strength


def _generate_historical_points(values: np.ndarray, column: str, start_index: int = 0) -> list[dict]:
    points = []
    for i, v in enumerate(values):
        points.append({
            "date": f"Day {start_index + i + 1}",
            "value": round(float(v), 2),
            "lower_bound": round(float(v), 2),
            "upper_bound": round(float(v), 2),
        })
    return points


async def generate_forecast(doc_id: int, column: str, periods: int = 30) -> dict:
    logger.info("Generating forecast for doc_id=%d, column=%s, periods=%d", doc_id, column, periods)
    try:
        async with get_session_factory()() as db:
            result = await db.execute(select(Document).where(Document.id == doc_id))
            doc = result.scalar_one_or_none()
    except Exception as e:
        logger.warning("DB error: %s", e)
        return _empty_forecast(column)

    if not doc or not doc.content:
        return _empty_forecast(column)

    df = pd.read_csv(io.StringIO(doc.content)) if doc.content.count(",") > 5 else None
    if df is None or column not in df.columns:
        return _empty_forecast(column)

    values = df[column].dropna().values.astype(float)
    if len(values) < 3:
        return _empty_forecast(column)

    x = np.arange(len(values))
    slope, intercept, rmse = _linear_regression(x, values)
    season_period, season_strength = _detect_seasonality(values)

    future_x = np.arange(len(values), len(values) + periods)
    trend_forecast = slope * future_x + intercept

    if season_period > 1 and season_strength > 0.3:
        seasonal_components = []
        for i in range(periods):
            idx = (len(values) - season_period + i) % season_period
            seasonal_components.append(float(values[idx] - (slope * idx + intercept)))
        seasonal = np.array(seasonal_components)
    else:
        seasonal = np.zeros(periods)

    raw_forecast = trend_forecast + seasonal
    confidence_mult = 1.96
    ci = confidence_mult * rmse * (1 + np.linspace(0.1, 0.3, periods))
    lower_bounds = raw_forecast - ci
    upper_bounds = raw_forecast + ci

    historical = _generate_historical_points(values, column)

    forecast_points = []
    for i in range(periods):
        forecast_points.append({
            "date": f"Day {len(values) + i + 1}",
            "value": round(float(raw_forecast[i]), 2),
            "lower_bound": round(float(max(lower_bounds[i], 0)), 2),
            "upper_bound": round(float(upper_bounds[i]), 2),
        })

    trend_direction = "up" if slope > 0 else "down" if slope < 0 else "stable"
    trend_strength = round(min(abs(slope) * 10, 1), 2)
    confidence_avg = round(max(0, min(1, 1 - (rmse / (np.mean(values) + 1e-10)))), 2)

    # Validation metrics
    from app.services.forecast_intelligence_service import validate_forecast, explain_forecast
    validation = validate_forecast(values, slope * np.arange(len(values)) + intercept)

    explanation_prompt = (
        f"The dataset column '{column}' shows a {trend_direction} trend with {trend_strength*100:.0f}% strength. "
        f"Historical data has {len(values)} points. "
        f"The forecast projects {periods} periods ahead. "
        f"Average confidence: {confidence_avg:.0%}. "
        f"Model validation: R2={validation.get('r2', 'N/A')}, RMSE={validation.get('rmse', 'N/A')}. "
        "Provide a 2-3 sentence business explanation of what this forecast means."
    )
    try:
        explanation = await generate_response_async(explanation_prompt, request_type="forecasting")
    except Exception:
        explanation = explain_forecast(trend_direction, trend_strength, confidence_avg, column, periods, "linear_regression")

    return {
        "column": column,
        "historical": historical,
        "forecast": forecast_points,
        "trend_direction": trend_direction,
        "trend_strength": trend_strength,
        "confidence_avg": confidence_avg,
        "explanation": explanation,
        "validation": validation,
    }


def _empty_forecast(column: str) -> dict:
    return {
        "column": column,
        "historical": [],
        "forecast": [],
        "trend_direction": "unknown",
        "trend_strength": 0,
        "confidence_avg": 0,
        "explanation": "Insufficient data for forecasting.",
    }
