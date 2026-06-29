import io
import logging

import numpy as np
import pandas as pd

from app.database.database import get_session_factory
from app.models.document import Document
from app.services.ai_service import generate_response_async
from sqlalchemy import select

logger = logging.getLogger(__name__)


def _score_to_level(score: int) -> str:
    if score >= 70:
        return "critical"
    elif score >= 50:
        return "high"
    elif score >= 30:
        return "moderate"
    return "low"


def _calculate_financial_risk(df: pd.DataFrame) -> tuple[int, str, list[str]]:
    numeric_cols = df.select_dtypes(include=["number"]).columns
    if len(numeric_cols) < 2:
        return 20, "Limited financial data available for analysis.", ["Add more numeric columns for financial risk assessment."]

    risk_score = 0
    declining_count = 0
    volatile_count = 0

    for col in numeric_cols[:5]:
        values = pd.to_numeric(df[col], errors='coerce').dropna().values.astype(float)
        if len(values) < 3:
            continue
        changes = np.diff(values) / (values[:-1] + 1e-10)
        neg_ratio = np.sum(changes < -0.05) / len(changes)
        if neg_ratio > 0.5:
            declining_count += 1
            risk_score += 15
        volatility = np.std(changes)
        if volatility > 0.2:
            volatile_count += 1
            risk_score += 10

    mitigations = []
    if declining_count > 0:
        mitigations.append(f"Review {declining_count} column(s) showing frequent declines.")
    if volatile_count > 0:
        mitigations.append(f"Investigate {volatile_count} volatile column(s) for instability.")
    if risk_score == 0:
        mitigations.append("Financial indicators appear stable.")
        risk_score = 15

    risk_score = min(risk_score, 95)
    explanation = f"Risk from {len(numeric_cols)} numeric columns; {declining_count} show declines, {volatile_count} show high volatility."
    return risk_score, explanation, mitigations


def _calculate_operational_risk(df: pd.DataFrame) -> tuple[int, str, list[str]]:
    risk_score = 0
    mitigations = []

    dupes = df.duplicated().sum()
    dupe_ratio = dupes / len(df) if len(df) > 0 else 0
    if dupe_ratio > 0.1:
        risk_score += 25
        mitigations.append(f"Remove {dupes} duplicate rows to improve data quality.")
    elif dupe_ratio > 0.05:
        risk_score += 15
    else:
        risk_score += 5

    empty_cols = sum(1 for c in df.columns if df[c].dropna().empty)
    if empty_cols > 0:
        risk_score += empty_cols * 10
        mitigations.append(f"{empty_cols} column(s) are empty or fully null.")

    missing_ratio = df.isna().sum().sum() / (df.shape[0] * df.shape[1]) if df.shape[0] * df.shape[1] > 0 else 0
    if missing_ratio > 0.3:
        risk_score += 25
        mitigations.append(f"High missing data ratio ({missing_ratio:.0%}) requires attention.")
    elif missing_ratio > 0.1:
        risk_score += 15
    else:
        risk_score += 5

    if not mitigations:
        mitigations.append("Operational metrics appear normal.")

    risk_score = min(risk_score, 95)
    explanation = (
        f"{int(dupes)} duplicates ({dupe_ratio:.1%}), {empty_cols} empty columns, "
        f"missing data ratio {missing_ratio:.1%}."
    )
    return risk_score, explanation, mitigations


def _calculate_data_quality_risk(df: pd.DataFrame) -> tuple[int, str, list[str]]:
    risk_score = 0
    mitigations = []

    total_cols = len(df.columns)
    numeric_cols = df.select_dtypes(include=["number"]).columns
    num_numeric = len(numeric_cols)
    if num_numeric < total_cols * 0.3:
        risk_score += 20
        mitigations.append("Low proportion of numeric columns limits quantitative analysis.")

    mixed_types = 0
    for col in df.columns:
        if df[col].dropna().apply(type).nunique() > 2:
            mixed_types += 1
    if mixed_types > 0:
        risk_score += mixed_types * 10
        mitigations.append(f"{mixed_types} column(s) have mixed data types.")

    for col in numeric_cols:
        col_data = df[col].dropna()
        if len(col_data) > 0:
            z = np.abs((col_data - col_data.mean()) / (col_data.std() + 1e-10))
            outlier_ratio = (z > 3).sum() / len(col_data)
            if outlier_ratio > 0.05:
                risk_score += 10
                mitigations.append(f"Column '{col}' has {outlier_ratio:.1%} extreme outliers.")
                break

    if not mitigations:
        mitigations.append("Data quality is acceptable.")

    risk_score = min(risk_score, 95)
    explanation = f"Quality assessment across {total_cols} columns; {num_numeric} numeric, {mixed_types} mixed-type."
    return risk_score, explanation, mitigations


def _calculate_performance_risk(df: pd.DataFrame) -> tuple[int, str, list[str]]:
    risk_score = 0
    mitigations = []
    numeric_cols = df.select_dtypes(include=["number"]).columns

    if len(numeric_cols) < 3:
        risk_score += 20
        mitigations.append("Limited numeric data for performance trend analysis.")

    declining_metrics = 0
    for col in numeric_cols[:5]:
        values = pd.to_numeric(df[col], errors='coerce').dropna().values.astype(float)
        if len(values) < 4:
            continue
        recent = values[-3:].mean()
        earlier = values[:3].mean()
        if earlier > 0 and recent < earlier * 0.9:
            declining_metrics += 1
            risk_score += 15

    if declining_metrics > 0:
        mitigations.append(f"{declining_metrics} metric(s) show recent performance decline.")
    elif risk_score == 0:
        risk_score = 15
        mitigations.append("Performance indicators are stable.")

    risk_score = min(risk_score, 95)
    explanation = f"Analysis of {len(numeric_cols)} numeric metrics; {declining_metrics} show declining performance."
    return risk_score, explanation, mitigations


async def calculate_risk_score(doc_id: int) -> dict:
    logger.info("Calculating risk score for doc_id=%d", doc_id)
    try:
        async with get_session_factory()() as db:
            result = await db.execute(select(Document).where(Document.id == doc_id))
            doc = result.scalar_one_or_none()
    except Exception as e:
        logger.warning("DB error: %s", e)
        return _empty_risk_score()

    if not doc or not doc.content:
        return _empty_risk_score()

    df = pd.read_csv(io.StringIO(doc.content), on_bad_lines="skip") if doc.content.count(",") > 5 else None
    if df is None or len(df.columns) < 2:
        return _empty_risk_score()

    fin_score, fin_exp, fin_mit = _calculate_financial_risk(df)
    ops_score, ops_exp, ops_mit = _calculate_operational_risk(df)
    dq_score, dq_exp, dq_mit = _calculate_data_quality_risk(df)
    perf_score, perf_exp, perf_mit = _calculate_performance_risk(df)

    overall = round((fin_score + ops_score + dq_score + perf_score) / 4)
    overall = max(0, min(100, overall))

    overall_exp_prompt = (
        f"Business dataset risk assessment: Financial Risk={fin_score}/100, "
        f"Operational Risk={ops_score}/100, Data Quality Risk={dq_score}/100, "
        f"Performance Risk={perf_score}/100. Overall={overall}/100. "
        "Provide a 2-sentence executive summary of the key risks."
    )
    try:
        overall_explanation = await generate_response_async(overall_exp_prompt, request_type="risk_scoring")
    except Exception:
        overall_explanation = (
            f"Overall business risk is {overall}/100 ({_score_to_level(overall)}). "
            f"Primary concerns: {fin_exp[:50]} {ops_exp[:50]}"
        )

    return {
        "overall_score": overall,
        "overall_level": _score_to_level(overall),
        "overall_explanation": overall_explanation,
        "categories": [
            {
                "name": "Financial Risk",
                "score": fin_score,
                "level": _score_to_level(fin_score),
                "explanation": fin_exp,
                "mitigations": fin_mit,
            },
            {
                "name": "Operational Risk",
                "score": ops_score,
                "level": _score_to_level(ops_score),
                "explanation": ops_exp,
                "mitigations": ops_mit,
            },
            {
                "name": "Data Quality Risk",
                "score": dq_score,
                "level": _score_to_level(dq_score),
                "explanation": dq_exp,
                "mitigations": dq_mit,
            },
            {
                "name": "Performance Risk",
                "score": perf_score,
                "level": _score_to_level(perf_score),
                "explanation": perf_exp,
                "mitigations": perf_mit,
            },
        ],
    }


def _empty_risk_score() -> dict:
    return {
        "overall_score": 0,
        "overall_level": "unknown",
        "overall_explanation": "Insufficient data for risk scoring.",
        "categories": [
            {"name": "Financial Risk", "score": 0, "level": "unknown", "explanation": "No data.", "mitigations": []},
            {"name": "Operational Risk", "score": 0, "level": "unknown", "explanation": "No data.", "mitigations": []},
            {"name": "Data Quality Risk", "score": 0, "level": "unknown", "explanation": "No data.", "mitigations": []},
            {"name": "Performance Risk", "score": 0, "level": "unknown", "explanation": "No data.", "mitigations": []},
        ],
    }
