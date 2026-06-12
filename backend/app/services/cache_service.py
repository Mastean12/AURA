import hashlib
import json
import logging
from datetime import datetime, timezone

from sqlalchemy import select, func

from app.database.database import get_session_factory
from app.models.ai_cache import AICache

logger = logging.getLogger(__name__)

CACHE_TTL_SECONDS = 86400 * 30


def compute_doc_hash(content: str) -> str:
    return hashlib.sha256((content or "").encode("utf-8")).hexdigest()


async def get_cached(doc_id: int, doc_hash: str, result_type: str) -> dict | None:
    try:
        async with get_session_factory()() as db:
            result = await db.execute(
                select(AICache).where(
                    AICache.doc_id == doc_id,
                    AICache.doc_hash == doc_hash,
                    AICache.result_type == result_type,
                )
            )
            entry = result.scalar_one_or_none()
            if entry:
                entry.hit_count = (entry.hit_count or 0) + 1
                await db.commit()
                try:
                    return json.loads(entry.response)
                except (json.JSONDecodeError, TypeError):
                    return {"raw": entry.response}
    except Exception as e:
        logger.warning("Cache read failed: %s", e)
    return None


async def set_cached(doc_id: int, doc_hash: str, result_type: str, response: dict | str):
    try:
        serialized = json.dumps(response) if isinstance(response, dict) else response
        async with get_session_factory()() as db:
            existing = await db.execute(
                select(AICache).where(
                    AICache.doc_id == doc_id,
                    AICache.result_type == result_type,
                )
            )
            entry = existing.scalar_one_or_none()
            if entry:
                entry.doc_hash = doc_hash
                entry.response = serialized
                entry.updated_at = datetime.now(timezone.utc)
            else:
                entry = AICache(
                    doc_id=doc_id,
                    doc_hash=doc_hash,
                    result_type=result_type,
                    response=serialized,
                    hit_count=0,
                )
                db.add(entry)
            await db.commit()
    except Exception as e:
        logger.warning("Cache write failed: %s", e)


async def invalidate_cache(doc_id: int | None = None):
    try:
        async with get_session_factory()() as db:
            if doc_id:
                await db.execute(
                    AICache.__table__.delete().where(AICache.doc_id == doc_id)
                )
            else:
                await db.execute(AICache.__table__.delete())
            await db.commit()
    except Exception as e:
        logger.warning("Cache invalidation failed: %s", e)


async def get_cache_stats() -> dict:
    try:
        async with get_session_factory()() as db:
            total = await db.execute(func.count(AICache.id))
            total_count = total.scalar() or 0
            hits = await db.execute(func.sum(AICache.hit_count))
            total_hits = hits.scalar() or 0
            return {"total_entries": total_count, "total_hits": total_hits}
    except Exception as e:
        logger.warning("Cache stats failed: %s", e)
        return {"total_entries": 0, "total_hits": 0}
