from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.models.schemas import (
    AnalyticsRequest, IndustryDashboardResponse,
    MultiDocumentRequest, MultiDocumentResponse,
    ComparisonRequest, ComparisonResponse,
    AutonomousAnalysisRequest, AutonomousAnalysisResponse,
    BoardReportRequest,
    ExecutiveBriefingRequest, ExecutiveBriefingResponse,
)
from app.services.industry_intelligence_service import generate_industry_dashboard
from app.services.multi_document_service import analyze_multi_document
from app.services.comparison_service import compare_documents
from app.services.autonomous_analyst_service import run_autonomous_analysis
from app.services.board_report_service import generate_board_report
from app.services.executive_briefing_service import generate_executive_briefing

router = APIRouter(tags=["enterprise"])


@router.get("/analytics/industry-dashboard", response_model=IndustryDashboardResponse)
async def industry_dashboard(doc_id: int):
    result = await generate_industry_dashboard(doc_id)
    return IndustryDashboardResponse(
        doc_id=doc_id,
        **result,
    )


@router.post("/analytics/multi-document", response_model=MultiDocumentResponse)
async def multi_document(payload: MultiDocumentRequest):
    result = await analyze_multi_document(payload.doc_ids)
    return MultiDocumentResponse(**result)


@router.post("/analytics/compare", response_model=ComparisonResponse)
async def compare(payload: ComparisonRequest):
    result = await compare_documents(payload.doc_id_a, payload.doc_id_b, payload.label_a, payload.label_b)
    return ComparisonResponse(**result)


@router.post("/analytics/autonomous-analysis", response_model=AutonomousAnalysisResponse)
async def autonomous_analysis(payload: AutonomousAnalysisRequest):
    result = await run_autonomous_analysis(payload.doc_ids)
    return AutonomousAnalysisResponse(
        doc_id=result.get("doc_id", 0),
        business_health=result.get("business_health", {}),
        top_risks=result.get("top_risks", []),
        top_opportunities=result.get("top_opportunities", []),
        forecasts=result.get("forecasts", []),
        strategic_recommendations=result.get("strategic_recommendations", []),
        overall_confidence=result.get("overall_confidence", 0),
    )


@router.post("/reports/board-report")
async def board_report(payload: BoardReportRequest):
    try:
        pdf_bytes = await generate_board_report(payload.doc_id, payload.company_name)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=board-report-{payload.doc_id}.pdf"},
        )
    except Exception as e:
        logger = __import__("logging").getLogger(__name__)
        logger.warning("Board report failed: %s", e)
        raise HTTPException(status_code=500, detail="Board report generation failed.")


@router.post("/reports/executive-briefing", response_model=ExecutiveBriefingResponse)
async def executive_briefing(payload: ExecutiveBriefingRequest):
    result = await generate_executive_briefing(payload.doc_id, payload.company_name)
    return ExecutiveBriefingResponse(**result)
