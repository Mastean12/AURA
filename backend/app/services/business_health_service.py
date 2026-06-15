import io
import json
import logging

import numpy as np
import pandas as pd

from app.database.database import get_session_factory
from app.models.document import Document
from app.services.health_service import get_dataset_health
from app.services.risk_scoring_service import calculate_risk_score
from app.services.ai_service import generate_response_async
from sqlalchemy import select

logger = logging.getLogger(__name__)


async def calculate_business_health(doc_ids: list[int] | None = None) -> dict:
    if not doc_ids:
        return _empty_health()

    primary_doc = doc_ids[0]
    data_health = {}
    risk_data = {}
    financial_score = 50
    operational_score = 50
    growth_score = 50
    risk_exposure = 50

    try:
        data_health = await get_dataset_health(primary_doc)
        data_quality = data_health.get("overall", 50)
    except Exception:
        data_quality = 50

    try:
        risk_data = await calculate_risk_score(primary_doc)
        risk_scores = {c["name"]: c["score"] for c in risk_data.get("categories", [])}
        risk_exposure = 100 - min(risk_data.get("overall_score", 50), 100)
        financial_score = 100 - risk_scores.get("Financial Risk", 50)
        operational_score = 100 - risk_scores.get("Operational Risk", 50)
    except Exception:
        pass

    try:
        async with get_session_factory()() as db:
            result = await db.execute(select(Document).where(Document.id == primary_doc))
            doc = result.scalar_one_or_none()
            if doc and doc.content:
                df = pd.read_csv(io.StringIO(doc.content)) if doc.content.count(",") > 5 else None
                if df is not None:
                    numeric_cols = df.select_dtypes(include=["number"]).columns
                    if len(numeric_cols) >= 2:
                        for col in numeric_cols[:3]:
                            vals = df[col].dropna().values.astype(float)
                            if len(vals) >= 4:
                                recent = vals[-3:].mean()
                                earlier = vals[:3].mean()
                                if earlier > 0:
                                    growth_rate = ((recent - earlier) / earlier) * 100
                                    if growth_rate > 0:
                                        growth_score = min(growth_score + 15, 100)
                                    else:
                                        growth_score = max(growth_score - 10, 0)
    except Exception:
        pass

    overall = round((financial_score + operational_score + growth_score + risk_exposure + data_quality) / 5)
    overall = max(0, min(100, overall))

    prompt = (
        f"Business Health Assessment:\n"
        f"Overall: {overall}/100\n"
        f"Financial Health: {financial_score}/100\n"
        f"Operational Health: {operational_score}/100\n"
        f"Growth Potential: {growth_score}/100\n"
        f"Risk Exposure: {risk_exposure}/100\n"
        f"Data Quality: {data_quality}/100\n\n"
        "Provide a 1-sentence explanation for each score. Keep it concise and business-focused."
    )
    explanations = {}
    try:
        raw = await generate_response_async(prompt, request_type="business_health")
        explanations = {"raw": raw[:500]}
    except Exception:
        pass

    return {
        "overall": overall,
        "financial_health": financial_score,
        "operational_health": operational_score,
        "growth_potential": growth_score,
        "risk_exposure": risk_exposure,
        "data_quality": data_quality,
        "explanations": explanations,
        "level": "excellent" if overall >= 80 else "good" if overall >= 60 else "moderate" if overall >= 40 else "critical",
    }


def _empty_health() -> dict:
    return {
        "overall": 0, "financial_health": 0, "operational_health": 0,
        "growth_potential": 0, "risk_exposure": 0, "data_quality": 0,
        "explanations": {}, "level": "unknown",
    }
