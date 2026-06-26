"use client";

import { useState, useEffect, useRef } from "react";
import {
  Brain, Shield, BarChart3, TrendingUp, MessageSquare,
  FileText, Send, Loader2, AlertTriangle,
  Lightbulb, Flag, Bot, User, DollarSign, Users,
  Clock, ArrowUpRight, ArrowDownRight, Database, Edit2, Check, X,
  Target, LineChart, PieChart, Activity, CheckCircle, XCircle,
} from "lucide-react";
import { listDocuments, getAnalytics } from "@/lib/api";
import type { DocumentResponse } from "@/types";

const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function AnalyticsPage() {
  const [docs, setDocs] = useState<DocumentResponse[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<number | null>(null);
  const [analytics, setAnalytics] = useState<Record<string, any> | null>(null);
  const [fetched, setFetched] = useState(false);
  const [loading, setLoading] = useState(false);
  const [businessData, setBusinessData] = useState<Record<string, any> | null>(null);
  const [pipelineRunning, setPipelineRunning] = useState(false);
  const [pipelineData, setPipelineData] = useState<Record<string, any> | null>(null);
  const token = typeof window !== "undefined" ? localStorage.getItem("aura_token") : "";
  const authH = { "Content-Type": "application/json", Authorization: `Bearer ${token}` } as Record<string, string>;

  useEffect(() => { if (!fetched) listDocuments().then(setDocs).finally(() => setFetched(true)); }, []);

  async function runAnalysis() {
    if (!selectedDoc) return;
    setLoading(true);
    try {
      const a = await getAnalytics(selectedDoc);
      setAnalytics(a as any);
      const token = localStorage.getItem("aura_token");
      const res = await fetch(`${apiBase}/api/v1/analytics/business-analytics`, {
        method: "POST", headers: authH, body: JSON.stringify({ doc_id: selectedDoc }),
      });
      if (res.ok) setBusinessData(await res.json());
    } catch {} finally { setLoading(false); }
  }

  async function runPipeline() {
    if (!selectedDoc) return;
    setPipelineRunning(true);
    setPipelineData(null);
    try {
      const res = await fetch(`${apiBase}/api/v1/analytics/pipeline`, {
        method: "POST", headers: authH, body: JSON.stringify({ doc_id: selectedDoc }),
      });
      if (res.ok) setPipelineData(await res.json());
    } catch {} finally { setPipelineRunning(false); }
  }

  const pipelineDash = pipelineData?.results?.dashboard || {};
  const pipelineExec = pipelineData?.results?.executive || {};
  const pipelineStages = pipelineData?.stages || [];
  const pipelineBh = pipelineDash?.business_health || {};

  const kpiSummary = businessData?.kpi_summary || {};
  const chartRecs = businessData?.chart_recommendations || [];
  const trend = businessData?.trend_analysis || {};
  const charts = businessData?.charts || [];
  const comparative = businessData?.comparative_analysis || [];
  const correlations = businessData?.correlations || [];
  const kpis = kpiSummary.kpis || [];

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Business Analytics</h1>
          <p className="text-sm text-zinc-500">Executive insights, KPIs, trends, and comparative analysis</p>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        {docs.map(d => (
          <button key={d.id} onClick={() => { setSelectedDoc(d.id); setBusinessData(null); }}
            className={`rounded-xl border px-4 py-2 text-sm transition-colors ${selectedDoc === d.id ? "border-blue-600 bg-blue-600/20 text-blue-300" : "border-zinc-800 bg-zinc-900/50 text-zinc-400 hover:border-zinc-700"}`}>
            {d.title.length > 30 ? d.title.slice(0, 30) + "..." : d.title}
          </button>
        ))}
      </div>

      {selectedDoc && (
        <div className="space-y-6">
          {!businessData && !loading && (
            <button onClick={runAnalysis} className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-emerald-600 px-6 py-3 text-sm font-medium hover:from-blue-500 hover:to-emerald-500 shadow-lg shadow-blue-600/20">
              <Activity className="h-5 w-5" />Run Business Analysis
            </button>
          )}
          {loading && <div className="space-y-4">{[1,2,3,4].map(i => <div key={i} className="h-24 animate-pulse rounded-xl bg-zinc-800/50" />)}</div>}

          {businessData && <>
            {/* Dataset Context */}
            {businessData.dataset_intelligence && (
              <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-3">
                <div className="flex flex-wrap gap-4 text-xs">
                  <span className="text-zinc-500">Industry: <span className="text-zinc-200 font-medium">{businessData.dataset_intelligence.industry || "—"}</span></span>
                  <span className="text-zinc-500">Domain: <span className="text-zinc-200 font-medium">{businessData.dataset_intelligence.dataset_type || "—"}</span></span>
                  <span className="text-zinc-500">Target: <span className="text-blue-400 font-medium">{businessData.dataset_intelligence.target_variable || "—"}</span></span>
                  <span className="text-zinc-500">KPIs detected: <span className="text-emerald-400 font-medium">{kpiSummary.total_detected || 0}</span></span>
                  <span className="text-zinc-500">Charts recommended: <span className="text-amber-400 font-medium">{chartRecs.length}</span></span>
                </div>
              </div>
            )}

            {/* Executive KPI Cards */}
            {kpis.length > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <BarChart3 className="h-5 w-5 text-zinc-400" />
                  <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Key Performance Indicators</h2>
                </div>
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                  {kpis.map((kpi: any, i: number) => (
                    <div key={i} className={`rounded-xl border p-4 ${kpi.category === "Finance" ? "border-emerald-800/30 bg-emerald-950/20" : kpi.category === "Sales" ? "border-blue-800/30 bg-blue-950/20" : kpi.category === "HR" ? "border-purple-800/30 bg-purple-950/20" : "border-zinc-800 bg-zinc-900/50"}`}>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-[10px] font-medium uppercase tracking-wider opacity-70">{kpi.category}</span>
                        <DollarSign className="h-4 w-4 text-zinc-500" />
                      </div>
                      <p className="text-xs text-zinc-500">{kpi.label}</p>
                      <p className="mt-1 text-xl font-semibold text-zinc-100">{kpi.value}</p>
                      {kpi.change !== null && (
                        <div className={`mt-1 flex items-center gap-1 text-xs ${kpi.change >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                          {kpi.change >= 0 ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}
                          {Math.abs(kpi.change).toFixed(1)}%
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Chart Recommendations + Trend Analysis */}
            <div className="grid gap-6 lg:grid-cols-2">
              {/* Recommended Charts */}
              <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
                <h2 className="text-xs font-medium uppercase tracking-wider text-zinc-500 mb-3">Recommended Visualizations</h2>
                <div className="space-y-1.5">
                  {chartRecs.filter((c: any) => c.chart_type !== "metric").slice(0, 8).map((rec: any, i: number) => (
                    <div key={i} className="flex items-center gap-2 rounded-lg bg-zinc-800/30 px-3 py-2">
                      <span className={`text-[10px] font-medium uppercase px-1.5 py-0.5 rounded ${
                        rec.chart_type === "line" ? "bg-blue-900/50 text-blue-300" :
                        rec.chart_type === "bar" ? "bg-emerald-900/50 text-emerald-300" :
                        rec.chart_type === "pie" ? "bg-purple-900/50 text-purple-300" :
                        rec.chart_type === "histogram" ? "bg-amber-900/50 text-amber-300" : "bg-zinc-800 text-zinc-400"
                      }`}>{rec.chart_type}</span>
                      <span className="text-xs text-zinc-200 flex-1">{rec.column}</span>
                      <span className="text-[10px] text-zinc-500">{rec.classification}</span>
                    </div>
                  ))}
                  {chartRecs.length === 0 && <p className="text-xs text-zinc-600 py-4 text-center">No chart recommendations — check column types.</p>}
                </div>
              </div>

              {/* Trend Analysis */}
              {Object.keys(trend).length > 0 && (
                <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
                  <h2 className="text-xs font-medium uppercase tracking-wider text-zinc-500 mb-3">Trend Analysis</h2>
                  <div className="space-y-2">
                    {Object.entries(trend).map(([col, t]: [string, any]) => (
                      <div key={col} className="rounded-lg bg-zinc-800/30 p-3">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-medium text-zinc-200">{col}</span>
                          <span className={`text-xs font-semibold ${t.direction === "up" ? "text-emerald-400" : t.direction === "down" ? "text-red-400" : "text-zinc-400"}`}>
                            {t.direction === "up" ? "↑" : t.direction === "down" ? "↓" : "→"} {t.change_pct > 0 ? "+" : ""}{t.change_pct}%
                          </span>
                        </div>
                        <div className="flex items-center gap-3 mt-1 text-[10px] text-zinc-500">
                          <span>Current: {t.current}</span>
                          <span>Avg: {t.average}</span>
                        </div>
                        <div className="mt-1.5 h-1.5 rounded-full bg-zinc-800 overflow-hidden">
                          <div className={`h-full rounded-full ${t.direction === "up" ? "bg-emerald-500" : t.direction === "down" ? "bg-red-500" : "bg-zinc-600"}`}
                            style={{ width: `${Math.min(Math.abs(t.change_pct) * 3, 100)}%` }} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Key Visualizations */}
            {charts.length > 0 && (
              <div>
                <div className="flex items-center gap-2 mb-3">
                  <BarChart3 className="h-5 w-5 text-zinc-400" />
                  <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Key Visualizations</h2>
                </div>
                <div className="grid gap-4 sm:grid-cols-2">
                  {charts.map((ch: any, i: number) => (
                    <div key={i} className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-3">
                      <h3 className="mb-1 text-xs font-medium uppercase tracking-wider text-zinc-500 flex items-center gap-1.5">
                        <BarChart3 className="h-3.5 w-3.5" />
                        {ch.column}
                        <span className="text-[10px] text-zinc-600 font-normal lowercase">({ch.chart_type} — {ch.business_reason})</span>
                      </h3>
                      <iframe srcDoc={ch.html} className="w-full h-64 rounded-lg border-0" title={ch.column} />
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Comparative Analysis */}
            {comparative.length > 0 && (
              <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
                <div className="flex items-center gap-2 mb-3">
                  <Target className="h-5 w-5 text-orange-400" />
                  <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Comparative Analysis</h2>
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                  {comparative.map((c: any, i: number) => (
                    <div key={i} className="rounded-lg bg-zinc-800/30 p-3">
                      <p className="text-xs text-zinc-400">{c.kpi} <span className="text-zinc-600">by</span> {c.segment}</p>
                      <div className="mt-2 flex items-center gap-3">
                        <div className="flex-1">
                          <p className="text-[10px] text-emerald-400">Best: {c.top_segment}</p>
                          <p className="text-xs font-semibold text-zinc-200">{c.top_value.toFixed(2)}</p>
                        </div>
                        <div className="flex-1">
                          <p className="text-[10px] text-red-400">Worst: {c.bottom_segment}</p>
                          <p className="text-xs font-semibold text-zinc-200">{c.bottom_value.toFixed(2)}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Strong Correlations */}
            {correlations.length > 0 && (
              <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
                <div className="flex items-center gap-2 mb-3">
                  <Activity className="h-5 w-5 text-violet-400" />
                  <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Key Relationships</h2>
                </div>
                <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                  {correlations.map((c: any, i: number) => (
                    <div key={i} className="rounded-lg bg-zinc-800/30 px-3 py-2 text-xs">
                      <span className="text-zinc-300">{c.col_a}</span>
                      <span className={`mx-1 ${c.correlation > 0 ? "text-emerald-400" : "text-red-400"}`}>
                        {c.correlation > 0 ? "+" : ""}{c.correlation}
                      </span>
                      <span className="text-zinc-300">{c.col_b}</span>
                      <span className="ml-1 text-[10px] text-zinc-600">({c.strength})</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Category breakdown */}
            {kpiSummary.by_category && Object.keys(kpiSummary.by_category).length > 0 && (
              <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
                <h2 className="text-xs font-medium uppercase tracking-wider text-zinc-500 mb-3">KPI Breakdown by Category</h2>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(kpiSummary.by_category).map(([cat, count]: [string, any]) => (
                    <div key={cat} className="rounded-lg bg-zinc-800/30 px-3 py-2 text-xs">
                      <span className="text-zinc-400">{cat}: </span>
                      <span className="text-zinc-200 font-semibold">{count} KPIs</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>}

          {/* Pipeline Orchestrator — additional feature */}
          <div className="border-t border-zinc-800 pt-6 mt-4">
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Analytics Pipeline</h2>
              {!pipelineRunning && !pipelineData && (
                <button onClick={runPipeline} className="flex items-center gap-1.5 rounded-lg bg-zinc-800 px-3 py-1.5 text-xs text-zinc-300 hover:bg-zinc-700">
                  <Activity className="h-3.5 w-3.5" />Run Full Pipeline
                </button>
              )}
              {pipelineRunning && (
                <span className="flex items-center gap-1.5 text-xs text-blue-400"><Loader2 className="h-3.5 w-3.5 animate-spin" />Processing...</span>
              )}
              {pipelineData && !pipelineRunning && (
                <div className="flex items-center gap-2">
                  <CheckCircle className="h-4 w-4 text-emerald-400" />
                  <span className="text-xs text-zinc-500">{(pipelineData.total_duration_ms / 1000).toFixed(1)}s</span>
                  <button onClick={runPipeline} className="text-xs text-blue-400 hover:underline">Re-run</button>
                </div>
              )}
            </div>

            {/* Processing timeline */}
            {pipelineRunning && (
              <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-4 space-y-2">
                {["understanding", "business_context", "data_quality", "statistical", "kpis", "executive", "visualizations", "dashboard"].map((sid, i) => {
                  const found = pipelineStages.find((s: any) => s.id === sid);
                  const status = found?.status || (pipelineRunning ? "running" : "pending");
                  return (
                    <div key={sid} className="flex items-center gap-2 text-xs">
                      {status === "completed" ? <CheckCircle className="h-4 w-4 text-emerald-500 shrink-0" /> :
                       status === "running" ? <Loader2 className="h-4 w-4 text-blue-400 animate-spin shrink-0" /> :
                       status === "failed" ? <XCircle className="h-4 w-4 text-red-500 shrink-0" /> :
                       <Clock className="h-4 w-4 text-zinc-700 shrink-0" />}
                      <span className={status === "completed" ? "text-zinc-300" : status === "running" ? "text-blue-300" : "text-zinc-600"}>
                        {sid === "understanding" ? "Understanding Dataset" :
                         sid === "business_context" ? "Detecting Business Context" :
                         sid === "data_quality" ? "Assessing Data Quality" :
                         sid === "statistical" ? "Running Statistical Analysis" :
                         sid === "kpis" ? "Identifying KPIs" :
                         sid === "executive" ? "Generating Executive Insights" :
                         sid === "visualizations" ? "Building Visualizations" :
                         "Preparing Dashboard"}
                      </span>
                    </div>
                  );
                })}
              </div>
            )}

            {/* Pipeline Results */}
            {pipelineData && !pipelineRunning && pipelineDash.executive_summary && (
              <div className="space-y-4">
                <div className="rounded-xl border border-blue-900/30 bg-blue-950/20 p-4">
                  <h3 className="text-xs font-medium uppercase tracking-wider text-blue-400 mb-2">Executive Summary</h3>
                  <p className="text-sm text-zinc-200">{pipelineDash.executive_summary}</p>
                </div>
                {pipelineBh.overall && (
                  <div className="grid gap-3 sm:grid-cols-6">
                    {[
                      { label: "Overall", value: pipelineBh.overall },
                      { label: "Revenue", value: pipelineBh.revenue_health },
                      { label: "Growth", value: pipelineBh.growth_health },
                      { label: "Risk", value: pipelineBh.risk_health },
                      { label: "Operations", value: pipelineBh.operations_health },
                      { label: "Customers", value: pipelineBh.customer_health },
                    ].filter(m => m.value).map(m => (
                      <div key={m.label} className="text-center rounded-lg bg-zinc-800/30 p-2">
                        <p className="text-[10px] text-zinc-500">{m.label}</p>
                        <p className={`text-lg font-bold ${m.value >= 70 ? "text-emerald-400" : m.value >= 40 ? "text-amber-400" : "text-red-400"}`}>{m.value}</p>
                      </div>
                    ))}
                  </div>
                )}
                {pipelineExec.risks?.length > 0 && (
                  <div className="rounded-xl border border-red-800/30 bg-red-950/20 p-4">
                    <h3 className="text-xs font-medium uppercase tracking-wider text-red-400 mb-2">Risks</h3>
                    <div className="space-y-1">
                      {pipelineExec.risks.slice(0, 3).map((r: any, i: number) => (
                        <div key={i} className="flex gap-2 text-xs text-zinc-300">
                          <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-red-500" />{r.name}{r.financial_exposure ? ` — ${r.financial_exposure}` : ""}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {pipelineExec.recommendations?.length > 0 && (
                  <div className="rounded-xl border border-purple-800/30 bg-purple-950/20 p-4">
                    <h3 className="text-xs font-medium uppercase tracking-wider text-purple-400 mb-2">Recommendations</h3>
                    <div className="space-y-1">
                      {pipelineExec.recommendations.slice(0, 3).map((r: any, i: number) => (
                        <div key={i} className="flex gap-2 text-xs text-zinc-300">
                          <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-purple-500" />{r.title}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
