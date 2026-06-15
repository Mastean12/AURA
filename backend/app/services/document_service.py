from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.chunk import Chunk
from app.models.schemas import DocumentCreate


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


async def create_document(db: AsyncSession, payload: DocumentCreate) -> Document:
    doc = Document(
        title=payload.title,
        content=payload.content,
        source=payload.source,
        file_type=classify_file_type(payload.title),
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return doc


async def list_documents(db: AsyncSession) -> list[Document]:
    result = await db.execute(select(Document).order_by(Document.created_at.desc()))
    return list(result.scalars().all())


async def get_document(db: AsyncSession, doc_id: int) -> Document:
    doc = await db.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


async def delete_document(db: AsyncSession, doc_id: int) -> None:
    doc = await db.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    await db.delete(doc)
    await db.commit()


async def bulk_delete_documents(db: AsyncSession, doc_ids: list[int]) -> int:
    deleted = 0
    for did in doc_ids:
        doc = await db.get(Document, did)
        if doc:
            await db.delete(doc)
            deleted += 1
    await db.commit()
    return deleted


async def store_chunks(db: AsyncSession, doc_id: int, chunks: list[dict]) -> None:
    for chunk in chunks:
        db_chunk = Chunk(
            doc_id=doc_id,
            chunk_index=chunk["chunk_index"],
            content=chunk["content"],
            source=chunk.get("source"),
        )
        db.add(db_chunk)
    await db.commit()
