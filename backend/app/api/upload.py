import asyncio
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database.database import get_db
from app.models.schemas import DocumentCreate, DocumentResponse, UploadResponse
from app.services.document_service import create_document, list_documents, get_document, delete_document
from app.services.document_service import store_chunks as store_chunks_db
from app.services.document_parser import allowed_file, extract_text, save_upload
from app.services.chunking_service import chunk_text
from app.services.embedding_service import store_chunk_vectors

logger = logging.getLogger(__name__)

router = APIRouter(tags=["documents"])
settings = get_settings()

ALLOWED_STR = ", ".join(sorted([".csv", ".docx", ".pdf", ".xlsx"]))


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


@router.post("/upload/", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    logger.info("Upload request received: filename=%s", file.filename)

    if not file.filename:
        logger.warning("Upload rejected: no filename")
        raise HTTPException(status_code=400, detail="No filename provided")

    if not allowed_file(file.filename):
        logger.warning("Upload rejected: unsupported type %s", file.filename)
        raise HTTPException(
            status_code=400,
            detail=f"File type not supported. Allowed: {ALLOWED_STR}",
        )

    content_bytes = await file.read()
    file_size = len(content_bytes)
    logger.info("File read: filename=%s size=%d bytes", file.filename, file_size)

    ts = datetime.now(timezone.utc).isoformat()
    disk_path = save_upload(content_bytes, file.filename, settings.upload_dir)
    logger.info("File saved: path=%s size=%d timestamp=%s", disk_path, file_size, ts)

    try:
        parsed_text = extract_text(disk_path)
    except Exception:
        parsed_text = ""

    doc_id = None
    try:
        payload = DocumentCreate(
            title=file.filename,
            content=parsed_text,
            source=file.filename,
        )
        doc = await create_document(db, payload)
        doc_id = doc.id
    except Exception:
        pass

    if parsed_text:
        langchain_docs = chunk_text(parsed_text, source=file.filename)
        chunk_dicts = [
            {
                "chunk_index": d.metadata["chunk_index"],
                "content": d.page_content,
                "source": file.filename,
            }
            for d in langchain_docs
        ]
        try:
            await store_chunks_db(db, doc_id, chunk_dicts)
        except Exception:
            pass
        try:
            await asyncio.wait_for(
                asyncio.to_thread(
                    store_chunk_vectors, chunk_dicts,
                    filename=file.filename, doc_id=doc_id,
                ),
                timeout=5,
            )
        except Exception:
            pass

    logger.info(
        "Upload complete: filename=%s size=%d parsed=%d chars",
        file.filename, file_size, len(parsed_text),
    )

    return UploadResponse(
        filename=file.filename,
        size=file_size,
        upload_timestamp=datetime.now(timezone.utc),
        content_preview=parsed_text[:200] if parsed_text else None,
    )
