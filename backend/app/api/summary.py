from fastapi import APIRouter

from app.models.schemas import SummaryRequest, SummaryResponse
from app.services.summary_service import summarize_document

router = APIRouter(prefix="/summary", tags=["summary"])


@router.post("/", response_model=SummaryResponse)
async def summarize(payload: SummaryRequest):
    return await summarize_document(payload.doc_id, payload.summary_type)
