"use client";

import { useState, useEffect, useRef } from "react";
import {
  Brain, Shield, BarChart3, TrendingUp, Activity,
  Loader2, AlertTriangle, Lightbulb, Target, DollarSign, Users,
  Clock, ArrowUpRight, ArrowDownRight, Database, CheckCircle, XCircle,
  FileText, LineChart,
} from "lucide-react";
import { listDocuments } from "@/lib/api";
import type { DocumentResponse } from "@/types";

const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const STAGES = [
  { id: "understanding", label: "Understanding Dataset", icon: Database },
  { id: "business_context", label: "Detecting Business Context", icon: Activity },
  { id: "data_quality", label: "Assessing Data Quality", icon: Shield },
  { id: "statistical", label: "Running Statistical Analysis", icon: BarChart3 },
  { id: "kpis", label: "Identifying KPIs & Metrics", icon: Target },
  { id: "executive", label: "Generating Executive Insights", icon: Brain },
  { id: "visualizations", label: "Building Visualizations", icon: LineChart },
  { id: "dashboard", label: "Preparing Executive Dashboard", icon: FileText },
];

export default function AnalyticsPage() {
  const [docs, setDocs] = useState<DocumentResponse[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<number | null>(null);
  const [fetched, setFetched] = useState(false);
  const [running, setRunning] = useState(false);
  const [stageStatus, setStageStatus] = useState<Record<string, string>>({});
  const [result, setResult] = useState<Record<string, any> | null>(null);
  const token = typeof window !== "undefined" ? localStorage.getItem("aura_token") : "";
  const authH = { "Content-Type": "application/json", Authorization: `Bearer ${token}` } as Record<string, string>;

  useEffect(() => { if (!fetched) listDocuments().then(setDocs).finally(() => setFetched(true)); }, []);

  async function runAnalysis() {
    if (!selectedDoc) return;
    setRunning(true);
    setResult(null);
    setStageStatus({});
    // Simulate progress: mark stages as running one by one
    for (const s of STAGES) {
      setStageStatus((prev: Record<string, string>) => ({ ...prev, [s.id]: "running" }));
      await new Promise(r => setTimeout(r, 300));
    }
    try {
      const res = await fetch(`${apiBase}/api/v1/analytics/pipeline`, {
        method: "POST", headers: authH, body: JSON.stringify({ doc_id: selectedDoc }),
      });
      if (res.ok) {
        const data = await res.json();
        setResult(data);
        // Mark all stages as completed/failed based on response
        const statuses: Record<string, string> = {};
        for (const s of data.stages || []) {
          statuses[s.id] = s.status;
        }
        setStageStatus(statuses);
      }
    } catch {} finally { setRunning(false); }
  }

  const dash = result?.results?.dashboard || {};
  const exec = result?.results?.executive || {};
  const dq = result?.results?.data_quality || {};
  const biz = result?.results?.kpis || {};
  const stages = result?.stages || [];
  const ds = result?.results?.understanding || {};
  const bh = dash?.business_health || {};

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Business Analytics</h1>
          <p className="text-sm text-zinc-500">End-to-end automated business intelligence pipeline</p>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        {docs.map(d => (
          <button key={d.id} onClick={() => { setSelectedDoc(d.id); setResult(null); }}
            className={`rounded-xl border px-4 py-2 text-sm transition-colors ${selectedDoc === d.id ? "border-blue-600 bg-blue-600/20 text-blue-300" : "border-zinc-800 bg-zinc-900/50 text-zinc-400 hover:border-zinc-700"}`}>
            {d.title.slice(0, 30)}
          </button>
        ))}
      </div>

      {selectedDoc && (
        <div className="space-y-4">
          {/* Run button */}
          {!running && !result && (
            <button onClick={runAnalysis}
              className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-emerald-600 px-6 py-3 text-sm font-medium hover:from-blue-500 hover:to-emerald-500 shadow-lg shadow-blue-600/20">
              <Activity className="h-5 w-5" />Run Full Analytics Pipeline
            </button>
          )}

          {/* Processing Timeline */}
          {(running || stageStatus.dashboard) && !result && (
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-6">
              <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500 mb-4">Processing Pipeline</h2>
              <div className="space-y-3">
                {STAGES.map(s => {
                  const status = stageStatus[s.id] || "pending";
                  const Icon = s.icon;
                  return (
                    <div key={s.id} className="flex items-center gap-3">
                      {status === "completed" ? <CheckCircle className="h-5 w-5 text-emerald-500 shrink-0" /> :
                       status === "failed" ? <XCircle className="h-5 w-5 text-red-500 shrink-0" /> :
                       status === "running" ? <Loader2 className="h-5 w-5 text-blue-400 animate-spin shrink-0" /> :
                       <Clock className="h-5 w-5 text-zinc-700 shrink-0" />}
                      <Icon className={`h-4 w-4 shrink-0 ${status === "completed" ? "text-emerald-400" : status === "running" ? "text-blue-400" : "text-zinc-700"}`} />
                      <span className={`text-sm ${status === "completed" ? "text-zinc-200" : status === "failed" ? "text-red-400" : status === "running" ? "text-blue-300" : "text-zinc-600"}`}>
                        {s.label}
                      </span>
                      {stages.find((st: any) => st.id === s.id)?.duration_ms != null && (
                        <span className="text-[10px] text-zinc-600 ml-auto">{stages.find((st: any) => st.id === s.id).duration_ms}ms</span>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Pipeline Complete - Results Dashboard */}
          {result && !running && (
            <>
              {/* Execution Summary */}
              <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {result.success ? <CheckCircle className="h-5 w-5 text-emerald-400" /> : <XCircle className="h-5 w-5 text-red-400" />}
                    <span className="text-sm font-medium">{result.success ? "Analysis complete" : "Completed with errors"}</span>
                    <span className="text-xs text-zinc-500 ml-2">{(result.total_duration_ms / 1000).toFixed(1)}s</span>
                  </div>
                </div>
                {/* Stage status row */}
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {STAGES.map(s => {
                    const st = result.stages?.find((st: any) => st.id === s.id);
                    return (
                      <span key={s.id} className={`flex items-center gap-1 rounded px-1.5 py-0.5 text-[9px] ${st?.status === "completed" ? "bg-emerald-950 text-emerald-400" : st?.status === "failed" ? "bg-red-950 text-red-400" : "bg-zinc-800 text-zinc-600"}`}>
                        {st?.status === "completed" ? "✓" : st?.status === "failed" ? "✗" : "○"} {s.label.split(" ")[0]}
                      </span>
                    );
                  })}
                </div>
              </div>

              {/* Dataset Context + KPI Summary */}
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                {[
                  { label: "Industry", value: ds.industry || "—", icon: Activity, color: "text-blue-400" },
                  { label: "Domain", value: ds.dataset_type || "—", icon: Database, color: "text-emerald-400" },
                  { label: "Target", value: ds.target_variable || "—", icon: Target, color: "text-amber-400" },
                  { label: "Data Quality", value: dq.overall_score != null ? `${dq.overall_score}/100` : "—", icon: Shield, color: dq.overall_score >= 70 ? "text-emerald-400" : dq.overall_score >= 40 ? "text-amber-400" : "text-red-400" },
                  { label: "KPIs Detected", value: biz.kpi_summary?.total_detected || 0, icon: BarChart3, color: "text-purple-400" },
                  { label: "Findings", value: exec.key_findings?.length || 0, icon: Lightbulb, color: "text-blue-400" },
                  { label: "Risks", value: exec.risks?.length || 0, icon: AlertTriangle, color: "text-red-400" },
                  { label: "Recommendations", value: exec.recommendations?.length || 0, icon: CheckCircle, color: "text-emerald-400" },
                ].map(m => (
                  <div key={m.label} className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-3">
                    <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-zinc-500 mb-1">
                      <m.icon className={`h-3.5 w-3.5 ${m.color}`} />{m.label}
                    </div>
                    <p className="text-sm font-semibold text-zinc-200">{m.value}</p>
                  </div>
                ))}
              </div>

              {/* Executive Summary */}
              {dash.executive_summary && (
                <div className="rounded-xl border border-blue-900/30 bg-blue-950/20 p-5">
                  <div className="flex items-center gap-2 mb-2">
                    <Brain className="h-5 w-5 text-blue-400" />
                    <h2 className="text-sm font-medium uppercase tracking-wider text-blue-400">Executive Summary</h2>
                  </div>
                  <p className="text-sm leading-relaxed text-zinc-200">{dash.executive_summary}</p>
                </div>
              )}

              {/* Business Health */}
              {bh.overall && (
                <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
                  <div className="flex items-center justify-between mb-3">
                    <h2 className="text-xs font-medium uppercase tracking-wider text-zinc-500">Business Health Dashboard</h2>
                    <span className={`text-xl font-bold ${bh.overall >= 70 ? "text-emerald-400" : bh.overall >= 40 ? "text-amber-400" : "text-red-400"}`}>{bh.overall}<span className="text-xs text-zinc-600">/100</span></span>
                  </div>
                  <div className="grid gap-3 sm:grid-cols-6">
                    {[
                      { label: "Revenue", value: bh.revenue_health, icon: DollarSign },
                      { label: "Cost", value: bh.cost_health, icon: TrendingUp },
                      { label: "Growth", value: bh.growth_health, icon: TrendingUp },
                      { label: "Risk", value: bh.risk_health, icon: Shield },
                      { label: "Operations", value: bh.operations_health, icon: Clock },
                      { label: "Customers", value: bh.customer_health, icon: Users },
                    ].filter(m => m.value).map(m => (
                      <div key={m.label} className="text-center">
                        <p className="text-[10px] text-zinc-500">{m.label}</p>
                        <p className={`text-lg font-bold ${m.value >= 70 ? "text-emerald-400" : m.value >= 40 ? "text-amber-400" : "text-red-400"}`}>{m.value}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Key Visualizations */}
              {dash.charts?.length > 0 && (
                <div>
                  <h2 className="text-xs font-medium uppercase tracking-wider text-zinc-500 mb-3">Key Visualizations</h2>
                  <div className="grid gap-4 sm:grid-cols-2">
                    {dash.charts.slice(0, 4).map((ch: any, i: number) => (
                      <div key={i} className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-3">
                        <p className="text-[10px] text-zinc-500 mb-1">{ch.column} ({ch.chart_type})</p>
                        <iframe srcDoc={ch.html} className="w-full h-56 rounded-lg border-0" title={ch.column} />
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Risks + Recommendations */}
              <div className="grid gap-4 lg:grid-cols-2">
                {exec.risks?.length > 0 && (
                  <div className="rounded-xl border border-red-800/30 bg-red-950/20 p-5">
                    <h2 className="text-xs font-medium uppercase tracking-wider text-red-400 mb-3">Risks Identified</h2>
                    <div className="space-y-2">
                      {exec.risks.slice(0, 4).map((r: any, i: number) => (
                        <div key={i} className="rounded-lg bg-zinc-800/30 p-3">
                          <p className="text-xs font-semibold text-zinc-200">{r.name}</p>
                          <p className="text-[11px] text-zinc-400 mt-0.5">{r.description}</p>
                          {r.financial_exposure && <p className="text-[10px] text-amber-400 mt-0.5">Exposure: {r.financial_exposure}</p>}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {exec.recommendations?.length > 0 && (
                  <div className="rounded-xl border border-purple-800/30 bg-purple-950/20 p-5">
                    <h2 className="text-xs font-medium uppercase tracking-wider text-purple-400 mb-3">Recommendations</h2>
                    <div className="space-y-2">
                      {exec.recommendations.slice(0, 4).map((r: any, i: number) => (
                        <div key={i} className="rounded-lg bg-zinc-800/30 p-3">
                          <p className="text-xs font-semibold text-zinc-200">{r.title}</p>
                          {r.description && <p className="text-[11px] text-zinc-400 mt-0.5">{r.description}</p>}
                          {r.expected_outcome && <p className="text-[10px] text-zinc-500 mt-0.5">Outcome: {r.expected_outcome}</p>}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </>
          )}
        </div>
      )}
    </div>
  );
}
