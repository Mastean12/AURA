from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    AnalyticsRequest, AnalyticsResponse, ChartsRequest, ChartsResponse,
    InsightsResponse, HealthResponse, AnalyticsChatRequest, AnalyticsChatResponse,
    ExecutiveSummaryResponse, KPIResponse, ChartInsightRequest, ChartInsightResponse,
)
from app.services.analytics_service import get_analytics
from app.services.chart_service import generate_charts, generate_all_charts as _generate_all_charts, generate_smart_charts
from app.services.statistical_quality_service import run_full_quality_analysis as _run_full_quality_analysis
from app.services.insights_service import generate_insights as _generate_insights, generate_executive_summary
from app.services.health_service import get_dataset_health
from app.services.analytics_chat_service import chat_analytics as _chat_analytics
from app.services.kpi_detection_service import discover_kpis
from app.services.chart_insight_service import generate_chart_insight
from app.services.statistical_quality_service import run_full_quality_analysis, compute_statistical_confidence

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.post("/", response_model=AnalyticsResponse)
async def analytics(payload: AnalyticsRequest):
    return await get_analytics(payload.doc_id)


@router.post("/charts", response_model=ChartsResponse)
async def charts(payload: ChartsRequest):
    result = await generate_charts(payload.doc_id, payload.column)
    if result is None:
        raise HTTPException(status_code=404, detail="Document or column not found")
    return ChartsResponse(
        doc_id=payload.doc_id,
        column=payload.column,
        **result,
    )


@router.post("/charts/all", response_model=ChartsResponse)
async def charts_all(payload: AnalyticsRequest):
    # Uses new smart chart engine: top 5 features, one chart each
    result = await generate_smart_charts(payload.doc_id)
    return ChartsResponse(
        doc_id=payload.doc_id,
        column=(result.get("charts") or [{}])[0].get("column", ""),
        charts=result.get("charts", []),
        correlation=result.get("correlation"),
        target_variable=result.get("target_variable"),
    )


@router.post("/insights", response_model=InsightsResponse)
async def insights(payload: AnalyticsRequest):
    data = await _generate_insights(payload.doc_id)
    if "error" in data:
        raise HTTPException(status_code=500, detail=data["error"])
    return InsightsResponse(
        doc_id=payload.doc_id,
        executive_summary=data.get("executive_summary", ""),
        key_findings=data.get("key_findings", []),
        risks=data.get("risks", []),
        opportunities=data.get("opportunities", []),
        recommendations=data.get("recommendations", []),
        confidence_score=data.get("confidence_score", 0),
    )


@router.post("/health", response_model=HealthResponse)
async def health(payload: AnalyticsRequest):
    data = await get_dataset_health(payload.doc_id)
    return HealthResponse(
        doc_id=payload.doc_id,
        **data,
    )


@router.post("/chat", response_model=AnalyticsChatResponse)
async def analytics_chat(payload: AnalyticsChatRequest):
    result = await _chat_analytics(payload.doc_id, payload.question, payload.session_id)
    return AnalyticsChatResponse(
        answer=result["answer"],
        confidence=result["confidence"],
        session_id=payload.session_id,
    )


# --- Phase 1 New Endpoints ---

@router.post("/executive-summary", response_model=ExecutiveSummaryResponse)
async def executive_summary(payload: AnalyticsRequest):
    result = await generate_executive_summary(payload.doc_id)
    return ExecutiveSummaryResponse(
        doc_id=payload.doc_id,
        summary=result.get("summary", ""),
        confidence=result.get("confidence", 0.0),
    )


@router.get("/kpis", response_model=KPIResponse)
async def kpis(doc_id: int):
    result = await discover_kpis(doc_id)
    return KPIResponse(
        doc_id=doc_id,
        kpis=result,
    )


@router.post("/chart-insight", response_model=ChartInsightResponse)
async def chart_insight(payload: ChartInsightRequest):
    insight = await generate_chart_insight(payload.doc_id, payload.chart_type, payload.column)
    return ChartInsightResponse(
        doc_id=payload.doc_id,
        chart_type=payload.chart_type,
        column=payload.column,
        insight=insight,
    )


@router.post("/quality-analysis")
async def quality_analysis(payload: AnalyticsRequest):
    """Run full data quality + statistical analysis pipeline."""
    import io
    import logging
    import pandas as pd
    logger = logging.getLogger(__name__)
    try:
        from app.database.database import get_session_factory
        from app.models.document import Document
        from sqlalchemy import select
        async with get_session_factory()() as db:
            r = await db.execute(select(Document).where(Document.id == payload.doc_id))
            doc = r.scalar_one_or_none()
    except Exception:
        doc = None
    if not doc or not doc.content:
        raise HTTPException(status_code=404, detail="Document not found")
    df = pd.read_csv(io.StringIO(doc.content)) if doc.content.count(",") > 5 else None
    if df is None or len(df.columns) < 2:
        raise HTTPException(status_code=400, detail="Dataset must be tabular")

    import json
    from app.services.statistical_quality_service import run_full_quality_analysis
    result = await run_full_quality_analysis(payload.doc_id, df)

    # Persist
    try:
        from app.models.quality_report import QualityReport
        from app.database.database import get_session_factory
        async with get_session_factory()() as db:
            existing = await db.execute(select(QualityReport).where(QualityReport.doc_id == payload.doc_id))
            qr = existing.scalar_one_or_none()
            if not qr:
                qr = QualityReport(doc_id=payload.doc_id)
                db.add(qr)
            dq = result.get("data_quality", {})
            qr.data_quality_score = dq.get("overall_score")
            qr.data_quality_grade = dq.get("grade")
            qr.statistical_confidence = result.get("statistical_confidence", {}).get("score")
            qr.issues_count = dq.get("issues_count", 0)
            qr.issues_json = json.dumps(dq.get("issues", []))
            qr.suggestions_json = json.dumps(result.get("feature_engineering_suggestions", []))
            await db.commit()
    except Exception as e:
        logger.warning("Quality report persistence failed: %s", e)

    result["doc_id"] = payload.doc_id
    return result
