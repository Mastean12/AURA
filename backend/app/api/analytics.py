from fastapi import APIRouter, HTTPException

from app.models.schemas import AnalyticsRequest, AnalyticsResponse, ChartsRequest, ChartsResponse
from app.services.analytics_service import get_analytics
from app.services.chart_service import generate_charts

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.post("/", response_model=AnalyticsResponse)
async def analytics(payload: AnalyticsRequest):
    return await get_analytics(payload.doc_id)


@router.post("/charts", response_model=ChartsResponse)
async def charts(payload: ChartsRequest):
    result = generate_charts(payload.doc_id, payload.column)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Document or column not found",
        )
    return ChartsResponse(
        doc_id=payload.doc_id,
        column=payload.column,
        **result,
    )
