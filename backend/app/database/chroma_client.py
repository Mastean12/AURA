import logging
from functools import lru_cache

import httpx
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


def _chroma_reachable() -> bool:
    url = f"http://{settings.chroma_host}:{settings.chroma_port}/api/v1/heartbeat"
    try:
        r = httpx.get(url, timeout=2)
        return r.status_code == 200
    except Exception:
        return False


@lru_cache()
def get_chroma_client():
    if not _chroma_reachable():
        logger.warning("ChromaDB not reachable at %s:%s", settings.chroma_host, settings.chroma_port)
        return None
    return chromadb.HttpClient(
        host=settings.chroma_host,
        port=settings.chroma_port,
        settings=ChromaSettings(
            anonymized_telemetry=False,
            chroma_server_connect_timeout=5,
            chroma_server_read_timeout=30,
        ),
    )


def get_or_create_collection(name: str | None = None):
    client = get_chroma_client()
    if client is None:
        raise ConnectionError("ChromaDB server is not reachable")
    collection_name = name or settings.chroma_collection
    return client.get_or_create_collection(collection_name)
