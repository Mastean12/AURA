import asyncio
import logging

from langchain_core.messages import HumanMessage, AIMessage
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from app.services.llm import get_llm, get_embeddings
from app.models.schemas import ChatMessage, ChatResponse

logger = logging.getLogger(__name__)


async def chat_with_history(messages: list[ChatMessage]) -> ChatResponse:
    try:
        llm = get_llm()
    except Exception as e:
        logger.warning("LLM unavailable: %s", e)
        return ChatResponse(reply="AI service is not available right now.")

    try:
        from app.database.chroma_client import get_or_create_collection

        collection = await asyncio.to_thread(get_or_create_collection)
        embeddings = get_embeddings()
        vectorstore = Chroma(
            client=collection._client,
            collection_name=collection.name,
            embedding_function=embeddings,
        )
        retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    except Exception as e:
        logger.warning("Vector store unavailable: %s", e)
        retriever = None

    contextualize_q_prompt = ChatPromptTemplate.from_messages([
        ("system", "Given a chat history and the latest user question, formulate a standalone question."),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])

    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", "You are AURA, an AI assistant. Answer the question based on the context provided."),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])

    if retriever:
        history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_q_prompt)
        question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
        rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
    else:
        # No vector store available, use LLM directly with context-only prompt
        simple_prompt = ChatPromptTemplate.from_messages([
            ("system", "You are AURA, an AI assistant. Answer the user's question to the best of your ability."),
            MessagesPlaceholder("chat_history"),
            ("human", "{input}"),
        ])
        langchain_messages = []
        for msg in messages:
            if msg.role == "user":
                langchain_messages.append(HumanMessage(content=msg.content))
            else:
                langchain_messages.append(AIMessage(content=msg.content))
        result = simple_prompt.format_messages(
            chat_history=langchain_messages[:-1],
            input=messages[-1].content,
        )
        response = await asyncio.to_thread(llm.invoke, result)
        return ChatResponse(reply=response.content)

    langchain_messages = []
    for msg in messages:
        if msg.role == "user":
            langchain_messages.append(HumanMessage(content=msg.content))
        else:
            langchain_messages.append(AIMessage(content=msg.content))

    try:
        result = await asyncio.to_thread(
            rag_chain.invoke,
            {"input": messages[-1].content, "chat_history": langchain_messages[:-1]},
        )
        return ChatResponse(reply=result["answer"])
    except Exception as e:
        logger.warning("RAG chain failed: %s", e)
        prompt = qa_prompt.format_messages(
            chat_history=langchain_messages[:-1],
            input=messages[-1].content,
        )
        response = await asyncio.to_thread(llm.invoke, prompt)
        return ChatResponse(reply=response.content)
