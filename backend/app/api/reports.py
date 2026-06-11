from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.services.report_service import generate_report
from app.services.board_report_service import generate_board_report
from app.services.executive_briefing_report import generate_executive_briefing_pdf
from app.services.intelligence_report_generator import generate_intelligence_report

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/export")
async def export_report(payload: dict):
    doc_id = payload.get("doc_id")
    if not doc_id or not isinstance(doc_id, int):
        raise HTTPException(status_code=400, detail="doc_id is required")
    try:
        pdf_bytes = await generate_report(doc_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return Response(
        content=bytes(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="aura-report-{doc_id}.pdf"',
        },
    )


@router.post("/board-report")
async def board_report(payload: dict):
    doc_ids = payload.get("doc_ids", [])
    company_name = payload.get("company_name", "")
    if not doc_ids:
        raise HTTPException(status_code=400, detail="doc_ids is required")
    try:
        pdf_bytes = await generate_board_report(doc_ids, company_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Board report failed: {e}")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=aura-board-report.pdf"},
    )


@router.post("/executive-briefing-pdf")
async def executive_briefing_report(payload: dict):
    doc_ids = payload.get("doc_ids", [])
    company_name = payload.get("company_name", "")
    if not doc_ids:
        raise HTTPException(status_code=400, detail="doc_ids is required")
    try:
        pdf_bytes = await generate_executive_briefing_pdf(doc_ids, company_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Executive briefing failed: {e}")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=aura-executive-briefing.pdf"},
    )


@router.post("/intelligence-report")
async def intelligence_report(payload: dict):
    doc_ids = payload.get("doc_ids", [])
    if not doc_ids:
        raise HTTPException(status_code=400, detail="doc_ids is required")
    try:
        pdf_bytes = await generate_intelligence_report(doc_ids)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Intelligence report failed: {e}")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=aura-intelligence-report.pdf"},
    )
