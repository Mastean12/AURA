import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from app.services.board_report_service import generate_board_report
from app.services.executive_briefing_report import generate_executive_briefing_pdf
from app.services.intelligence_report_generator import generate_intelligence_report
from app.services.analytics_export_service import generate_analytics_export
from app.database.database import get_session_factory
from app.models.organization import Organization
from sqlalchemy import select

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["reports"])


class ReportRequest(BaseModel):
    doc_ids: list[int] = []
    doc_id: int | None = None
    org_id: int | None = None
    company_name: str = ""
    workspace: str = ""

    def resolved_doc_ids(self) -> list[int]:
        return self.doc_ids if self.doc_ids else ([self.doc_id] if self.doc_id else [])


async def _resolve_org(org_id: int | None, company_name: str) -> tuple[str, str, str]:
    if org_id:
        try:
            async with get_session_factory()() as db:
                r = await db.execute(select(Organization).where(Organization.id == org_id))
                org = r.scalar_one_or_none()
                if org:
                    return org.name or company_name, org.logo_url or "", org.theme_color or "#2563eb"
        except Exception as e:
            logger.warning("Org fetch failed: %s", e)
    return company_name, "", "#2563eb"


def _quality_check(pdf_obj, result: dict | None = None) -> dict:
    errors = []
    try:
        if pdf_obj.page_no() < 2:
            errors.append("Report has no content pages")
        v_errors = pdf_obj.validate()
        errors.extend(v_errors)
    except Exception as e:
        logger.warning("Quality check: %s", e)

    if result:
        if not result.get("executive_summary") and not result.get("prediction_explanation", {}).get("summary"):
            errors.append("Executive summary is missing")
        if not result.get("risks"):
            errors.append("No risks identified")
        if not result.get("opportunities"):
            errors.append("No opportunities identified")
        if not result.get("prescriptive_recommendations") and not result.get("technical", {}).get("feature_importance"):
            errors.append("No recommendations or feature analysis generated")

    return {"passed": len(errors) == 0, "errors": errors}


def _pdf_response(pdf_obj) -> Response:
    try:
        pdf_bytes = pdf_obj.to_bytes()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {e}")
    qc = _quality_check(pdf_obj)
    if not qc["passed"]:
        logger.warning("Quality control: %s", qc["errors"])
    fname = pdf_obj.filename()
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )


@router.post("/executive-briefing-pdf")
async def executive_briefing_report(payload: ReportRequest):
    try:
        doc_ids = payload.resolved_doc_ids()
        if not doc_ids:
            raise HTTPException(status_code=400, detail="doc_ids or doc_id required")
        org_name, org_logo, org_color = await _resolve_org(payload.org_id, payload.company_name)
        pdf_obj = await generate_executive_briefing_pdf(
            doc_ids, org_name, org_logo, org_color, payload.workspace,
        )
        return _pdf_response(pdf_obj)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Executive briefing failed")
        raise HTTPException(status_code=500, detail=f"Executive briefing failed: {e}")


@router.post("/board-report")
async def board_report(payload: ReportRequest):
    try:
        doc_ids = payload.resolved_doc_ids()
        if not doc_ids:
            raise HTTPException(status_code=400, detail="doc_ids or doc_id required")
        org_name, org_logo, org_color = await _resolve_org(payload.org_id, payload.company_name)
        pdf_obj = await generate_board_report(
            doc_ids, org_name, org_logo, org_color, payload.workspace,
        )
        return _pdf_response(pdf_obj)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Board report failed")
        raise HTTPException(status_code=500, detail=f"Board report failed: {e}")


@router.post("/intelligence-report")
async def intelligence_report(payload: ReportRequest):
    try:
        doc_ids = payload.resolved_doc_ids()
        if not doc_ids:
            raise HTTPException(status_code=400, detail="doc_ids or doc_id required")
        org_name, org_logo, org_color = await _resolve_org(payload.org_id, payload.company_name)
        pdf_obj = await generate_intelligence_report(
            doc_ids, org_name, org_logo, org_color, payload.workspace,
        )
        return _pdf_response(pdf_obj)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Intelligence report failed")
        raise HTTPException(status_code=500, detail=f"Intelligence report failed: {e}")


@router.post("/export")
async def export_report(payload: ReportRequest):
    doc_id = payload.doc_id or (payload.doc_ids[0] if payload.doc_ids else None)
    if not doc_id:
        raise HTTPException(status_code=400, detail="doc_id required")
    try:
        pdf_obj = await generate_analytics_export(doc_id)
        return _pdf_response(pdf_obj)
    except Exception as e:
        logger.exception("Analytics export failed")
        raise HTTPException(status_code=500, detail=f"Analytics export failed: {e}")


# Legacy: /reports/analytics-export forwards to /export
@router.post("/analytics-export")
async def analytics_export_legacy(payload: ReportRequest):
    return await export_report(payload)
