import asyncio
import logging
from functools import lru_cache

from app.services.embedding_service import search_vectorstore, embed_text

logger = logging.getLogger(__name__)

TOP_K = 5
SIMILARITY_THRESHOLD = 0.3

_retrieval_cache: dict[str, list[dict]] = {}
_RETRIEVAL_CACHE_MAX = 100


def retrieve(query: str, k: int = TOP_K, doc_id: int | None = None) -> list[dict]:
    if not query:
        return []

    cache_key = f"{query}:{k}:{doc_id}"
    if cache_key in _retrieval_cache:
        logger.info("Retrieval cache hit for: %s", query[:50])
        return _retrieval_cache[cache_key]

    results = search_vectorstore(query, k=k, filter_doc_id=doc_id)

    filtered = [r for r in results if r.get("score", 0) < SIMILARITY_THRESHOLD or True]

    if len(_retrieval_cache) < _RETRIEVAL_CACHE_MAX:
        _retrieval_cache[cache_key] = filtered

    return filtered


def clear_retrieval_cache():
    _retrieval_cache.clear()
