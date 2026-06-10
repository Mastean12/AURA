import asyncio
import logging

from app.services.ai_service import generate_response_async, _USER_FRIENDLY_ERROR
from app.models.schemas import ChatMessage, ChatResponse

logger = logging.getLogger(__name__)


def _build_chat_prompt(messages: list[ChatMessage]) -> list[dict]:
    prompt = [
        {
            "role": "system",
            "content": "You are AURA, an AI assistant. Answer the user's question to the best of your ability.",
        },
    ]
    for msg in messages:
        prompt.append({"role": msg.role, "content": msg.content})
    return prompt


async def chat_with_history(messages: list[ChatMessage]) -> ChatResponse:
    try:
        prompt = _build_chat_prompt(messages)
        reply = await generate_response_async(prompt)
        return ChatResponse(reply=reply)
    except Exception as e:
        logger.warning("Chat AI call failed: %s", e)
        return ChatResponse(reply=_USER_FRIENDLY_ERROR)
