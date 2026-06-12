import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database.database import get_db
from app.models.schemas import DocumentCreate, DocumentResponse, UploadResponse, BulkDeleteRequest, QueryRequest, QueryResponse
from app.services.document_service import (
    create_document, list_documents, get_document, delete_document,
    bulk_delete_documents,
)
from app.services.document_parser import allowed_file
from app.services.document_processing_service import process_document, classify_file_type
from app.services.rag_service import answer_question

logger = logging.getLogger(__name__)

router = APIRouter(tags=["documents"])
settings = get_settings()

ALLOWED_STR = ", ".join(sorted([".csv", ".docx", ".pdf", ".xlsx", ".txt"]))


@router.post("/documents/", response_model=DocumentResponse)
async def create(payload: DocumentCreate, db: AsyncSession = Depends(get_db)):
    return await create_document(db, payload)


@router.get("/documents/", response_model=list[DocumentResponse])
async def list_all(db: AsyncSession = Depends(get_db)):
    return await list_documents(db)


@router.get("/documents/{doc_id}", response_model=DocumentResponse)
async def get(doc_id: int, db: AsyncSession = Depends(get_db)):
    return await get_document(db, doc_id)


@router.delete("/documents/{doc_id}")
async def delete(doc_id: int, db: AsyncSession = Depends(get_db)):
    await delete_document(db, doc_id)
    return {"detail": "Document deleted"}


@router.post("/documents/batch-delete")
async def batch_delete(payload: BulkDeleteRequest, db: AsyncSession = Depends(get_db)):
    deleted = await bulk_delete_documents(db, payload.doc_ids)
    return {"detail": f"{deleted} document(s) deleted", "deleted_count": deleted}


@router.post("/documents/query", response_model=QueryResponse)
async def query(payload: QueryRequest):
    return await answer_question(
        question=payload.question,
        k=payload.k or 5,
        session_id=payload.session_id,
        doc_id=payload.doc_id,
    )


@router.post("/upload/", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...)):
    logger.info("Upload request received: filename=%s", file.filename)

    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    if not allowed_file(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"File type not supported. Allowed: {ALLOWED_STR}",
        )

    content_bytes = await file.read()
    file_size = len(content_bytes)
    file_type = classify_file_type(file.filename)
    logger.info("File read: filename=%s type=%s size=%d bytes", file.filename, file_type, file_size)

    doc_id = await process_document(content_bytes, file.filename)

    return UploadResponse(
        filename=file.filename,
        size=file_size,
        file_type=file_type,
        upload_timestamp=datetime.now(timezone.utc),
        content_preview=file.filename,
    )
