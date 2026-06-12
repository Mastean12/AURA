import { API_BASE, HEALTH_URL } from "./config";
import type {
  ChatMessage,
  ChatResponse,
  QueryResponse,
  UploadResponse,
  DocumentResponse,
  AnalyticsResponse,
  ChartsResponse,
  InsightsResponse,
  HealthResponse,
  AnalyticsChatResponse,
  SummaryResponse,
  ExecutiveSummaryResponse,
  KPIResponse,
  ChartInsightResponse,
  ForecastResponse,
  AnomalyResponse,
  RiskScoreResponse,
  RecommendationResponse,
  IndustryDashboardResponse,
  MultiDocumentResponse,
  ComparisonResponse,
  AutonomousAnalysisResponse,
  ExecutiveBriefingResponse,
} from "@/types";

function log(level: "info" | "error", msg: string, data?: unknown) {
  if (level === "info") console.log(`[API] ${msg}`, data ?? "");
  else console.error(`[API] ${msg}`, data ?? "");
}

export async function chat(messages: ChatMessage[]): Promise<ChatResponse> {
  const url = `${API_BASE}/chat/`;
  log("info", "POST", url);
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages }),
  });
  const data = await res.json();
  log("info", "Response", { status: res.status, data });
  return data;
}

export async function query(payload: {
  question: string;
  k?: number;
  session_id?: string;
}): Promise<QueryResponse> {
  const url = `${API_BASE}/chat/query`;
  log("info", "POST", url);
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  log("info", "Response", { status: res.status, data });
  return data;
}

export async function queryDocuments(payload: {
  question: string;
  k?: number;
  session_id?: string;
  doc_id?: number;
}): Promise<QueryResponse> {
  const url = `${API_BASE}/documents/query`;
  log("info", "POST", url);
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return res.json();
}

export async function uploadFile(file: File): Promise<UploadResponse> {
  const form = new FormData();
  form.append("file", file);
  const url = `${API_BASE}/upload/`;
  log("info", "POST", url);
  const res = await fetch(url, { method: "POST", body: form });
  const data = await res.json();
  log("info", "Response", { status: res.status, data });
  return data;
}

export function uploadFileWithProgress(
  file: File,
  onProgress: (pct: number) => void
): Promise<UploadResponse> {
  return new Promise((resolve, reject) => {
    const formData = new FormData();
    formData.append("file", file);

    const url = `${API_BASE}/upload/`;
    log("info", "XHR POST", url);

    const xhr = new XMLHttpRequest();
    xhr.upload.addEventListener("progress", (e) => {
      if (e.lengthComputable) {
        const pct = Math.round((e.loaded / e.total) * 100);
        onProgress(pct);
      }
    });
    xhr.addEventListener("load", () => {
      log("info", "XHR complete", { status: xhr.status, response: xhr.responseText.slice(0, 200) });
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(JSON.parse(xhr.responseText));
      } else {
        reject(new Error(`Upload failed: ${xhr.status} ${xhr.statusText}`));
      }
    });
    xhr.addEventListener("error", () => {
      log("error", "XHR network error", { url });
      reject(new Error("Network error"));
    });
    xhr.addEventListener("abort", () => {
      log("error", "XHR aborted", { url });
      reject(new Error("Upload aborted"));
    });
    xhr.open("POST", url);
    xhr.send(formData);
  });
}

export async function listDocuments(): Promise<DocumentResponse[]> {
  const url = `${API_BASE}/documents/`;
  log("info", "GET", url);
  const res = await fetch(url);
  const data = await res.json();
  log("info", "Response", { status: res.status, count: Array.isArray(data) ? data.length : 0 });
  return data;
}

export async function getDocument(id: number): Promise<DocumentResponse> {
  const url = `${API_BASE}/documents/${id}`;
  log("info", "GET", url);
  const res = await fetch(url);
  return res.json();
}

export async function deleteDocument(id: number): Promise<void> {
  const url = `${API_BASE}/documents/${id}`;
  log("info", "DELETE", url);
  await fetch(url, { method: "DELETE" });
}

export async function getAnalytics(doc_id: number): Promise<AnalyticsResponse> {
  const url = `${API_BASE}/analytics/`;
  log("info", "POST", url);
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ doc_id }),
  });
  return res.json();
}

export async function getCharts(
  doc_id: number,
  column: string
): Promise<ChartsResponse> {
  const url = `${API_BASE}/analytics/charts`;
  log("info", "POST", url);
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ doc_id, column }),
  });
  return res.json();
}

export async function getAllCharts(doc_id: number): Promise<ChartsResponse> {
  const url = `${API_BASE}/analytics/charts/all`;
  log("info", "POST", url);
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ doc_id }),
  });
  return res.json();
}

export async function getInsights(doc_id: number): Promise<InsightsResponse> {
  const url = `${API_BASE}/analytics/insights`;
  log("info", "POST", url);
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ doc_id }),
  });
  return res.json();
}

export async function getDatasetHealth(doc_id: number): Promise<HealthResponse> {
  const url = `${API_BASE}/analytics/health`;
  log("info", "POST", url);
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ doc_id }),
  });
  return res.json();
}

export async function analyticsChat(
  doc_id: number,
  question: string,
  session_id: string
): Promise<AnalyticsChatResponse> {
  const url = `${API_BASE}/analytics/chat`;
  log("info", "POST", url);
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ doc_id, question, session_id }),
  });
  return res.json();
}

export async function getSummary(
  doc_id: number,
  summary_type: number
): Promise<SummaryResponse> {
  const url = `${API_BASE}/summary/`;
  log("info", "POST", url);
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ doc_id, summary_type }),
  });
  return res.json();
}

export async function exportReport(doc_id: number): Promise<Blob> {
  const url = `${API_BASE}/reports/export`;
  log("info", "POST", url);
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ doc_id }),
  });
  if (!res.ok) throw new Error("Export failed");
  return res.blob();
}

export async function health(): Promise<{ status: string }> {
  log("info", "GET", HEALTH_URL);
  const res = await fetch(HEALTH_URL);
  const data = await res.json();
  log("info", "Response", { status: res.status, data });
  return data;
}

// --- Phase 1 New API Calls ---

export async function getExecutiveSummary(doc_id: number): Promise<ExecutiveSummaryResponse> {
  const url = `${API_BASE}/analytics/executive-summary`;
  log("info", "POST", url);
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ doc_id }),
  });
  return res.json();
}

export async function getKPIs(doc_id: number): Promise<KPIResponse> {
  const url = `${API_BASE}/analytics/kpis?doc_id=${doc_id}`;
  log("info", "GET", url);
  const res = await fetch(url);
  return res.json();
}

export async function getChartInsight(
  doc_id: number,
  chart_type: string,
  column: string
): Promise<ChartInsightResponse> {
  const url = `${API_BASE}/analytics/chart-insight`;
  log("info", "POST", url);
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ doc_id, chart_type, column }),
  });
  return res.json();
}

// --- Phase 2 API Calls ---

export async function getForecast(
  doc_id: number,
  column: string,
  periods: number = 30
): Promise<ForecastResponse> {
  const url = `${API_BASE}/predictive/forecast`;
  log("info", "POST", url);
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ doc_id, column, periods }),
  });
  return res.json();
}

export async function getAnomalies(
  doc_id: number,
  column: string,
  severity?: string
): Promise<AnomalyResponse> {
  const url = `${API_BASE}/predictive/anomalies`;
  log("info", "POST", url);
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ doc_id, column, severity }),
  });
  return res.json();
}

export async function getRiskScore(
  doc_id: number
): Promise<RiskScoreResponse> {
  const url = `${API_BASE}/predictive/risk-score`;
  log("info", "POST", url);
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ doc_id }),
  });
  return res.json();
}

export async function getRecommendations(
  doc_id: number
): Promise<RecommendationResponse> {
  const url = `${API_BASE}/predictive/recommendations`;
  log("info", "POST", url);
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ doc_id }),
  });
  return res.json();
}

// --- Phase 3 API Calls ---

export async function getIndustryDashboard(doc_id: number): Promise<IndustryDashboardResponse> {
  const url = `${API_BASE}/analytics/industry-dashboard?doc_id=${doc_id}`;
  log("info", "GET", url);
  const res = await fetch(url);
  return res.json();
}

export async function getMultiDocumentAnalysis(doc_ids: number[]): Promise<MultiDocumentResponse> {
  const url = `${API_BASE}/analytics/multi-document`;
  log("info", "POST", url);
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ doc_ids }),
  });
  return res.json();
}

export async function getComparison(
  doc_id_a: number,
  doc_id_b: number,
  label_a: string = "Document A",
  label_b: string = "Document B"
): Promise<ComparisonResponse> {
  const url = `${API_BASE}/analytics/compare`;
  log("info", "POST", url);
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ doc_id_a, doc_id_b, label_a, label_b }),
  });
  return res.json();
}

export async function getAutonomousAnalysis(doc_ids: number[]): Promise<AutonomousAnalysisResponse> {
  const url = `${API_BASE}/analytics/autonomous-analysis`;
  log("info", "POST", url);
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ doc_ids }),
  });
  return res.json();
}

export async function getExecutiveBriefing(doc_id: number, company_name: string = ""): Promise<ExecutiveBriefingResponse> {
  const url = `${API_BASE}/reports/executive-briefing`;
  log("info", "POST", url);
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ doc_id, company_name }),
  });
  return res.json();
}
