from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class DocumentCreate(BaseModel):
    title: str
    content: str
    source: Optional[str] = None


class DocumentResponse(BaseModel):
    id: int
    title: str
    content: str
    source: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class QueryRequest(BaseModel):
    question: str
    k: int = 5
    session_id: str | None = None


class QueryResponse(BaseModel):
    answer: str
    sources: list[str]
    confidence: float = 0.0
    session_id: str | None = None


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]


class ChatResponse(BaseModel):
    reply: str


class SummaryRequest(BaseModel):
    doc_id: int
    summary_type: int = 1


class SummaryResponse(BaseModel):
    summary_type: str
    content: list[dict]
    doc_id: int


class ColumnStat(BaseModel):
    name: str
    dtype: str
    missing: int
    total: int
    numeric: dict | None = None
    categorical: dict | None = None


class AnalyticsRequest(BaseModel):
    doc_id: int


class AnalyticsResponse(BaseModel):
    doc_id: int
    row_count: int
    column_count: int
    columns: list[ColumnStat]


class ChartsRequest(BaseModel):
    doc_id: int
    column: str


class ChartsResponse(BaseModel):
    doc_id: int
    column: str
    bar: dict
    pie: dict
    line: dict


class UploadResponse(BaseModel):
    filename: str
    size: int
    upload_timestamp: datetime
    content_preview: str | None = None
