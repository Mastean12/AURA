import logging

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

from app.services.board_report_service import generate_board_report
from app.services.executive_briefing_report import generate_executive_briefing_pdf
from app.services.intelligence_report_generator import generate_intelligence_report
from app.database.database import get_session_factory
from app.models.organization import Organization
from sqlalchemy import select

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["reports"])


class ReportRequest(BaseModel):
    doc_ids: list[int]
    org_id: int | None = None
    company_name: str = ""
    workspace: str = ""


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


def _quality_check(pdf_bytes: bytes, pdf_obj) -> dict:
    errors = []
    if not pdf_bytes or len(pdf_bytes) < 5000:
        errors.append("Report content is too short or empty")
    if pdf_obj.page_no() < 2:
        errors.append("Report has no content pages")
    v_errors = pdf_obj.validate()
    errors.extend(v_errors)
    return {"passed": len(errors) == 0, "errors": errors}


def _pdf_response(pdf_bytes: bytes, pdf_obj) -> Response:
    qc = _quality_check(pdf_bytes, pdf_obj)
    if not qc["passed"]:
        logger.warning("Quality control failed: %s", qc["errors"])
    fname = pdf_obj.filename()
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )


@router.post("/executive-briefing-pdf")
async def executive_briefing_report(payload: ReportRequest):
    try:
        org_name, org_logo, org_color = await _resolve_org(payload.org_id, payload.company_name)
        pdf_obj = await generate_executive_briefing_pdf(
            payload.doc_ids, org_name, org_logo, org_color, payload.workspace,
        )
        return _pdf_response(pdf_obj, pdf_obj)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Executive briefing failed: {e}")


@router.post("/board-report")
async def board_report(payload: ReportRequest):
    try:
        org_name, org_logo, org_color = await _resolve_org(payload.org_id, payload.company_name)
        pdf_obj = await generate_board_report(
            payload.doc_ids, org_name, org_logo, org_color, payload.workspace,
        )
        return _pdf_response(pdf_obj, pdf_obj)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Board report failed: {e}")


@router.post("/intelligence-report")
async def intelligence_report(payload: ReportRequest):
    try:
        org_name, org_logo, org_color = await _resolve_org(payload.org_id, payload.company_name)
        pdf_obj = await generate_intelligence_report(
            payload.doc_ids, org_name, org_logo, org_color, payload.workspace,
        )
        return _pdf_response(pdf_obj, pdf_obj)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Intelligence report failed: {e}")


@router.post("/export")
async def export_report(payload: ReportRequest):
    return await board_report(payload)
