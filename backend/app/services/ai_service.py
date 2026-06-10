import logging
from typing import Any

from app.config import get_settings
from app.services.gemini_client import generate_with_retry, _USER_FRIENDLY_ERROR

logger = logging.getLogger(__name__)


def get_ai_provider() -> str:
    return get_settings().ai_provider.lower()


def generate_response(prompt: str | list[dict]) -> str:
    provider = get_ai_provider()
    if provider == "gemini":
        return _gemini_generate(prompt)
    elif provider == "openai":
        return _openai_generate(prompt)
    else:
        raise ValueError(f"Unknown AI_PROVIDER: {provider}")


async def generate_response_async(prompt: str | list[dict]) -> str:
    import asyncio
    return await asyncio.to_thread(generate_response, prompt)


def _format_prompt_text(prompt: str | list[dict]) -> str:
    if isinstance(prompt, str):
        return prompt
    parts = []
    for msg in prompt:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        parts.append(f"{role}: {content}")
    return "\n".join(parts)


# --- Gemini ---

def _gemini_generate(prompt: str | list[dict]) -> str:
    settings = get_settings()
    return generate_with_retry(prompt, settings.gemini_api_key)


# --- OpenAI ---

def _openai_generate(prompt: str | list[dict]) -> str:
    from openai import OpenAI

    settings = get_settings()
    client = OpenAI(api_key=settings.openai_api_key)

    if isinstance(prompt, str):
        messages = [{"role": "user", "content": prompt}]
    else:
        messages = prompt

    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=messages,
    )
    return response.choices[0].message.content or ""


def get_available_providers() -> dict[str, bool]:
    settings = get_settings()
    return {
        "gemini": bool(settings.gemini_api_key),
        "openai": bool(settings.openai_api_key),
        "active": settings.ai_provider.lower(),
    }
