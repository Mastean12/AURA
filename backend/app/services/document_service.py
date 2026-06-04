from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.models.chunk import Chunk
from app.models.schemas import DocumentCreate


async def create_document(db: AsyncSession, payload: DocumentCreate) -> Document:
    doc = Document(title=payload.title, content=payload.content, source=payload.source)
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
