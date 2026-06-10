import json
import logging

from app.services.ai_service import generate_response_async, _USER_FRIENDLY_ERROR
from app.models.schemas import SummaryResponse

logger = logging.getLogger(__name__)

SUMMARY_TYPES = {
    1: "executive_summary",
    2: "key_findings",
    3: "recommendations",
    4: "risks",
}

PROMPTS = {
    1: (
        "You are an AI analyst. Generate an executive summary of the following document. "
        "Return ONLY valid JSON with no markdown or explanation:\n"
        '{\n'
        '  "title": "concise title of the summary",\n'
        '  "summary": "2-3 paragraph overview capturing the essence",\n'
        '  "key_points": ["point 1", "point 2", "point 3"]\n'
        "}\n\nDocument:\n{document}"
    ),
    2: (
        "You are an AI analyst. Extract the key findings from the following document. "
        "Return ONLY valid JSON with no markdown or explanation:\n"
        '{\n'
        '  "findings": [\n'
        '    {"finding": "description of finding 1", "significance": "high"},\n'
        '    {"finding": "description of finding 2", "significance": "medium"}\n'
        "  ]\n"
        "}\n\nDocument:\n{document}"
    ),
    3: (
        "You are an AI analyst. Generate actionable recommendations based on the following document. "
        "Return ONLY valid JSON with no markdown or explanation:\n"
        '{\n'
        '  "recommendations": [\n'
        '    {"recommendation": "action item 1", "priority": "high", "impact": "expected outcome"},\n'
        '    {"recommendation": "action item 2", "priority": "medium", "impact": "expected outcome"}\n'
        "  ]\n"
        "}\n\nDocument:\n{document}"
    ),
    4: (
        "You are an AI analyst. Identify risks and mitigation strategies from the following document. "
        "Return ONLY valid JSON with no markdown or explanation:\n"
        '{\n'
        '  "risks": [\n'
        '    {"risk": "description of risk 1", "severity": "high", "mitigation": "how to address"},\n'
        '    {"risk": "description of risk 2", "severity": "medium", "mitigation": "how to address"}\n'
        "  ]\n"
        "}\n\nDocument:\n{document}"
    ),
}


async def summarize_document(doc_id: int, summary_type: int = 1) -> SummaryResponse:
    doc = None
    try:
        from app.database.database import get_session_factory
        from app.models.document import Document
        from sqlalchemy import select

        async with get_session_factory()() as db:
            result = await db.execute(select(Document).where(Document.id == doc_id))
            doc = result.scalar_one_or_none()
    except Exception:
        pass

    if not doc:
        return SummaryResponse(
            summary_type=SUMMARY_TYPES.get(summary_type, "unknown"),
            content=[{"error": "Document not found"}],
            doc_id=doc_id,
        )

    type_name = SUMMARY_TYPES.get(summary_type, "executive_summary")
    prompt_template = PROMPTS.get(summary_type, PROMPTS[1])
    truncated = doc.content[:10000]
    prompt = prompt_template.format(document=truncated)

    try:
        raw = await generate_response_async(prompt)
    except Exception as e:
        logger.warning("Summary AI call failed: %s", e)
        return SummaryResponse(
            summary_type=type_name,
            content=[{"error": _USER_FRIENDLY_ERROR}],
            doc_id=doc_id,
        )

    raw = raw.strip()
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        content = json.loads(raw)
        if isinstance(content, dict):
            content = [content]
    except json.JSONDecodeError:
        content = [{"raw": raw}]

    return SummaryResponse(
        summary_type=type_name,
        content=content,
        doc_id=doc_id,
    )
