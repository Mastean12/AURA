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
    area: dict | None = None
    histogram: dict | None = None
    distribution: dict | None = None
    correlation: dict | None = None


class InsightsResponse(BaseModel):
    doc_id: int
    executive_summary: str
    key_findings: list[str]
    risks: list[str]
    opportunities: list[str]
    recommendations: list[str]
    confidence_score: float


class HealthResponse(BaseModel):
    doc_id: int
    completeness: int
    quality: int
    consistency: int
    missing_data: int
    overall: int
    color: str
    label: str
    explanation: str


class AnalyticsChatRequest(BaseModel):
    doc_id: int
    question: str
    session_id: str = "default"


class AnalyticsChatResponse(BaseModel):
    answer: str
    confidence: float
    session_id: str


class UploadResponse(BaseModel):
    filename: str
    size: int
    upload_timestamp: datetime
    content_preview: str | None = None


# --- Phase 1 New Schemas ---

class ExecutiveSummaryResponse(BaseModel):
    doc_id: int
    summary: str
    confidence: float


class KPIResponse(BaseModel):
    doc_id: int
    kpis: list[dict]


class ChartInsightRequest(BaseModel):
    doc_id: int
    chart_type: str
    column: str


class ChartInsightResponse(BaseModel):
    doc_id: int
    chart_type: str
    column: str
    insight: str


# --- Phase 2 Schemas ---

class ForecastRequest(BaseModel):
    doc_id: int
    column: str
    periods: int = 30


class ForecastPoint(BaseModel):
    date: str
    value: float
    lower_bound: float
    upper_bound: float


class ForecastResponse(BaseModel):
    doc_id: int
    column: str
    historical: list[ForecastPoint]
    forecast: list[ForecastPoint]
    trend_direction: str
    trend_strength: float
    confidence_avg: float
    explanation: str


class AnomalyRequest(BaseModel):
    doc_id: int
    column: str
    severity: str | None = None


class AnomalyItem(BaseModel):
    index: int
    value: float
    expected: float
    deviation: float
    severity: str
    type: str
    explanation: str


class AnomalyResponse(BaseModel):
    doc_id: int
    column: str
    anomalies: list[AnomalyItem]
    anomaly_count: int
    high_severity_count: int
    summary: str


class RiskScoreRequest(BaseModel):
    doc_id: int


class RiskCategory(BaseModel):
    name: str
    score: int
    level: str
    explanation: str
    mitigations: list[str]


class RiskScoreResponse(BaseModel):
    doc_id: int
    overall_score: int
    overall_level: str
    overall_explanation: str
    categories: list[RiskCategory]


class RecommendationRequest(BaseModel):
    doc_id: int


class RecommendationItem(BaseModel):
    title: str
    description: str
    category: str
    impact: str
    urgency: str
    confidence: float
    source: str


class RecommendationResponse(BaseModel):
    doc_id: int
    recommendations: list[RecommendationItem]
    total_count: int
    high_priority_count: int
