import asyncio
import logging
import uuid

from app.services.ai_service import generate_response_async, _USER_FRIENDLY_ERROR
from app.services.retrieval_service import retrieve
from app.services.session_service import store_query
from app.models.schemas import QueryResponse

logger = logging.getLogger(__name__)

CHROMA_TIMEOUT = 4


def _build_rag_prompt(context: str, question: str, sources: list[str]) -> list[dict]:
    source_refs = "\n".join(f"- {s}" for s in sources) if sources else "No specific sources."
    return [
        {
            "role": "system",
            "content": (
                "You are AURA, an AI Business Intelligence and Document Intelligence Analyst.\n\n"
                "Rules:\n"
                "- Answer only using the provided context below.\n"
                "- If the information is not in the context, say so clearly.\n"
                "- Do not hallucinate or make up information.\n"
                "- Cite the relevant document filenames when you reference specific information.\n\n"
                f"Sources Available:\n{source_refs}\n\n"
                f"Context:\n{context}"
            ),
        },
        {"role": "user", "content": question},
    ]


def _format_context(results: list[dict]) -> str:
    blocks = []
    for i, r in enumerate(results):
        meta = r.get("metadata", {})
        filename = meta.get("filename", "unknown")
        chunk_idx = meta.get("chunk_index", "?")
        blocks.append(f"[Source {i + 1}] ({filename} - Chunk {chunk_idx})\n{r['content']}")
    return "\n\n".join(blocks)


def _extract_sources(results: list[dict]) -> list[dict]:
    seen = set()
    sources = []
    for r in results:
        meta = r.get("metadata", {})
        fn = meta.get("filename", "unknown")
        doc_id = meta.get("doc_id", "unknown")
        if fn not in seen:
            seen.add(fn)
            sources.append({"filename": fn, "doc_id": doc_id})
    return sources


def _compute_confidence(results: list[dict]) -> float:
    if not results:
        return 0.0
    scores = [r.get("score", 0) for r in results]
    avg_distance = sum(scores) / len(scores)
    confidence = 1.0 / (1.0 + avg_distance)
    return round(confidence, 4)


async def answer_question(
    question: str,
    k: int = 5,
    session_id: str | None = None,
    doc_id: int | None = None,
) -> QueryResponse:
    if not session_id:
        session_id = str(uuid.uuid4())

    try:
        results = await asyncio.wait_for(
            asyncio.to_thread(retrieve, question, k, doc_id),
            timeout=CHROMA_TIMEOUT,
        )
    except Exception as e:
        logger.warning("Retrieval failed: %s", e)
        results = []

    if not results:
        response = QueryResponse(
            answer="No relevant documents found. Please upload and process documents first.",
            sources=[],
            confidence=0.0,
            session_id=session_id,
        )
    else:
        context = _format_context(results)
        sources = _extract_sources(results)
        source_names = [s["filename"] for s in sources]
        confidence = _compute_confidence(results)

        try:
            prompt = _build_rag_prompt(context, question, source_names)
            answer = await generate_response_async(prompt, request_type="rag")
        except Exception as e:
            logger.warning("RAG AI call failed: %s", e)
            answer = _USER_FRIENDLY_ERROR

        response = QueryResponse(
            answer=answer,
            sources=source_names,
            confidence=confidence,
            session_id=session_id,
        )

    await store_query(
        session_id=session_id,
        user_query=question,
        ai_response=response.answer,
        sources=response.sources,
        confidence=response.confidence,
    )

    return response
