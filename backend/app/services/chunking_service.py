import hashlib
import uuid

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


def chunk_text(text: str, source: str = "", doc_id: int = 0) -> list[dict]:
    if not text:
        return []

    separators = ["\n\n", "\n", ". ", " ", ""]
    chunks = _split_recursive(text, separators, 0, CHUNK_SIZE, CHUNK_OVERLAP)

    result = []
    for i, chunk_text in enumerate(chunks):
        chunk_id = str(uuid.uuid4())[:8]
        content_hash = hashlib.md5(chunk_text.encode("utf-8")).hexdigest()
        result.append({
            "chunk_id": chunk_id,
            "doc_id": doc_id,
            "chunk_index": i,
            "content": chunk_text,
            "source": source,
            "content_hash": content_hash,
            "char_count": len(chunk_text),
        })
    return result


def _split_recursive(text: str, separators: list[str], depth: int, chunk_size: int, overlap: int) -> list[str]:
    if depth >= len(separators):
        return _split_by_size(text, chunk_size, overlap)

    separator = separators[depth]
    parts = text.split(separator) if separator else [text]

    chunks = []
    for part in parts:
        stripped = part.strip()
        if not stripped:
            continue
        if len(stripped) <= chunk_size:
            chunks.append(stripped)
        else:
            sub_chunks = _split_recursive(stripped, separators, depth + 1, chunk_size, overlap)
            chunks.extend(sub_chunks)
    return _merge_with_overlap(chunks, chunk_size, overlap)


def _split_by_size(text: str, chunk_size: int, overlap: int) -> list[str]:
    if len(text) <= chunk_size:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        start += chunk_size - overlap
    return chunks


def _merge_with_overlap(chunks: list[str], chunk_size: int, overlap: int) -> list[str]:
    if not chunks:
        return []
    merged = []
    current = chunks[0]
    for next_chunk in chunks[1:]:
        if len(current) + len(next_chunk) <= chunk_size + overlap:
            current += "\n" + next_chunk
        else:
            merged.append(current)
            current = next_chunk
    merged.append(current)
    return merged
