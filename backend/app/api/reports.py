from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.services.report_service import generate_report

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
