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


async def create_document(db: AsyncSession, payload: DocumentCreate, org_id: int | None = None, user_id: int | None = None) -> Document:
    doc = Document(
        title=payload.title,
        content=payload.content,
        source=payload.source,
        file_type=classify_file_type(payload.title),
        organization_id=org_id,
        uploaded_by=user_id,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)
    return doc


async def list_documents(db: AsyncSession, org_id: int | None = None) -> list[Document]:
    query = select(Document).order_by(Document.created_at.desc())
    if org_id is not None:
        query = query.where(Document.organization_id == org_id)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_document(db: AsyncSession, doc_id: int, org_id: int | None = None) -> Document:
    doc = await db.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if org_id is not None and doc.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


async def delete_document(db: AsyncSession, doc_id: int, org_id: int | None = None) -> None:
    doc = await db.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if org_id is not None and doc.organization_id != org_id:
        raise HTTPException(status_code=404, detail="Document not found")
    await db.delete(doc)
    await db.commit()


async def bulk_delete_documents(db: AsyncSession, doc_ids: list[int], org_id: int | None = None) -> int:
    deleted = 0
    for did in doc_ids:
        doc = await db.get(Document, did)
        if doc and (org_id is None or doc.organization_id == org_id):
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
