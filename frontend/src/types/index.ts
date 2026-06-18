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
  doc_id?: number;
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
  file_type: string;
  upload_timestamp: string;
  content_preview: string | null;
}

export interface DocumentResponse {
  id: number;
  title: string;
  content: string;
  source: string | null;
  file_type: string | null;
  file_size: number | null;
  processing_status: string | null;
  chunk_count: number | null;
  page_count: number | null;
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
  dataset_type?: string | null;
  target_variable?: string | null;
  data_quality_score?: number | null;
  data_quality_grade?: string | null;
}

export interface ChartItem {
  column: string;
  chart_type: string;
  nunique: number;
  data: Record<string, unknown>;
  html: string;
}

export interface ChartsResponse {
  doc_id: number;
  column: string;
  bar?: Record<string, unknown> | null;
  pie?: Record<string, unknown> | null;
  line?: Record<string, unknown> | null;
  area?: Record<string, unknown> | null;
  histogram?: Record<string, unknown> | null;
  distribution?: Record<string, unknown> | null;
  correlation?: Record<string, unknown> | null;
  charts?: ChartItem[];
  target_variable?: string | null;
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

// --- Phase 2 Types ---

export interface ForecastPoint {
  date: string;
  value: number;
  lower_bound: number;
  upper_bound: number;
}

export interface ForecastResponse {
  doc_id: number;
  column: string;
  historical: ForecastPoint[];
  forecast: ForecastPoint[];
  trend_direction: string;
  trend_strength: number;
  confidence_avg: number;
  explanation: string;
}

export interface AnomalyItem {
  index: number;
  value: number;
  expected: number;
  deviation: number;
  severity: string;
  type: string;
  explanation: string;
}

export interface AnomalyResponse {
  doc_id: number;
  column: string;
  anomalies: AnomalyItem[];
  anomaly_count: number;
  high_severity_count: number;
  summary: string;
}

export interface RiskCategory {
  name: string;
  score: number;
  level: string;
  explanation: string;
  mitigations: string[];
}

export interface RiskScoreResponse {
  doc_id: number;
  overall_score: number;
  overall_level: string;
  overall_explanation: string;
  categories: RiskCategory[];
}

export interface RecommendationItem {
  title: string;
  description: string;
  category: string;
  impact: string;
  urgency: string;
  confidence: number;
  source: string;
}

export interface RecommendationResponse {
  doc_id: number;
  recommendations: RecommendationItem[];
  total_count: number;
  high_priority_count: number;
}

// --- Phase 3 Types ---

export interface IndustryDashboardResponse {
  doc_id: number;
  detected_industry: string;
  industry_kpis: { label: string; column: string; value: string; raw_value: number }[];
  industry_summary: string;
  recommendations: string[];
  confidence: number;
}

export interface MultiDocumentResponse {
  doc_count: number;
  consolidated_summary: string;
  themes: string[];
  conflicts: string[];
  cross_references: string[];
  total_insights: string[];
  confidence: number;
}

export interface ComparisonResponse {
  similarities: string[];
  differences: string[];
  key_changes: string[];
  recommended_actions: string[];
  comparison_summary: string;
  confidence: number;
}

// --- Phase 4 Types ---

export interface AutonomousAnalysisResponse {
  doc_id: number;
  business_health: {
    overall_score: number;
    label: string;
    completeness: number;
    quality: number;
  };
  top_risks: { title: string; severity: string; impact: string; probability: string; mitigation: string }[];
  top_opportunities: { title: string; estimated_impact: string; strategic_value: string; recommended_action: string }[];
  forecasts: { metric: string; trend: string; confidence: number; horizon: string }[];
  strategic_recommendations: { title: string; impact: string; urgency: string; confidence: number; expected_outcome: string }[];
  overall_confidence: number;
}

export interface ExecutiveBriefingResponse {
  summary: string;
  business_health: string;
  critical_risks: string[];
  growth_opportunities: string[];
  forecast_outlook: string;
  recommended_actions: string[];
  confidence: number;
}
