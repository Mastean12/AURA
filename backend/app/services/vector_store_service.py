import logging

from app.database.chroma_client import get_or_create_collection

logger = logging.getLogger(__name__)


def collection_stats() -> dict:
    try:
        collection = get_or_create_collection()
        count = collection.count()
        return {"collection": collection.name, "chunk_count": count}
    except Exception as e:
        logger.warning("Failed to get collection stats: %s", e)
        return {"collection": "unknown", "chunk_count": 0, "error": str(e)}


def delete_document_vectors(doc_id: int | str) -> int:
    try:
        collection = get_or_create_collection()
        results = collection.get(where={"doc_id": str(doc_id)})
        ids = results.get("ids", [])
        if ids:
            collection.delete(ids=ids)
            logger.info("Deleted %d vectors for doc_id=%s", len(ids), doc_id)
        return len(ids)
    except Exception as e:
        logger.warning("Failed to delete vectors: %s", e)
        return 0
