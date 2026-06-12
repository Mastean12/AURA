import hashlib
import logging
import time

from app.config import get_settings
from app.database.chroma_client import get_or_create_collection
from app.database.database import get_session_factory
from app.models.embedding_meta import EmbeddingMetadata

logger = logging.getLogger(__name__)

EMBEDDING_MODEL = "text-embedding-004"
_BATCH_SIZE = 10
_embedding_cache: dict[str, list[float]] = {}


def _embed_batch(texts: list[str]) -> list[list[float]]:
    settings = get_settings()
    import google.genai as genai
    client = genai.Client(api_key=settings.gemini_api_key)
    result = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=texts,
    )
    return [e.values for e in result.embeddings]


def _get_cache_key(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def embed_text(text: str) -> list[float]:
    key = _get_cache_key(text)
    if key in _embedding_cache:
        return _embedding_cache[key]
    result = _embed_batch([text])[0]
    _embedding_cache[key] = result
    return result


def embed_documents(texts: list[str]) -> list[list[float]]:
    uncached_indices = []
    uncached_texts = []
    for i, t in enumerate(texts):
        key = _get_cache_key(t)
        if key in _embedding_cache:
            continue
        uncached_indices.append(i)
        uncached_texts.append(t)

    if uncached_texts:
        for start in range(0, len(uncached_texts), _BATCH_SIZE):
            batch = uncached_texts[start:start + _BATCH_SIZE]
            try:
                embeddings = _embed_batch(batch)
                for j, emb in enumerate(embeddings):
                    idx = uncached_indices[start + j]
                    key = _get_cache_key(batch[j])
                    _embedding_cache[key] = emb
            except Exception as e:
                logger.warning("Embedding batch failed: %s", e)

    return [_embedding_cache[_get_cache_key(t)] for t in texts]


async def get_embedding_status(doc_id: int) -> dict | None:
    try:
        async with get_session_factory()() as db:
            from sqlalchemy import select
            result = await db.execute(
                select(EmbeddingMetadata).where(EmbeddingMetadata.doc_id == doc_id)
            )
            entry = result.scalar_one_or_none()
            if entry:
                return {"status": entry.status, "chunk_count": entry.chunk_count, "model": entry.embedding_model}
    except Exception:
        pass
    return None


async def set_embedding_status(doc_id: int, status: str, chunk_count: int = 0):
    try:
        async with get_session_factory()() as db:
            from sqlalchemy import select
            result = await db.execute(
                select(EmbeddingMetadata).where(EmbeddingMetadata.doc_id == doc_id)
            )
            entry = result.scalar_one_or_none()
            if entry:
                entry.status = status
                entry.chunk_count = chunk_count
                entry.embedding_model = EMBEDDING_MODEL
            else:
                entry = EmbeddingMetadata(
                    doc_id=doc_id,
                    chunk_count=chunk_count,
                    embedding_model=EMBEDDING_MODEL,
                    status=status,
                )
                db.add(entry)
            await db.commit()
    except Exception as e:
        logger.warning("Failed to update embedding status: %s", e)


def store_chunk_vectors(chunks: list[dict], filename: str, doc_id: int | None = None) -> None:
    if not chunks:
        return
    collection = get_or_create_collection()
    ids = []
    documents = []
    metadatas = []

    for chunk in chunks:
        cid = chunk.get("chunk_id", chunk.get("chunk_index", 0))
        ids.append(f"{doc_id or filename}_{cid}")
        documents.append(chunk["content"])
        metadatas.append({
            "filename": filename,
            "doc_id": str(doc_id) if doc_id else filename,
            "chunk_id": str(cid),
            "chunk_index": chunk.get("chunk_index", 0),
            "source": chunk.get("source", filename),
        })

    embeddings = embed_documents(documents)
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )
    logger.info("Stored %d chunk vectors for doc_id=%s", len(chunks), doc_id)


def search_vectorstore(query: str, k: int = 5, filter_doc_id: int | None = None) -> list[dict]:
    collection = get_or_create_collection()
    where = {"doc_id": str(filter_doc_id)} if filter_doc_id else None
    results = collection.query(
        query_texts=[query],
        n_results=k,
        where=where,
    )
    docs = []
    for i in range(len(results["ids"][0])):
        docs.append({
            "id": results["ids"][0][i],
            "content": results["documents"][0][i],
            "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
            "score": results["distances"][0][i] if results["distances"] else 0,
        })
    return docs
