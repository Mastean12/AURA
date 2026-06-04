import asyncio
import uuid

from langchain_core.prompts import ChatPromptTemplate

from app.services.llm import get_llm
from app.services.embedding_service import search_vectorstore
from app.services.session_service import store_query
from app.models.schemas import QueryResponse

CHROMA_TIMEOUT = 4

RAG_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are AURA, an AI assistant. Answer the question using only the context provided. "
        "If the context does not contain enough information, say so. "
        "Cite the source filename when referencing specific information.\n\nContext:\n{context}",
    ),
    ("human", "{question}"),
])


def _compute_confidence(results: list[dict]) -> float:
    if not results:
        return 0.0
    scores = [r.get("score", 0) for r in results]
    avg_distance = sum(scores) / len(scores)
    confidence = 1.0 / (1.0 + avg_distance)
    return round(confidence, 4)


def _format_context(results: list[dict]) -> str:
    blocks = []
    for i, r in enumerate(results):
        meta = r.get("metadata", {})
        filename = meta.get("filename", "unknown")
        blocks.append(f"[Source {i + 1}] ({filename})\n{r['content']}")
    return "\n\n".join(blocks)


def _extract_sources(results: list[dict]) -> list[str]:
    seen = set()
    sources = []
    for r in results:
        fn = r.get("metadata", {}).get("filename", "unknown")
        if fn not in seen:
            seen.add(fn)
            sources.append(fn)
    return sources


async def answer_question(
    question: str,
    k: int = 5,
    session_id: str | None = None,
) -> QueryResponse:
    if not session_id:
        session_id = str(uuid.uuid4())

    try:
        results = await asyncio.wait_for(
            asyncio.to_thread(search_vectorstore, question, k),
            timeout=CHROMA_TIMEOUT,
        )
    except Exception:
        results = []

    if not results:
        response = QueryResponse(
            answer="No relevant documents found.",
            sources=[],
            confidence=0.0,
            session_id=session_id,
        )
    else:
        try:
            llm = get_llm()
        except Exception as e:
            response = QueryResponse(
                answer=f"LLM unavailable: {e}",
                sources=[],
                confidence=0.0,
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

        context = _format_context(results)
        sources = _extract_sources(results)
        confidence = _compute_confidence(results)

        prompt = RAG_PROMPT.format_messages(context=context, question=question)
        llm_response = await asyncio.to_thread(llm.invoke, prompt)

        response = QueryResponse(
            answer=llm_response.content,
            sources=sources,
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
