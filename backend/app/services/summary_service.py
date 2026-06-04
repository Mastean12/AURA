import asyncio
import json

from langchain_core.prompts import ChatPromptTemplate

from app.services.llm import get_llm
from app.models.schemas import SummaryResponse

SUMMARY_TYPES = {
    1: "executive_summary",
    2: "key_findings",
    3: "recommendations",
    4: "risks",
}

PROMPTS = {
    1: ChatPromptTemplate.from_messages([
        (
            "system",
            "You are an AI analyst. Generate an executive summary of the following document. "
            "Return ONLY valid JSON with no markdown or explanation:\n"
            '{{\n'
            '  "title": "concise title of the summary",\n'
            '  "summary": "2-3 paragraph overview capturing the essence",\n'
            '  "key_points": ["point 1", "point 2", "point 3"]\n'
            "}}\n\nDocument:\n{document}",
        ),
        ("human", "Generate the executive summary."),
    ]),
    2: ChatPromptTemplate.from_messages([
        (
            "system",
            "You are an AI analyst. Extract the key findings from the following document. "
            "Return ONLY valid JSON with no markdown or explanation:\n"
            '{{\n'
            '  "findings": [\n'
            '    {{"finding": "description of finding 1", "significance": "high"}},\n'
            '    {{"finding": "description of finding 2", "significance": "medium"}}\n'
            "  ]\n"
            "}}\n\nDocument:\n{document}",
        ),
        ("human", "Extract the key findings."),
    ]),
    3: ChatPromptTemplate.from_messages([
        (
            "system",
            "You are an AI analyst. Generate actionable recommendations based on the following document. "
            "Return ONLY valid JSON with no markdown or explanation:\n"
            '{{\n'
            '  "recommendations": [\n'
            '    {{"recommendation": "action item 1", "priority": "high", "impact": "expected outcome"}},\n'
            '    {{"recommendation": "action item 2", "priority": "medium", "impact": "expected outcome"}}\n'
            "  ]\n"
            "}}\n\nDocument:\n{document}",
        ),
        ("human", "Generate recommendations."),
    ]),
    4: ChatPromptTemplate.from_messages([
        (
            "system",
            "You are an AI analyst. Identify risks and mitigation strategies from the following document. "
            "Return ONLY valid JSON with no markdown or explanation:\n"
            '{{\n'
            '  "risks": [\n'
            '    {{"risk": "description of risk 1", "severity": "high", "mitigation": "how to address"}},\n'
            '    {{"risk": "description of risk 2", "severity": "medium", "mitigation": "how to address"}}\n'
            "  ]\n"
            "}}\n\nDocument:\n{document}",
        ),
        ("human", "Identify risks."),
    ]),
}


async def summarize_document(doc_id: int, summary_type: int = 1) -> SummaryResponse:
    try:
        from app.database.database import get_session_factory
        from app.models.document import Document
        from sqlalchemy import select

        async with get_session_factory()() as db:
            result = await db.execute(select(Document).where(Document.id == doc_id))
            doc = result.scalar_one_or_none()
    except Exception:
        doc = None

    if not doc:
        return SummaryResponse(
            summary_type=SUMMARY_TYPES.get(summary_type, "unknown"),
            content=[{"error": "Document not found"}],
            doc_id=doc_id,
        )

    try:
        llm = get_llm()
    except Exception as e:
        return SummaryResponse(
            summary_type=SUMMARY_TYPES.get(summary_type, "unknown"),
            content=[{"error": f"LLM unavailable: {e}"}],
            doc_id=doc_id,
        )

    type_name = SUMMARY_TYPES.get(summary_type, "executive_summary")
    prompt = PROMPTS.get(summary_type, PROMPTS[1])

    truncated = doc.content[:10000]
    messages = prompt.format_messages(document=truncated)
    response = await asyncio.to_thread(llm.invoke, messages)
    raw = response.content.strip()

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
