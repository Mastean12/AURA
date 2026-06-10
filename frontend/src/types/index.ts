export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ChatResponse {
  reply: string;
}

export interface QueryRequest {
  question: string;
  k?: number;
  session_id?: string;
}

export interface QueryResponse {
  answer: string;
  sources: string[];
  confidence: number;
  session_id?: string;
}

export interface UploadResponse {
  filename: string;
  size: number;
  upload_timestamp: string;
  content_preview: string | null;
}

export interface DocumentResponse {
  id: number;
  title: string;
  content: string;
  source: string | null;
  created_at: string;
  updated_at: string;
}

export interface ColumnStat {
  name: string;
  dtype: string;
  missing: number;
  total: number;
  numeric: Record<string, number> | null;
  categorical: Record<string, unknown> | null;
}

export interface AnalyticsResponse {
  doc_id: number;
  row_count: number;
  column_count: number;
  columns: ColumnStat[];
}

export interface ChartsResponse {
  doc_id: number;
  column: string;
  bar: Record<string, unknown>;
  pie: Record<string, unknown>;
  line: Record<string, unknown>;
  area: Record<string, unknown> | null;
  histogram: Record<string, unknown> | null;
  distribution: Record<string, unknown> | null;
  correlation: Record<string, unknown> | null;
}

export interface InsightsResponse {
  doc_id: number;
  executive_summary: string;
  key_findings: string[];
  risks: string[];
  opportunities: string[];
  recommendations: string[];
  confidence_score: number;
}

export interface HealthResponse {
  doc_id: number;
  completeness: number;
  quality: number;
  consistency: number;
  missing_data: number;
  overall: number;
  color: string;
  label: string;
  explanation: string;
}

export interface AnalyticsChatResponse {
  answer: string;
  confidence: number;
  session_id: string;
}

export interface SummaryResponse {
  summary_type: string;
  content: Record<string, unknown>[];
  doc_id: number;
}

// --- Phase 1 New Types ---

export interface ExecutiveSummaryResponse {
  doc_id: number;
  summary: string;
  confidence: number;
}

export interface KPIItem {
  category: string;
  label: string;
  column: string;
  value: string;
  raw_value: number;
  change: number | null;
  format: string;
}

export interface KPIResponse {
  doc_id: number;
  kpis: KPIItem[];
}

export interface ChartInsightResponse {
  doc_id: number;
  chart_type: string;
  column: string;
  insight: string;
}
