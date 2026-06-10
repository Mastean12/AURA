import logging

from app.database.database import get_session_factory
from app.models.document import Document
from app.services.ai_service import generate_response
from app.services.insights_service import generate_insights
from sqlalchemy import select

logger = logging.getLogger(__name__)


async def analyze_multi_document(doc_ids: list[int]) -> dict:
    logger.info("Multi-document analysis for %d docs", len(doc_ids))
    docs: list[Document] = []
    try:
        async with get_session_factory()() as db:
            for did in doc_ids:
                result = await db.execute(select(Document).where(Document.id == did))
                d = result.scalar_one_or_none()
                if d:
                    docs.append(d)
    except Exception as e:
        logger.warning("DB error: %s", e)

    if len(docs) < 1:
        return {"doc_count": 0, "consolidated_summary": "", "themes": [], "conflicts": [], "cross_references": [], "total_insights": [], "confidence": 0}

    doc_summaries = []
    all_insights: list[str] = []
    for d in docs:
        title = d.title or f"Doc #{d.id}"
        preview = d.content[:300] if d.content else ""
        doc_summaries.append(f"--- {title} ---\n{preview}")
        try:
            ins = await generate_insights(d.id)
            all_insights.extend(ins.get("key_findings", []))
        except Exception:
            pass

    combined = "\n\n".join(doc_summaries)

    prompt = (
        f"Analyze these {len(docs)} organizational documents together:\n\n{combined}\n\n"
        "Return ONLY valid JSON:\n"
        '{"consolidated_summary": "2-3 sentence unified summary", '
        '"themes": ["theme 1", "theme 2", "theme 3"], '
        '"conflicts": ["conflict 1 between docs"] if any, or [], '
        '"cross_references": ["cross-reference 1"] if applicable, or []}'
    )

    try:
        raw = generate_response(prompt)
        raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        import json
        result = json.loads(raw)
    except Exception as e:
        logger.warning("Multi-doc analysis failed: %s", e)
        result = {"consolidated_summary": "Could not generate consolidated analysis.", "themes": [], "conflicts": [], "cross_references": []}

    return {
        "doc_count": len(docs),
        "consolidated_summary": result.get("consolidated_summary", ""),
        "themes": result.get("themes", []),
        "conflicts": result.get("conflicts", []),
        "cross_references": result.get("cross_references", []),
        "total_insights": all_insights[:10],
        "confidence": round(min(0.5 + len(docs) * 0.1, 0.95), 2),
    }
