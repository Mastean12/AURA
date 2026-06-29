"use client";

import { useState, useEffect, useRef } from "react";
import {
  Brain, Shield, BarChart3, TrendingUp, MessageSquare,
  FileText, Send, Loader2, AlertTriangle,
  Lightbulb, Flag, Bot, User, DollarSign, Users,
  Clock, ArrowUpRight, ArrowDownRight, Database, Edit2, Check, X,
  Target, LineChart, PieChart, Activity, CheckCircle,
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
  const [pipelineStages, setPipelineStages] = useState<any[]>([]);
  const [execData, setExecData] = useState<Record<string, any> | null>(null);
  const [kpiV2, setKpiV2] = useState<Record<string, any> | null>(null);
  const token = typeof window !== "undefined" ? localStorage.getItem("aura_token") : "";
  const authH = { "Content-Type": "application/json", Authorization: `Bearer ${token}` } as Record<string, string>;

  useEffect(() => { if (!fetched) listDocuments().then(setDocs).finally(() => setFetched(true)); }, []);

  async function runAnalysis() {
    if (!selectedDoc) return;
    setLoading(true);
    setPipelineStages([]);
    const STAGE_LABELS = [
      "Understanding Dataset", "Detecting Business Context", "Assessing Data Quality",
      "Running Statistical Analysis", "Identifying KPIs", "Generating Executive Insights",
      "Building Visualizations", "Preparing Executive Dashboard",
    ];
    for (const label of STAGE_LABELS) {
      setPipelineStages(prev => [...prev, { label, status: "running" }]);
      await new Promise(r => setTimeout(r, 150));
    }
    try {
      const a = await getAnalytics(selectedDoc);
      setAnalytics(a as any);
      const [bizRes, execRes, kpiRes] = await Promise.all([
        fetch(`${apiBase}/api/v1/analytics/business-analytics`, {
          method: "POST", headers: authH, body: JSON.stringify({ doc_id: selectedDoc }),
        }),
        fetch(`${apiBase}/api/v1/analytics/executive-intelligence-v3`, {
          method: "POST", headers: authH, body: JSON.stringify({ doc_id: selectedDoc }),
        }),
        fetch(`${apiBase}/api/v1/analytics/kpis-v2`, {
          method: "POST", headers: authH, body: JSON.stringify({ doc_id: selectedDoc }),
        }),
      ]);
      if (bizRes.ok) setBusinessData(await bizRes.json());
      if (execRes.ok) setExecData(await execRes.json());
      if (kpiRes.ok) setKpiV2(await kpiRes.json());
      setPipelineStages(prev => prev.map(s => ({ ...s, status: "completed" })));
    } catch {} finally { setLoading(false); }
  }

  const kpiSummary = businessData?.kpi_summary || {};
  const chartRecs = businessData?.chart_recommendations || [];
  const trend = businessData?.trend_analysis || {};
  const charts = businessData?.charts || [];
  const comparative = businessData?.comparative_analysis || [];
  const correlations = businessData?.correlations || [];
  const kpis = kpiSummary.kpis || [];
  const execBH = execData?.business_health || {};
  const execImpact = execData?.business_impact || {};
  const kpiV2Primary = kpiV2?.primary_kpis || [];
  const kpiV2Secondary = kpiV2?.secondary_kpis || [];
  const execFindings = execData?.key_findings || [];
  const execRootCauses = execData?.root_causes || [];
  const execRisks = execData?.risks || [];
  const execOpps = execData?.opportunities || [];
  const execRecs = execData?.recommendations || [];
  const growthRates = execData?.growth_rates || [];
  const regional = execData?.regional_breakdown || [];
  const deptData = execData?.department_breakdown || [];
  const marginAnalysis = execData?.margin_analysis;

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
          {loading && (
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-6">
              <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500 mb-4">Processing Pipeline</h2>
              <div className="space-y-3">
                {pipelineStages.map((s, i) => (
                  <div key={i} className="flex items-center gap-3">
                    {s.status === "completed" ? <CheckCircle className="h-5 w-5 text-emerald-500 shrink-0" /> :
                     <Loader2 className="h-5 w-5 text-blue-400 animate-spin shrink-0" />}
                    <span className={`text-sm ${s.status === "completed" ? "text-zinc-200" : "text-blue-300"}`}>{s.label}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

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

            {/* Section 4: Executive Intelligence */}
            {execData?.executive_summary && (
              <div className="rounded-xl border border-blue-900/30 bg-blue-950/20 p-5">
                <div className="flex items-center gap-2 mb-2">
                  <Brain className="h-5 w-5 text-blue-400" />
                  <h2 className="text-sm font-medium uppercase tracking-wider text-blue-400">Executive Summary</h2>
                  <span className="ml-auto text-xs text-zinc-500">{(execData.confidence * 100).toFixed(0)}% confidence</span>
                </div>
                <p className="text-sm leading-relaxed text-zinc-200">{execData.executive_summary}</p>
              </div>
            )}

            {/* Intelligent KPI Detection */}
            {kpiV2Primary.length > 0 && (
              <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
                <div className="flex items-center gap-2 mb-3">
                  <BarChart3 className="h-5 w-5 text-emerald-400" />
                  <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Intelligent KPIs</h2>
                  <span className="ml-auto text-xs text-zinc-500">{kpiV2?.total_detected || 0} detected</span>
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                  {kpiV2Primary.map((k: any, i: number) => (
                    <div key={i} className="rounded-lg bg-emerald-950/30 border border-emerald-800/30 p-3">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] uppercase text-emerald-400 font-medium">Primary KPI</span>
                        <span className="text-xs text-zinc-500">{(k.importance_score || 0).toFixed(0)}%</span>
                      </div>
                      <p className="text-sm font-semibold text-zinc-200 mt-1">{k.kpi}</p>
                      <p className="text-lg font-bold text-zinc-100">{k.value}</p>
                      {k.change !== null && (
                        <span className={`text-xs ${k.change >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                          {k.change >= 0 ? "↑" : "↓"} {Math.abs(k.change).toFixed(1)}%
                        </span>
                      )}
                    </div>
                  ))}
                  {kpiV2Secondary.slice(0, 4).map((k: any, i: number) => (
                    <div key={i} className="rounded-lg bg-zinc-800/30 p-3">
                      <p className="text-[10px] text-zinc-500">Secondary KPI</p>
                      <div className="flex items-center justify-between">
                        <p className="text-sm font-semibold text-zinc-200">{k.kpi}</p>
                        <p className="text-sm font-bold text-zinc-100">{k.value}</p>
                      </div>
                      {k.change !== null && (
                        <span className={`text-xs ${k.change >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                          {k.change >= 0 ? "↑" : "↓"} {Math.abs(k.change).toFixed(1)}%
                        </span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Business Health Dashboard */}
            {execBH.overall && (
              <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
                <div className="flex items-center justify-between mb-3">
                  <h2 className="text-xs font-medium uppercase tracking-wider text-zinc-500">Business Health Dashboard</h2>
                  <span className={`text-xl font-bold ${execBH.overall >= 70 ? "text-emerald-400" : execBH.overall >= 40 ? "text-amber-400" : "text-red-400"}`}>{execBH.overall}<span className="text-xs text-zinc-600">/100</span></span>
                </div>
                <div className="grid gap-3 sm:grid-cols-6">
                  {[
                    { label: "Revenue", value: execBH.revenue_health, icon: DollarSign },
                    { label: "Cost", value: execBH.cost_health, icon: TrendingUp },
                    { label: "Growth", value: execBH.growth_health, icon: TrendingUp },
                    { label: "Risk", value: execBH.risk_health, icon: Shield },
                    { label: "Operations", value: execBH.operations_health, icon: Clock },
                    { label: "Customers", value: execBH.customer_health, icon: Users },
                  ].filter(m => m.value).map(m => (
                    <div key={m.label} className="text-center rounded-lg bg-zinc-800/30 p-2">
                      <p className="text-[10px] text-zinc-500">{m.label}</p>
                      <p className={`text-lg font-bold ${m.value >= 70 ? "text-emerald-400" : m.value >= 40 ? "text-amber-400" : "text-red-400"}`}>{m.value}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Business Impact */}
            {execImpact.revenue_impact && (
              <div className="grid gap-4 sm:grid-cols-2">
                {[{ label: "Revenue Impact", value: execImpact.revenue_impact, icon: DollarSign, color: "text-emerald-400" },
                  { label: "Cost Impact", value: execImpact.cost_impact, icon: TrendingUp, color: "text-red-400" },
                  { label: "Operational Impact", value: execImpact.operational_impact, icon: Clock, color: "text-blue-400" },
                  { label: "Customer Impact", value: execImpact.customer_impact, icon: Users, color: "text-purple-400" },
                ].filter(m => m.value).map(m => (
                  <div key={m.label} className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-3">
                    <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-zinc-500 mb-1">
                      <m.icon className={`h-3.5 w-3.5 ${m.color}`} />{m.label}
                    </div>
                    <p className="text-xs text-zinc-300">{m.value}</p>
                  </div>
                ))}
              </div>
            )}

            {/* Executive Findings */}
            {execFindings.length > 0 && (
              <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
                <div className="flex items-center gap-2 mb-3">
                  <Lightbulb className="h-5 w-5 text-emerald-400" />
                  <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Executive Findings</h2>
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                  {execFindings.slice(0, 6).map((f: any, i: number) => (
                    <div key={i} className="rounded-lg bg-zinc-800/30 p-3">
                      <div className="flex items-start gap-2">
                        <span className={`mt-1 h-2 w-2 shrink-0 rounded-full ${f.impact === "high" ? "bg-red-500" : f.impact === "medium" ? "bg-amber-500" : "bg-blue-500"}`} />
                        <div>
                          <p className="text-xs font-semibold text-zinc-200">{f.title}</p>
                          {f.detail && <p className="text-[11px] text-zinc-400 mt-0.5">{f.detail}</p>}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Root Causes */}
            {execRootCauses.length > 0 && (
              <div className="rounded-xl border border-amber-800/30 bg-amber-950/20 p-5">
                <div className="flex items-center gap-2 mb-3">
                  <AlertTriangle className="h-5 w-5 text-amber-400" />
                  <h2 className="text-sm font-medium uppercase tracking-wider text-amber-400">Root Cause Analysis</h2>
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                  {execRootCauses.slice(0, 4).map((rc: any, i: number) => (
                    <div key={i} className="rounded-lg bg-zinc-800/30 p-3">
                      <p className="text-xs font-medium text-zinc-200">{rc.cause}</p>
                      {rc.evidence && <p className="text-[11px] text-zinc-400 mt-0.5">Evidence: {rc.evidence}</p>}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Growth & Performance Breakdown */}
            {(growthRates.length > 0 || regional.length > 0 || deptData.length > 0) && (
              <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
                <h2 className="text-xs font-medium uppercase tracking-wider text-zinc-500 mb-3">Growth & Performance Breakdown</h2>
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {growthRates.slice(0, 2).map((g: any, i: number) => (
                    <div key={i} className="rounded-lg bg-zinc-800/30 p-3">
                      <p className="text-[10px] text-zinc-500">{g.metric}</p>
                      <p className={`text-lg font-bold mt-0.5 ${g.change_pct >= 0 ? "text-emerald-400" : "text-red-400"}`}>{g.change_pct >= 0 ? "+" : ""}{g.change_pct}%</p>
                      <p className="text-[10px] text-zinc-500">{g.directional_word}</p>
                    </div>
                  ))}
                  {regional.slice(0, 2).map((r: any, i: number) => (
                    <div key={`reg-${i}`} className="rounded-lg bg-blue-950/30 border border-blue-800/30 p-3">
                      <p className="text-[10px] text-blue-400">{r.segment}</p>
                      <p className="text-sm font-bold text-zinc-200 mt-0.5">{r.contribution_pct}%</p>
                      <p className="text-[10px] text-zinc-500">of {r.kpi}</p>
                    </div>
                  ))}
                  {deptData.slice(0, 2).map((d: any, i: number) => (
                    <div key={`dept-${i}`} className="rounded-lg bg-amber-950/30 border border-amber-800/30 p-3">
                      <p className="text-[10px] text-amber-400">{d.kpi} by Department</p>
                      <p className="text-xs text-zinc-300 mt-1">Best: <span className="text-emerald-400">{d.best_department}</span></p>
                      <p className="text-xs text-zinc-300">Worst: <span className="text-red-400">{d.worst_department}</span></p>
                      <p className="text-[10px] text-zinc-500 mt-0.5">{d.gap_pct}% gap</p>
                    </div>
                  ))}
                  {marginAnalysis && (
                    <div className="rounded-lg bg-red-950/30 border border-red-800/30 p-3">
                      <p className="text-[10px] text-red-400">Margin Alert</p>
                      <p className="text-[11px] text-zinc-300 mt-1">{marginAnalysis.insight}</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Risks */}
            {execRisks.length > 0 && (
              <div className="rounded-xl border border-red-800/30 bg-red-950/20 p-5">
                <div className="flex items-center gap-2 mb-3">
                  <AlertTriangle className="h-5 w-5 text-red-400" />
                  <h2 className="text-sm font-medium uppercase tracking-wider text-red-400">Business Risks</h2>
                </div>
                <div className="space-y-2">
                  {execRisks.slice(0, 4).map((r: any, i: number) => (
                    <div key={i} className="rounded-lg bg-zinc-800/30 p-3">
                      <div className="flex items-center justify-between mb-1">
                        <p className="text-xs font-semibold text-zinc-200">{r.name}</p>
                        <span className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${r.severity === "Critical" || r.severity === "High" ? "bg-red-900/50 text-red-300" : "bg-amber-900/50 text-amber-300"}`}>{r.severity}</span>
                      </div>
                      <p className="text-[11px] text-zinc-400">{r.description}</p>
                      {r.financial_exposure && <p className="text-[10px] text-amber-400 mt-0.5">Exposure: {r.financial_exposure}</p>}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Recommendations */}
            {execRecs.length > 0 && (
              <div className="rounded-xl border border-purple-800/30 bg-purple-950/20 p-5">
                <div className="flex items-center gap-2 mb-3">
                  <CheckCircle className="h-5 w-5 text-purple-400" />
                  <h2 className="text-sm font-medium uppercase tracking-wider text-purple-400">Recommended Actions</h2>
                </div>
                <div className="space-y-2">
                  {execRecs.slice(0, 4).map((r: any, i: number) => (
                    <div key={i} className="flex items-start gap-3 rounded-lg bg-zinc-800/30 p-3">
                      <span className={`mt-0.5 h-2 w-2 shrink-0 rounded-full ${r.priority === "Critical" || r.priority === "High" ? "bg-red-500" : r.priority === "Medium" ? "bg-amber-500" : "bg-blue-500"}`} />
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <p className="text-xs font-semibold text-zinc-200">{r.title}</p>
                          <span className={`rounded px-1.5 py-0.5 text-[9px] font-medium uppercase ${r.priority === "Critical" || r.priority === "High" ? "bg-red-900/50 text-red-300" : r.priority === "Medium" ? "bg-amber-900/50 text-amber-300" : "bg-blue-900/50 text-blue-300"}`}>{r.priority}</span>
                        </div>
                        {r.description && <p className="text-[11px] text-zinc-400 mt-0.5">{r.description}</p>}
                        {r.expected_outcome && <p className="text-[10px] text-zinc-500 mt-0.5">Outcome: {r.expected_outcome}</p>}
                      </div>
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
        </div>
      )}
    </div>
  );
}
