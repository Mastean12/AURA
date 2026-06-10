import logging
from functools import lru_cache
import logging

from app.config import get_settings
from app.services.ai_service import generate_response_async as ai_generate

logger = logging.getLogger(__name__)


async def generate(prompt: str | list[dict]) -> str:
    return await ai_generate(prompt)


@lru_cache()
def get_embeddings():
    from langchain_openai import OpenAIEmbeddings
    settings = get_settings()
    return OpenAIEmbeddings(
        api_key=settings.openai_api_key,
        model="text-embedding-3-small",
    )
