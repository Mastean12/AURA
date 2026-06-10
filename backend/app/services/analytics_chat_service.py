import logging

import pandas as pd

from app.services.ai_service import generate_response
from app.database.database import get_session_factory
from app.models.document import Document
from sqlalchemy import select

logger = logging.getLogger(__name__)

_chat_sessions: dict[str, list[dict]] = {}

_USER_FRIENDLY_ERROR = "AI analysis temporarily unavailable. Please try again shortly."


def _df_summary(df: pd.DataFrame) -> str:
    info = [f"This dataset has {len(df)} rows and {len(df.columns)} columns.", "Columns:"]
    for col in df.columns:
        dtype = "numeric" if pd.api.types.is_numeric_dtype(df[col]) else "categorical"
        missing = int(df[col].isna().sum())
        info.append(f"  - {col} ({dtype}, {missing} missing)")
    return "\n".join(info)


def _build_prompt(question: str, history: list[dict], df_summary: str, sample: str):
    system = f"""You are AURA Analytics, an AI data analyst. You have access to a dataset with these characteristics:

{df_summary}

First 3 rows of data:
{sample}

Answer questions about this dataset. Be specific, cite column names and numbers where possible.
Keep responses concise but informative."""
    messages = [{"role": "system", "content": system}]
    for h in history[-10:]:
        messages.append(h)
    messages.append({"role": "user", "content": question})
    return messages


def _compute_confidence(response_text: str) -> float:
    if not response_text or any(w in response_text.lower() for w in ["insufficient", "cannot", "not able"]):
        return 0.3
    return 0.85


async def chat_analytics(doc_id: int, question: str, session_id: str) -> dict:
    session_key = f"{doc_id}:{session_id}"
    history = _chat_sessions.setdefault(session_key, [])

    try:
        async with get_session_factory()() as db:
            result = await db.execute(select(Document).where(Document.id == doc_id))
            doc = result.scalar_one_or_none()
    except Exception:
        doc = None

    if not doc or not doc.content:
        return {"answer": "Document not found or empty.", "confidence": 0.0}

    df = pd.read_csv(pd.io.common.StringIO(doc.content))
    if df is None or len(df.columns) < 2:
        return {"answer": "Dataset could not be parsed as tabular data.", "confidence": 0.0}

    df_summary = _df_summary(df)
    sample = df.head(3).to_string()
    prompt = _build_prompt(question, history, df_summary, sample)

    try:
        raw = generate_response(prompt)
    except Exception as e:
        logger.warning("Analytics chat failed: %s", e)
        return {"answer": _USER_FRIENDLY_ERROR, "confidence": 0.0}

    confidence = _compute_confidence(raw)
    history.append({"role": "user", "content": question})
    history.append({"role": "assistant", "content": raw})

    return {"answer": raw, "confidence": confidence}
