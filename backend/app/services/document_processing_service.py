import asyncio
import logging

from app.database.database import get_session_factory
from app.models.document import Document
from app.services.document_parser import extract_text, extract_metadata, save_upload
from app.services.chunking_service import chunk_text as create_chunks
from app.services.embedding_service import store_chunk_vectors, set_embedding_status
from app.services.document_service import store_chunks
from app.config import get_settings
from sqlalchemy import select

logger = logging.getLogger(__name__)


def classify_file_type(filename: str) -> str:
    ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if ext == "pdf":
        return "PDF"
    elif ext in ("doc", "docx"):
        return "Word"
    elif ext in ("xls", "xlsx", "csv"):
        return "Excel"
    elif ext == "txt":
        return "Text"
    return "Other"


async def process_document(content_bytes: bytes, filename: str) -> int | None:
    settings = get_settings()
    disk_path = save_upload(content_bytes, filename, settings.upload_dir)

    meta = extract_metadata(disk_path)
    parsed_text = extract_text(disk_path)
    file_type = classify_file_type(filename)
    file_size = len(content_bytes)

    async with get_session_factory()() as db:
        from app.models.schemas import DocumentCreate
        payload = DocumentCreate(title=filename, content=parsed_text, source=filename)
        doc = Document(
            title=payload.title,
            content=payload.content,
            source=payload.source,
            file_type=file_type,
            file_size=file_size,
            processing_status="processing",
            page_count=meta.get("page_count", 0),
        )
        db.add(doc)
        await db.commit()
        await db.refresh(doc)
        doc_id = doc.id

    chunks = create_chunks(parsed_text, source=filename, doc_id=doc_id)
    if chunks:
        try:
            async with get_session_factory()() as db:
                await store_chunks(db, doc_id, chunks)
        except Exception as e:
            logger.warning("Chunk DB storage failed: %s", e)

        try:
            await asyncio.wait_for(
                asyncio.to_thread(store_chunk_vectors, chunks, filename=filename, doc_id=doc_id),
                timeout=30,
            )
        except Exception as e:
            logger.warning("Vector storage failed: %s", e)

        try:
            await set_embedding_status(doc_id, "completed", len(chunks))
        except Exception as e:
            logger.warning("Embedding status update failed: %s", e)

    async with get_session_factory()() as db:
        result = await db.execute(select(Document).where(Document.id == doc_id))
        doc = result.scalar_one_or_none()
        if doc:
            doc.processing_status = "completed"
            doc.chunk_count = len(chunks)
            await db.commit()

    logger.info("Document %d processed: %s (%d chunks)", doc_id, filename, len(chunks))
    return doc_id
