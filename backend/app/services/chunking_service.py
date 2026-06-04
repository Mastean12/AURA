from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document as LangchainDocument

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


def chunk_text(text: str, source: str = "") -> list[LangchainDocument]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", " ", ""],
    )
    texts = splitter.split_text(text)
    docs = []
    for i, chunk in enumerate(texts):
        meta = {"source": source, "chunk_index": i, "chunk_count": len(texts)}
        docs.append(LangchainDocument(page_content=chunk, metadata=meta))
    return docs
