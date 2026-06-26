"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  Brain, Shield, BarChart3, TrendingUp, Target, Lightbulb, Loader2,
  CheckCircle, XCircle, Clock, Database, FileText, DollarSign, Users,
  Activity, AlertTriangle,
} from "lucide-react";
import { listDocuments } from "@/lib/api";
import type { DocumentResponse } from "@/types";

const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const STAGES_CONFIG: Record<string, { icon: any; label: string; color: string }> = {
  understanding: { icon: Database, label: "Understanding Dataset", color: "text-blue-400" },
  business_context: { icon: Activity, label: "Detecting Business Context", color: "text-emerald-400" },
  data_quality: { icon: Shield, label: "Assessing Data Quality", color: "text-cyan-400" },
  statistical: { icon: BarChart3, label: "Running Statistical Analysis", color: "text-purple-400" },
  kpis: { icon: Target, label: "Identifying KPIs & Metrics", color: "text-amber-400" },
  executive: { icon: Brain, label: "Generating Executive Insights", color: "text-blue-400" },
  visualizations: { icon: TrendingUp, label: "Building Visualizations", color: "text-violet-400" },
  dashboard: { icon: FileText, label: "Preparing Executive Dashboard", color: "text-emerald-400" },
};

export default function PipelinePage() {
  const router = useRouter();
  const [docs, setDocs] = useState<DocumentResponse[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<number | null>(null);
  const [fetched, setFetched] = useState(false);
  const [running, setRunning] = useState(false);
  const [pipeline, setPipeline] = useState<Record<string, any> | null>(null);
  const token = typeof window !== "undefined" ? localStorage.getItem("aura_token") : "";
  const authH = { "Content-Type": "application/json", Authorization: `Bearer ${token}` } as Record<string, string>;

  useEffect(() => { if (!fetched) listDocuments().then(setDocs).finally(() => setFetched(true)); }, []);

  async function runPipeline() {
    if (!selectedDoc) return;
    setRunning(true);
    setPipeline(null);
    try {
      const res = await fetch(`${apiBase}/api/v1/analytics/pipeline`, {
        method: "POST", headers: authH, body: JSON.stringify({ doc_id: selectedDoc }),
      });
      if (res.ok) setPipeline(await res.json());
    } catch {} finally { setRunning(false); }
  }

  const stages = pipeline?.stages || [];
  const results = pipeline?.results || {};
  const ds = results.understanding || {};
  const dq = results.data_quality || {};
  const exec = results.executive || {};
  const biz = results.kpis || {};
  const dash = results.dashboard || {};
  const bh = dash?.business_health || {};

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Analytics Pipeline</h1>
          <p className="text-sm text-zinc-500">End-to-end automated business intelligence processing</p>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        {docs.map(d => (
          <button key={d.id} onClick={() => { setSelectedDoc(d.id); setPipeline(null); }}
            className={`rounded-xl border px-4 py-2 text-sm transition-colors ${selectedDoc === d.id ? "border-blue-600 bg-blue-600/20 text-blue-300" : "border-zinc-800 bg-zinc-900/50 text-zinc-400 hover:border-zinc-700"}`}>
            {d.title.slice(0, 30)}
          </button>
        ))}
      </div>

      {selectedDoc && (
        <div className="space-y-4">
          {!pipeline && !running && (
            <button onClick={runPipeline}
              className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-emerald-600 px-6 py-3 text-sm font-medium hover:from-blue-500 hover:to-emerald-500 shadow-lg shadow-blue-600/20">
              <Activity className="h-5 w-5" />Run Full Analytics Pipeline
            </button>
          )}

          {/* Processing Timeline */}
          {running && (
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-6">
              <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500 mb-4">Processing...</h2>
              <div className="space-y-3">
                {Object.entries(STAGES_CONFIG).map(([id, cfg]) => {
                  const stageDone = pipeline?.stages?.find((s: any) => s.id === id);
                  const status = stageDone?.status || "pending";
                  return (
                    <div key={id} className="flex items-center gap-3">
                      {status === "completed" ? <CheckCircle className="h-5 w-5 text-emerald-500 shrink-0" /> :
                       status === "failed" ? <XCircle className="h-5 w-5 text-red-500 shrink-0" /> :
                       status === "running" ? <Loader2 className="h-5 w-5 text-blue-400 animate-spin shrink-0" /> :
                       <Clock className="h-5 w-5 text-zinc-700 shrink-0" />}
                      <span className={`text-sm ${status === "completed" ? "text-zinc-200" : status === "failed" ? "text-red-400" : status === "running" ? "text-blue-300" : "text-zinc-600"}`}>
                        {cfg.label}
                      </span>
                      {stageDone?.duration_ms != null && (
                        <span className="text-[10px] text-zinc-600 ml-auto">{stageDone.duration_ms}ms</span>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* Pipeline Complete - Show Results */}
          {pipeline && !running && (
            <>
              {/* Execution Summary */}
              <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    {pipeline.success ? <CheckCircle className="h-5 w-5 text-emerald-400" /> : <XCircle className="h-5 w-5 text-red-400" />}
                    <span className="text-sm font-medium">{pipeline.success ? "Pipeline completed successfully" : "Pipeline completed with errors"}</span>
                  </div>
                  <span className="text-xs text-zinc-500">{(pipeline.total_duration_ms / 1000).toFixed(1)}s total</span>
                </div>
                {pipeline.errors?.length > 0 && (
                  <div className="mt-2 text-xs text-red-400">Errors: {pipeline.errors.join("; ")}</div>
                )}
              </div>

              {/* Quick Stats */}
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                {[
                  { label: "Industry", value: ds.industry || "Detected", icon: Activity, color: "text-blue-400" },
                  { label: "Dataset Type", value: ds.dataset_type || "Analyzed", icon: Database, color: "text-emerald-400" },
                  { label: "Target Variable", value: ds.target_variable || "None", icon: Target, color: "text-amber-400" },
                  { label: "Data Quality", value: `${dq.overall_score || "—"}/100`, icon: Shield, color: "text-cyan-400" },
                  { label: "KPIs Detected", value: `${biz.kpi_summary?.total_detected || 0}`, icon: BarChart3, color: "text-purple-400" },
                  { label: "Findings", value: `${exec.key_findings?.length || 0}`, icon: Lightbulb, color: "text-blue-400" },
                  { label: "Risks", value: `${exec.risks?.length || 0}`, icon: AlertTriangle, color: "text-red-400" },
                  { label: "Recommendations", value: `${exec.recommendations?.length || 0}`, icon: CheckCircle, color: "text-emerald-400" },
                ].map(m => (
                  <div key={m.label} className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-3">
                    <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-zinc-500 mb-1">
                      <m.icon className={`h-3.5 w-3.5 ${m.color}`} />{m.label}
                    </div>
                    <p className="text-sm font-semibold text-zinc-200">{m.value}</p>
                  </div>
                ))}
              </div>

              {/* Stages Timeline */}
              <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
                <h2 className="text-xs font-medium uppercase tracking-wider text-zinc-500 mb-3">Processing Timeline</h2>
                <div className="space-y-2">
                  {stages.map((s: any) => {
                    const cfg = STAGES_CONFIG[s.id] || { icon: Clock, label: s.id, color: "text-zinc-400" };
                    const Icon = cfg.icon;
                    return (
                      <div key={s.id} className="flex items-center gap-3">
                        {s.status === "completed" ? <CheckCircle className="h-4 w-4 text-emerald-500 shrink-0" /> :
                         s.status === "failed" ? <XCircle className="h-4 w-4 text-red-500 shrink-0" /> :
                         <Clock className="h-4 w-4 text-zinc-700 shrink-0" />}
                        <Icon className={`h-3.5 w-3.5 ${cfg.color} shrink-0`} />
                        <span className="text-xs text-zinc-300 flex-1">{cfg.label}</span>
                        <span className="text-[10px] text-zinc-600">{s.duration_ms ? `${s.duration_ms}ms` : "—"}</span>
                        <span className={`text-[10px] font-medium ${s.status === "completed" ? "text-emerald-500" : s.status === "failed" ? "text-red-500" : "text-zinc-500"}`}>
                          {s.status}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Dashboard Results Preview */}
              {dash.executive_summary && (
                <div className="rounded-xl border border-blue-900/30 bg-blue-950/20 p-5">
                  <h2 className="text-xs font-medium uppercase tracking-wider text-blue-400 mb-2">Executive Summary</h2>
                  <p className="text-sm text-zinc-200">{dash.executive_summary}</p>
                </div>
              )}

              {/* Business Health */}
              {bh.overall && (
                <div className="grid gap-3 sm:grid-cols-6">
                  {[
                    { label: "Overall", value: bh.overall, icon: Shield },
                    { label: "Revenue", value: bh.revenue_health, icon: DollarSign },
                    { label: "Cost", value: bh.cost_health, icon: TrendingUp },
                    { label: "Growth", value: bh.growth_health, icon: TrendingUp },
                    { label: "Risk", value: bh.risk_health, icon: AlertTriangle },
                    { label: "Operations", value: bh.operations_health, icon: Users },
                  ].filter(m => m.value).map(m => (
                    <div key={m.label} className="text-center">
                      <p className="text-[10px] text-zinc-500">{m.label}</p>
                      <p className={`text-lg font-bold ${m.value >= 70 ? "text-emerald-400" : m.value >= 40 ? "text-amber-400" : "text-red-400"}`}>{m.value}</p>
                    </div>
                  ))}
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
