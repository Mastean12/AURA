import logging
import time

from app.config import get_settings
from app.services.gemini_client import generate_with_retry

logger = logging.getLogger(__name__)

_USER_FRIENDLY_ERROR = "AI analysis temporarily unavailable. Please try again shortly."
_RETRYABLE_OPENAI_CODES = {429, 500, 502, 503, 504}
_OPENAI_MAX_RETRIES = 3
_OPENAI_BASE_DELAY = 2.0


def get_ai_provider() -> str:
    return get_settings().ai_provider.lower()


def _is_retryable_openai(error: Exception) -> bool:
    msg = str(error).lower()
    return any(str(c) in msg for c in _RETRYABLE_OPENAI_CODES) or \
           any(kw in msg for kw in ["rate_limit", "timeout", "unavailable", "overloaded", "server error"])


def generate_response(prompt: str | list[dict]) -> str:
    provider = get_ai_provider()
    if provider == "gemini":
        return _gemini_generate(prompt)
    elif provider == "openai":
        return _openai_generate(prompt)
    else:
        raise ValueError(f"Unknown AI_PROVIDER: {provider}")


async def generate_response_async(prompt: str | list[dict], request_type: str = "general") -> str:
    import asyncio
    start = time.perf_counter()
    retry_count = 0
    success = True
    error_msg = None
    try:
        result = await asyncio.to_thread(generate_response, prompt)
        return result
    except Exception as e:
        success = False
        error_msg = str(e)
        raise
    finally:
        elapsed = int((time.perf_counter() - start) * 1000)
        try:
            from app.services.monitoring_service import log_ai_usage
            settings = get_settings()
            tokens = len(str(prompt)) // 4
            asyncio.ensure_future(log_ai_usage(
                request_type=request_type,
                provider=get_ai_provider(),
                model=settings.gemini_model if get_ai_provider() == "gemini" else settings.openai_model,
                tokens_estimated=tokens,
                latency_ms=elapsed,
                success=success,
                error_message=error_msg,
                retry_count=retry_count,
            ))
        except Exception as log_err:
            logger.warning("Failed to log AI usage: %s", log_err)


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
    client = OpenAI(api_key=settings.openai_api_key, timeout=30.0)

    if isinstance(prompt, str):
        messages = [{"role": "user", "content": prompt}]
    else:
        messages = prompt

    last_error = None
    for attempt in range(1, _OPENAI_MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=settings.openai_model,
                messages=messages,
                max_tokens=2048,
                temperature=0.3,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.warning("OpenAI attempt %d/%d failed: %s", attempt, _OPENAI_MAX_RETRIES, e)
            last_error = e
            if attempt < _OPENAI_MAX_RETRIES and _is_retryable_openai(e):
                delay = _OPENAI_BASE_DELAY * (2 ** (attempt - 1))
                time.sleep(delay)

    raise RuntimeError(_USER_FRIENDLY_ERROR) from last_error


def get_available_providers() -> dict[str, bool]:
    settings = get_settings()
    return {
        "gemini": bool(settings.gemini_api_key),
        "openai": bool(settings.openai_api_key),
        "active": settings.ai_provider.lower(),
    }
