import json
import logging

from sqlalchemy import select

from app.database.database import get_session_factory
from app.models.session import ChatSession
from app.models.schemas import ChatMessage

logger = logging.getLogger(__name__)


async def store_query(
    session_id: str,
    user_query: str,
    ai_response: str,
    sources: list[str] | None = None,
    confidence: float | None = None,
) -> None:
    try:
        async with get_session_factory()() as db:
            entry = ChatSession(
                session_id=session_id,
                user_query=user_query,
                ai_response=ai_response,
                sources=json.dumps(sources) if sources else None,
                confidence=confidence,
            )
            db.add(entry)
            await db.commit()
    except Exception as e:
        logger.warning("Failed to store session memory: %s", e)


async def get_history(session_id: str) -> list[ChatMessage]:
    try:
        async with get_session_factory()() as db:
            result = await db.execute(
                select(ChatSession)
                .where(ChatSession.session_id == session_id)
                .order_by(ChatSession.created_at.asc())
            )
            rows = result.scalars().all()

        messages: list[ChatMessage] = []
        for row in rows:
            messages.append(ChatMessage(role="user", content=row.user_query))
            messages.append(ChatMessage(role="assistant", content=row.ai_response))
        return messages
    except Exception as e:
        logger.warning("Failed to retrieve session history: %s", e)
        return []
