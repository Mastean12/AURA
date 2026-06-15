import logging

from app.database.database import get_session_factory
from app.models.document import Document
from app.services.ai_service import generate_response_async
from sqlalchemy import select

logger = logging.getLogger(__name__)


async def compare_documents(doc_id_a: int, doc_id_b: int, label_a: str = "Document A", label_b: str = "Document B") -> dict:
    logger.info("Comparing docs %d and %d", doc_id_a, doc_id_b)
    docs = []
    try:
        async with get_session_factory()() as db:
            for did in (doc_id_a, doc_id_b):
                result = await db.execute(select(Document).where(Document.id == did))
                d = result.scalar_one_or_none()
                if d:
                    docs.append(d)
    except Exception as e:
        logger.warning("DB error: %s", e)

    if len(docs) < 2:
        return {"similarities": [], "differences": [], "key_changes": [], "recommended_actions": [], "comparison_summary": "", "confidence": 0}

    doc_a_content = docs[0].content[:2000] if docs[0].content else ""
    doc_b_content = docs[1].content[:2000] if docs[1].content else ""

    prompt = (
        f"Compare these two documents and identify key similarities, differences, and changes.\n\n"
        f"--- {label_a} ---\n{doc_a_content}\n\n"
        f"--- {label_b} ---\n{doc_b_content}\n\n"
        "Return ONLY valid JSON:\n"
        '{"similarities": ["sim 1", "sim 2", "sim 3"], '
        '"differences": ["diff 1", "diff 2", "diff 3"], '
        '"key_changes": ["change 1", "change 2"], '
        '"recommended_actions": ["action 1", "action 2", "action 3"], '
        '"comparison_summary": "2-3 sentence summary of the comparison"}'
    )

    try:
        raw = await generate_response_async(prompt, request_type="comparison")
        raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        import json
        result = json.loads(raw)
    except Exception as e:
        logger.warning("Comparison failed: %s", e)
        result = {"similarities": [], "differences": [], "key_changes": [], "recommended_actions": [], "comparison_summary": ""}

    return {
        "similarities": result.get("similarities", []),
        "differences": result.get("differences", []),
        "key_changes": result.get("key_changes", []),
        "recommended_actions": result.get("recommended_actions", []),
        "comparison_summary": result.get("comparison_summary", ""),
        "confidence": round(0.7 if any(result.values()) else 0, 2),
    }
