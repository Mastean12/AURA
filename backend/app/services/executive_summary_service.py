import json
import logging

from app.services.ai_service import generate_response
from app.database.database import get_session_factory
from app.models.document import Document
from app.services.rag_service import answer_question as rag_query
from sqlalchemy import select

logger = logging.getLogger(__name__)


async def generate_executive_summary_enhanced(doc_ids: list[int] | None = None) -> dict:
    if not doc_ids:
        return {"summary": "No documents provided.", "confidence": 0.0}

    context_parts = []
    source_refs = []
    for did in doc_ids:
        try:
            async with get_session_factory()() as db:
                result = await db.execute(select(Document).where(Document.id == did))
                doc = result.scalar_one_or_none()
                if doc:
                    preview = doc.content[:2000] if doc.content else ""
                    context_parts.append(f"--- {doc.title} ---\n{preview}")
                    source_refs.append(doc.title)
        except Exception:
            pass

    combined = "\n\n".join(context_parts) if context_parts else ""
    if not combined:
        return {"summary": "No document content available.", "confidence": 0.0}

    prompt = f"""You are an AI executive analyst. Based on the following documents, generate a concise executive summary.

Return ONLY valid JSON:
{{
  "summary": "2-4 sentence executive summary covering: what happened, why it matters, and what leadership should know.",
  "key_findings": ["finding 1", "finding 2", "finding 3"],
  "business_impact": "1-2 sentences on business implications.",
  "strategic_implications": "1-2 sentences on strategic considerations.",
  "confidence": 85
}}

Documents:
{combined}
"""

    try:
        raw = generate_response(prompt)
        raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        result = json.loads(raw)
    except Exception as e:
        logger.warning("Executive summary generation failed: %s", e)
        result = {"summary": "", "key_findings": [], "business_impact": "", "strategic_implications": "", "confidence": 0}

    result.setdefault("summary", "")
    result.setdefault("key_findings", [])
    result.setdefault("business_impact", "")
    result.setdefault("strategic_implications", "")
    result.setdefault("confidence", 0)
    result["sources"] = source_refs

    return result
