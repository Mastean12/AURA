import logging
import time
from typing import Any

logger = logging.getLogger(__name__)

PRIMARY_MODEL = "gemini-2.5-flash"
FALLBACK_MODEL = "gemini-2.0-flash"
MAX_RETRIES = 3
BASE_DELAY = 2.0

RETRYABLE_CODES = {429, 500, 502, 503, 504}

_USER_FRIENDLY_ERROR = "AI analysis temporarily unavailable. Please try again shortly."


def _import_genai():
    import google.genai as genai
    return genai


def _format_prompt_text(prompt: str | list[dict]) -> str:
    if isinstance(prompt, str):
        return prompt
    parts = []
    for msg in prompt:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        parts.append(f"{role}: {content}")
    return "\n".join(parts)


def _is_retryable(error: Exception) -> bool:
    msg = str(error).lower()
    codes = [str(c) for c in RETRYABLE_CODES]
    return any(c in msg for c in codes) or any(kw in msg for kw in ["unavailable", "timeout", "overloaded", "too many"])


def _is_quota_exhausted(error: Exception) -> bool:
    msg = str(error).lower()
    return "quota exceeded" in msg or "resource_exhausted" in msg


def generate_gemini(prompt: str | list[dict], api_key: str, model: str | None = None) -> str:
    genai = _import_genai()
    client = genai.Client(api_key=api_key)
    text = _format_prompt_text(prompt) if isinstance(prompt, list) else prompt
    active_model = model or PRIMARY_MODEL
    response = client.models.generate_content(
        model=active_model,
        contents=text,
        config={"max_output_tokens": 2048, "temperature": 0.3},
    )
    return response.text


def generate_with_retry(prompt: str | list[dict], api_key: str) -> str:
    last_error: Exception | None = None
    retry_count = 0

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            result = generate_gemini(prompt, api_key, model=PRIMARY_MODEL)
            return result
        except Exception as e:
            logger.warning("Gemini attempt %d/%d failed (model=%s): %s", attempt, MAX_RETRIES, PRIMARY_MODEL, e)
            last_error = e

            if _is_quota_exhausted(e):
                logger.warning("Quota exhausted — skipping remaining primary retries")
                break

            if attempt < MAX_RETRIES and _is_retryable(e):
                retry_count += 1
                delay = BASE_DELAY * (2 ** (attempt - 1))
                logger.info("Retrying in %.0fs (attempt %d)...", delay, attempt + 1)
                time.sleep(delay)
            elif not _is_retryable(e):
                logger.warning("Non-retryable error: %s", e)
                break

    logger.warning("Primary model failed after %d retries, trying fallback model %s", MAX_RETRIES, FALLBACK_MODEL)
    try:
        result = generate_gemini(prompt, api_key, model=FALLBACK_MODEL)
        logger.info("Fallback model %s succeeded", FALLBACK_MODEL)
        return result
    except Exception as e:
        logger.error("Fallback model also failed: %s", e)
        last_error = e

    raise RuntimeError(_USER_FRIENDLY_ERROR) from last_error
