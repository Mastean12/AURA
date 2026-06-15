import io
import logging

import numpy as np
import pandas as pd

from app.database.database import get_session_factory
from app.models.document import Document
from app.services.ai_service import generate_response_async
from sqlalchemy import select

logger = logging.getLogger(__name__)


def _detect_anomalies_zscore(values: np.ndarray) -> np.ndarray:
    mean = np.mean(values)
    std = np.std(values)
    if std == 0:
        return np.zeros_like(values)
    z = np.abs((values - mean) / std)
    return z


def _detect_anomalies_iqr(values: np.ndarray) -> tuple[np.ndarray, float, float]:
    q1, q3 = np.percentile(values, [25, 75])
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    scores = np.where((values < lower) | (values > upper), 1, 0)
    return scores, lower, upper


def _detect_anomalies_moving_average(values: np.ndarray, window: int = 5) -> np.ndarray:
    if len(values) < window + 2:
        return np.zeros_like(values)
    ma = pd.Series(values).rolling(window=window, min_periods=1).mean().values
    deviation = np.abs(values - ma)
    std_dev = np.std(deviation)
    if std_dev == 0:
        return np.zeros_like(values)
    scores = deviation / (std_dev + 1e-10)
    return scores


def _compute_severity(zscore: float, ma_score: float) -> tuple[str, str]:
    combined = max(zscore, ma_score)
    if combined > 3.5:
        return "high", "Critical deviation from expected pattern"
    elif combined > 2.5:
        return "medium", "Notable deviation detected"
    elif combined > 1.5:
        return "low", "Minor deviation observed"
    return "low", "Slight variation"


def _classify_anomaly(values: np.ndarray, idx: int) -> str:
    if idx == 0:
        return "spike" if values[idx] > values[idx + 1] else "drop"
    if idx == len(values) - 1:
        return "spike" if values[idx] > values[idx - 1] else "drop"
    if values[idx] > values[idx - 1] and values[idx] > values[idx + 1]:
        return "spike"
    if values[idx] < values[idx - 1] and values[idx] < values[idx + 1]:
        return "drop"
    return "outlier"


async def _generate_anomaly_explanation(values: np.ndarray, idx: int, anomaly_type: str, severity: str) -> str:
    val = values[idx]
    prev = values[idx - 1] if idx > 0 else val
    pct_change = ((val - prev) / (prev + 1e-10)) * 100
    direction = "increased" if pct_change > 0 else "decreased"

    prompt = (
        f"In a business dataset, value at index {idx} is {val:.2f}, "
        f"which {direction} by {abs(pct_change):.1f}% from the previous value of {prev:.2f}. "
        f"Type: {anomaly_type}. Severity: {severity}. "
        "Provide a 1-sentence business explanation of what might have caused this."
    )
    try:
        return await generate_response_async(prompt, request_type="anomaly_detection")
    except Exception:
        if anomaly_type == "spike":
            return f"Unexpected surge: value {direction} by {abs(pct_change):.1f}%."
        elif anomaly_type == "drop":
            return f"Unexpected decline: value {direction} by {abs(pct_change):.1f}%."
        return f"Unusual value detected: {val:.2f} ({direction} {abs(pct_change):.1f}%)."


async def detect_anomalies(doc_id: int, column: str, severity_filter: str | None = None) -> dict:
    logger.info("Detecting anomalies for doc_id=%d, column=%s", doc_id, column)
    try:
        async with get_session_factory()() as db:
            result = await db.execute(select(Document).where(Document.id == doc_id))
            doc = result.scalar_one_or_none()
    except Exception as e:
        logger.warning("DB error: %s", e)
        return {"column": column, "anomalies": [], "anomaly_count": 0, "high_severity_count": 0, "summary": ""}

    if not doc or not doc.content:
        return {"column": column, "anomalies": [], "anomaly_count": 0, "high_severity_count": 0, "summary": ""}

    df = pd.read_csv(io.StringIO(doc.content)) if doc.content.count(",") > 5 else None
    if df is None or column not in df.columns:
        return {"column": column, "anomalies": [], "anomaly_count": 0, "high_severity_count": 0, "summary": ""}

    values = df[column].dropna().values.astype(float)
    if len(values) < 5:
        return {"column": column, "anomalies": [], "anomaly_count": 0, "high_severity_count": 0, "summary": ""}

    z_scores = _detect_anomalies_zscore(values)
    iqr_scores, lower, upper = _detect_anomalies_iqr(values)
    ma_scores = _detect_anomalies_moving_average(values)

    anomalies = []
    high_count = 0

    for i in range(len(values)):
        if z_scores[i] < 1.5 and iqr_scores[i] == 0 and ma_scores[i] < 1.5:
            continue

        severity, severity_desc = _compute_severity(z_scores[i], ma_scores[i])
        if severity_filter and severity != severity_filter.lower():
            continue

        anomaly_type = _classify_anomaly(values, i)
        explanation = await _generate_anomaly_explanation(values, i, anomaly_type, severity)

        expected = np.mean([values[max(0, i - 3):i].mean() if i > 0 else values[i],
                           values[i + 1:min(len(values), i + 4)].mean() if i < len(values) - 1 else values[i]])
        deviation = abs(values[i] - expected) / (expected + 1e-10) * 100

        if severity == "high":
            high_count += 1

        anomalies.append({
            "index": int(i),
            "value": round(float(values[i]), 2),
            "expected": round(float(expected), 2),
            "deviation": round(float(deviation), 1),
            "severity": severity,
            "type": anomaly_type,
            "explanation": explanation,
        })

    anomalies.sort(key=lambda a: {"high": 0, "medium": 1, "low": 2}[a["severity"]])

    total_count = len(anomalies)
    if total_count == 0:
        summary = f"No significant anomalies detected in '{column}'."
    elif total_count == 1:
        summary = f"{total_count} anomaly detected in '{column}'."
    else:
        summary = f"{total_count} anomalies detected in '{column}' ({high_count} high severity)."

    return {
        "column": column,
        "anomalies": anomalies[:50],
        "anomaly_count": min(total_count, 50),
        "high_severity_count": high_count,
        "summary": summary,
    }
