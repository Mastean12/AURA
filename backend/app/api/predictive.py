from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import (
    ForecastRequest, ForecastResponse,
    AnomalyRequest, AnomalyResponse,
    RiskScoreRequest, RiskScoreResponse,
    RecommendationRequest, RecommendationResponse,
    RiskCategory, RecommendationItem,
)
from app.services.forecasting_service import generate_forecast
from app.services.anomaly_detection_service import detect_anomalies
from app.services.risk_scoring_service import calculate_risk_score
from app.services.recommendation_engine import generate_recommendations

router = APIRouter(prefix="/predictive", tags=["predictive"])


@router.post("/forecast", response_model=ForecastResponse)
async def forecast(payload: ForecastRequest):
    result = await generate_forecast(payload.doc_id, payload.column, payload.periods)
    return ForecastResponse(
        doc_id=payload.doc_id,
        column=result["column"],
        historical=result["historical"],
        forecast=result["forecast"],
        trend_direction=result["trend_direction"],
        trend_strength=result["trend_strength"],
        confidence_avg=result["confidence_avg"],
        explanation=result["explanation"],
    )


@router.post("/anomalies", response_model=AnomalyResponse)
async def anomalies(payload: AnomalyRequest):
    result = await detect_anomalies(payload.doc_id, payload.column, payload.severity)
    return AnomalyResponse(
        doc_id=payload.doc_id,
        column=result["column"],
        anomalies=result["anomalies"],
        anomaly_count=result["anomaly_count"],
        high_severity_count=result["high_severity_count"],
        summary=result["summary"],
    )


@router.post("/risk-score", response_model=RiskScoreResponse)
async def risk_score(payload: RiskScoreRequest):
    result = await calculate_risk_score(payload.doc_id)
    return RiskScoreResponse(
        doc_id=payload.doc_id,
        overall_score=result["overall_score"],
        overall_level=result["overall_level"],
        overall_explanation=result["overall_explanation"],
        categories=[RiskCategory(**c) for c in result["categories"]],
    )


@router.post("/recommendations", response_model=RecommendationResponse)
async def recommendations(payload: RecommendationRequest):
    result = await generate_recommendations(payload.doc_id)
    high_count = sum(1 for r in result if r.get("urgency") == "high" or r.get("impact") == "high")
    return RecommendationResponse(
        doc_id=payload.doc_id,
        recommendations=[RecommendationItem(**r) for r in result],
        total_count=len(result),
        high_priority_count=high_count,
    )
