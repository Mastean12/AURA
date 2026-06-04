from fastapi import APIRouter, Depends

from app.models.schemas import QueryRequest, QueryResponse, ChatRequest, ChatResponse
from app.services.rag_service import answer_question
from app.services.chat_service import chat_with_history

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/query", response_model=QueryResponse)
async def query(payload: QueryRequest):
    return await answer_question(
        question=payload.question,
        k=payload.k,
        session_id=payload.session_id,
    )


@router.post("/", response_model=ChatResponse)
async def chat(payload: ChatRequest):
    return await chat_with_history(payload.messages)
