from app.database.chroma_client import get_or_create_collection
from app.services.llm import get_embeddings


def embed_text(text: str) -> list[float]:
    return get_embeddings().embed_query(text)


def embed_documents(texts: list[str]) -> list[list[float]]:
    return get_embeddings().embed_documents(texts)


def store_chunk_vectors(
    chunks: list[dict],
    filename: str,
    doc_id: int | None = None,
    page: int = 0,
) -> None:
    collection = get_or_create_collection()
    ids = []
    documents = []
    metadatas = []

    for i, chunk in enumerate(chunks):
        chunk_id = chunk.get("chunk_index", i)
        ids.append(f"{doc_id or filename}_{chunk_id}")
        documents.append(chunk["content"])
        metadatas.append({
            "filename": filename,
            "page": page,
            "chunk_id": chunk_id,
            "doc_id": str(doc_id) if doc_id else filename,
        })

    embeddings = embed_documents(documents)
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )


def search_vectorstore(query: str, k: int = 5) -> list[dict]:
    collection = get_or_create_collection()
    results = collection.query(query_texts=[query], n_results=k)
    docs = []
    for i in range(len(results["ids"][0])):
        docs.append({
            "id": results["ids"][0][i],
            "content": results["documents"][0][i],
            "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
            "score": results["distances"][0][i] if results["distances"] else 0,
        })
    return docs
