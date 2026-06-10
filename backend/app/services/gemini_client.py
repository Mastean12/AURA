import logging
import time
from typing import Any

logger = logging.getLogger(__name__)

PRIMARY_MODEL = "gemini-2.5-flash"
FALLBACK_MODEL = "gemini-2.0-flash"
MAX_RETRIES = 3
BASE_DELAY = 2.0

_USER_FRIENDLY_ERROR = "AI analysis temporarily unavailable. Please try again shortly."


def _import_genai():
    try:
        import google.genai as genai
        return genai
    except ImportError:
        import sys as _sys
        import os as _os
        _user_site = _os.path.join(
            _os.environ.get("LOCALAPPDATA", ""),
            "Packages", "PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0",
            "LocalCache", "local-packages", "Python312", "site-packages"
        )
        if _os.path.isdir(_user_site) and _user_site not in _sys.path:
            _sys.path.insert(0, _user_site)
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


def generate_gemini(prompt: str | list[dict], api_key: str, model: str | None = None) -> str:
    genai = _import_genai()
    client = genai.Client(api_key=api_key)
    text = _format_prompt_text(prompt) if isinstance(prompt, list) else prompt
    active_model = model or PRIMARY_MODEL
    response = client.models.generate_content(
        model=active_model,
        contents=text,
    )
    return response.text


def generate_with_retry(prompt: str | list[dict], api_key: str) -> str:
    last_error: Exception | None = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return generate_gemini(prompt, api_key, model=PRIMARY_MODEL)
        except Exception as e:
            logger.warning("Gemini attempt %d/%d failed (model=%s): %s", attempt, MAX_RETRIES, PRIMARY_MODEL, e)
            last_error = e
            if attempt < MAX_RETRIES:
                delay = BASE_DELAY * (2 ** (attempt - 1))
                logger.info("Retrying in %.0fs...", delay)
                time.sleep(delay)

    logger.warning("Primary model failed after %d retries, trying fallback model %s", MAX_RETRIES, FALLBACK_MODEL)
    try:
        return generate_gemini(prompt, api_key, model=FALLBACK_MODEL)
    except Exception as e:
        logger.error("Fallback model also failed: %s", e)
        last_error = e

    raise RuntimeError(_USER_FRIENDLY_ERROR) from last_error
