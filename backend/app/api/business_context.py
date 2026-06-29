import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import select

from app.database.database import get_session_factory
from app.models.document import Document
from app.models.dataset_meta import DatasetMetadata
from app.services.business_context_service import run_business_context_detection

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/business-context", tags=["business-context"])


class DocRequest(BaseModel):
    doc_id: int


@router.post("/detect")
async def detect_business_context(payload: DocRequest):
    """Detect industry, dataset type, business objective, and analytical problem."""
    result = await run_business_context_detection(payload.doc_id)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])

    # Persist to DatasetMetadata
    try:
        async with get_session_factory()() as db:
            existing = await db.execute(select(DatasetMetadata).where(DatasetMetadata.doc_id == payload.doc_id))
            meta = existing.scalar_one_or_none()
            if meta and not meta.overridden:
                meta.industry = result.get("industry", meta.industry)
                meta.dataset_type = result.get("dataset_type", meta.dataset_type)
            elif not meta:
                meta = DatasetMetadata(
                    doc_id=payload.doc_id,
                    industry=result.get("industry"),
                    dataset_type=result.get("dataset_type"),
                    target_variable=result.get("target_variable"),
                )
                db.add(meta)
            await db.commit()
    except Exception as e:
        logger.warning("Context persistence failed: %s", e)

    return result


@router.get("/{doc_id}")
async def get_business_context(doc_id: int):
    """Retrieve stored business context for a document."""
    try:
        async with get_session_factory()() as db:
            r = await db.execute(select(DatasetMetadata).where(DatasetMetadata.doc_id == doc_id))
            meta = r.scalar_one_or_none()
            if not meta:
                raise HTTPException(status_code=404, detail="No context found")
            return {
                "doc_id": doc_id,
                "industry": meta.industry,
                "dataset_type": meta.dataset_type,
                "target_variable": meta.target_variable,
                "overridden": meta.overridden,
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
