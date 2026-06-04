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
}

export interface SummaryResponse {
  summary_type: string;
  content: Record<string, unknown>[];
  doc_id: number;
}
