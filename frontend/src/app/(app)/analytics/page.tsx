"use client";

import { useState, useEffect } from "react";
import {
  Brain, Shield, BarChart3, TrendingUp, Loader2, AlertTriangle,
  Lightbulb, DollarSign, Users, Clock, ArrowUpRight, ArrowDownRight,
  Target, Activity, CheckCircle, Database, LineChart,
} from "lucide-react";
import { listDocuments, getAnalytics } from "@/lib/api";
import type { DocumentResponse } from "@/types";

const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function AnalyticsPage() {
  const [docs, setDocs] = useState<DocumentResponse[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<number | null>(null);
  const [fetched, setFetched] = useState(false);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<Record<string, any>>({ charts: [], validated: [], insights: [], kpis: [] });
  const [pipelineStages, setPipelineStages] = useState<any[]>([]);
  const token = typeof window !== "undefined" ? localStorage.getItem("aura_token") : "";
  const authH = { "Content-Type": "application/json", Authorization: `Bearer ${token}` } as Record<string, string>;

  useEffect(() => { if (!fetched) listDocuments().then(setDocs).finally(() => setFetched(true)); }, []);

  async function runAnalysis() {
    if (!selectedDoc) return;
    setLoading(true);
    setPipelineStages([]);
    const stages = ["Understanding Dataset", "Detecting Business Context", "Assessing Data Quality",
      "Running Statistical Analysis", "Identifying KPIs", "Generating Executive Insights",
      "Building Visualizations", "Preparing Executive Dashboard"];
    for (const label of stages) {
      setPipelineStages(prev => [...prev, { label, status: "running" }]);
      await new Promise(r => setTimeout(r, 120));
    }
    try {
      const a = await getAnalytics(selectedDoc);
      const [bizRes, execRes, kpiRes, chartRes] = await Promise.all([
        fetch(`${apiBase}/api/v1/analytics/business-analytics`, { method: "POST", headers: authH, body: JSON.stringify({ doc_id: selectedDoc }) }),
        fetch(`${apiBase}/api/v1/analytics/executive-intelligence-v3`, { method: "POST", headers: authH, body: JSON.stringify({ doc_id: selectedDoc }) }),
        fetch(`${apiBase}/api/v1/analytics/kpis-v2`, { method: "POST", headers: authH, body: JSON.stringify({ doc_id: selectedDoc }) }),
        fetch(`${apiBase}/api/v1/charts/recommend`, { method: "POST", headers: authH, body: JSON.stringify({ doc_id: selectedDoc }) }),
      ]);
      const biz = bizRes.ok ? await bizRes.json() : {};
      const execV3 = execRes.ok ? await execRes.json() : {};
      const kpiV2 = kpiRes.ok ? await kpiRes.json() : { primary_kpis: [], secondary_kpis: [] };
      const chartRec = chartRes.ok ? await chartRes.json() : { charts: [] };

      setData({
        analytics: a,
        exec_summary: execV3.executive_summary || "",
        business_health: execV3.business_health || {},
        kpis: [...(kpiV2.primary_kpis || []), ...(kpiV2.secondary_kpis || [])].slice(0, 8),
        findings: execV3.key_findings || [],
        risks: execV3.risks || [],
        recommendations: execV3.recommendations || [],
        trends: biz.trend_analysis || {},
        comparative: biz.comparative_analysis || [],
        correlations: biz.correlations || [],
        charts: chartRec.charts || [],
        growth_rates: execV3.growth_rates || [],
        regional: execV3.regional_breakdown || [],
        margin: execV3.margin_analysis || null,
      });
      setPipelineStages(prev => prev.map(s => ({ ...s, status: "completed" })));
    } catch {} finally { setLoading(false); }
  }

  const d = data;

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div><h1 className="text-2xl font-semibold tracking-tight">Executive Analytics</h1><p className="text-sm text-zinc-500">Integrated business intelligence platform</p></div>
      </div>

      <div className="flex flex-wrap gap-2">
        {docs.map(doc => (
          <button key={doc.id} onClick={() => { setSelectedDoc(doc.id); setData({ charts: [], validated: [], insights: [], kpis: [] }); }}
            className={`rounded-xl border px-4 py-2 text-sm transition-colors ${selectedDoc === doc.id ? "border-blue-600 bg-blue-600/20 text-blue-300" : "border-zinc-800 bg-zinc-900/50 text-zinc-400 hover:border-zinc-700"}`}>
            {doc.title.slice(0, 30)}
          </button>
        ))}
      </div>

      {selectedDoc && (
        <div className="space-y-4">
          {!Object.keys(d.charts).length && !loading && (
            <button onClick={runAnalysis} className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-emerald-600 px-6 py-3 text-sm font-medium hover:from-blue-500 hover:to-emerald-500 shadow-lg shadow-blue-600/20">
              <Activity className="h-5 w-5" />Run Executive Analysis
            </button>
          )}

          {loading && (
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-6">
              <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500 mb-4">Processing Pipeline</h2>
              <div className="space-y-3">
                {pipelineStages.map((s, i) => (
                  <div key={i} className="flex items-center gap-3">
                    {s.status === "completed" ? <CheckCircle className="h-5 w-5 text-emerald-500 shrink-0" /> : <Loader2 className="h-5 w-5 text-blue-400 animate-spin shrink-0" />}
                    <span className={`text-sm ${s.status === "completed" ? "text-zinc-200" : "text-blue-300"}`}>{s.label}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {(d.exec_summary || d.kpis.length > 0 || d.charts.length > 0 || d.risks?.length > 0) && !loading && <>
            {/* Executive Summary */}
            {d.exec_summary && (
              <div className="rounded-xl border border-blue-900/30 bg-blue-950/20 p-5">
                <div className="flex items-center gap-2 mb-2"><Brain className="h-5 w-5 text-blue-400" /><h2 className="text-sm font-medium uppercase tracking-wider text-blue-400">Executive Summary</h2></div>
                <p className="text-sm leading-relaxed text-zinc-200">{d.exec_summary}</p>
              </div>
            )}

            {/* KPI Cards */}
            {d.kpis.length > 0 && (
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                {d.kpis.slice(0, 4).map((k: any, i: number) => (
                  <div key={i} className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[10px] font-medium uppercase tracking-wider text-zinc-500">{k.is_primary ? "PRIMARY KPI" : "KPI"}</span>
                      <BarChart3 className="h-4 w-4 text-zinc-500" />
                    </div>
                    <p className="text-xs text-zinc-500">{k.kpi}</p>
                    <p className="mt-1 text-xl font-semibold text-zinc-100">{k.value}</p>
                    {k.change !== null && (
                      <div className={`mt-1 flex items-center gap-1 text-xs ${k.change >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                        {k.change >= 0 ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}{Math.abs(k.change).toFixed(1)}%
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Chart Cards with Business Context */}
            <div className="grid gap-6 sm:grid-cols-2">
              {d.charts.slice(0, 6).map((ch: any, i: number) => (
                <div key={i} className="rounded-xl border border-zinc-800 bg-zinc-900/50 overflow-hidden">
                  <div className="p-4 pb-0">
                    <div className="flex items-center justify-between mb-1">
                      <h3 className="text-sm font-semibold text-zinc-200">{ch.column}</h3>
                      <span className="rounded bg-zinc-800 px-1.5 py-0.5 text-[9px] font-medium uppercase text-zinc-400">{ch.chart_type}</span>
                    </div>
                    {ch.business_reason && <p className="text-[11px] text-zinc-500 mb-2">{ch.business_reason}</p>}
                    {ch.quality_score != null && (
                      <div className="flex items-center gap-2 mb-2">
                        <div className="flex-1 h-1 rounded-full bg-zinc-800 overflow-hidden">
                          <div className={`h-full rounded-full ${ch.quality_score >= 70 ? "bg-emerald-500" : ch.quality_score >= 40 ? "bg-amber-500" : "bg-red-500"}`}
                            style={{ width: `${ch.quality_score}%` }} />
                        </div>
                        <span className="text-[10px] text-zinc-500">{ch.quality_score}% confidence</span>
                      </div>
                    )}
                  </div>
                  {ch.html && <iframe srcDoc={ch.html} className="w-full h-52 rounded-lg border-0" title={ch.column} />}
                </div>
              ))}
            </div>

            {/* Risks + Recommendations Grid */}
            <div className="grid gap-4 lg:grid-cols-2">
              {d.risks?.length > 0 && (
                <div className="rounded-xl border border-red-800/30 bg-red-950/20 p-5">
                  <h2 className="text-xs font-medium uppercase tracking-wider text-red-400 mb-3 flex items-center gap-1.5"><AlertTriangle className="h-4 w-4" />Risks</h2>
                  <div className="space-y-2">
                    {d.risks.slice(0, 4).map((r: any, i: number) => (
                      <div key={i} className="rounded-lg bg-zinc-800/30 p-3">
                        <div className="flex items-center justify-between"><p className="text-xs font-semibold text-zinc-200">{r.name}</p>
                          <span className={`rounded px-1.5 py-0.5 text-[9px] font-medium ${r.severity === "Critical" || r.severity === "High" ? "bg-red-900/50 text-red-300" : r.severity === "Medium" ? "bg-amber-900/50 text-amber-300" : "bg-blue-900/50 text-blue-300"}`}>{r.severity}</span></div>
                        <p className="text-[11px] text-zinc-400 mt-1">{r.description}</p>
                        {r.financial_exposure && <p className="text-[10px] text-amber-400 mt-0.5">Exposure: {r.financial_exposure}</p>}
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {d.recommendations?.length > 0 && (
                <div className="rounded-xl border border-purple-800/30 bg-purple-950/20 p-5">
                  <h2 className="text-xs font-medium uppercase tracking-wider text-purple-400 mb-3 flex items-center gap-1.5"><Lightbulb className="h-4 w-4" />Recommendations</h2>
                  <div className="space-y-2">
                    {d.recommendations.slice(0, 4).map((r: any, i: number) => (
                      <div key={i} className="flex items-start gap-3 rounded-lg bg-zinc-800/30 p-3">
                        <span className={`mt-0.5 h-2 w-2 shrink-0 rounded-full ${r.priority === "Critical" || r.priority === "High" ? "bg-red-500" : r.priority === "Medium" ? "bg-amber-500" : "bg-blue-500"}`} />
                        <div><p className="text-xs font-semibold text-zinc-200">{r.title}</p>
                          {r.description && <p className="text-[11px] text-zinc-400 mt-0.5">{r.description}</p>}
                          {r.expected_outcome && <p className="text-[10px] text-zinc-500 mt-0.5">Outcome: {r.expected_outcome}</p>}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Growth & Regional Breakdown */}
            {(d.growth_rates?.length > 0 || d.regional?.length > 0) && (
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                {d.growth_rates?.slice(0, 2).map((g: any, i: number) => (
                  <div key={i} className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-3">
                    <p className="text-[10px] text-zinc-500">{g.metric}</p>
                    <p className={`text-lg font-bold mt-0.5 ${g.change_pct >= 0 ? "text-emerald-400" : "text-red-400"}`}>{g.change_pct >= 0 ? "+" : ""}{g.change_pct}%</p>
                    <p className="text-[10px] text-zinc-500">{g.directional_word}</p>
                  </div>
                ))}
                {d.regional?.slice(0, 2).map((r: any, i: number) => (
                  <div key={`reg-${i}`} className="rounded-lg border border-blue-800/30 bg-blue-950/30 p-3">
                    <p className="text-[10px] text-blue-400">{r.segment}</p>
                    <p className="text-sm font-bold text-zinc-200 mt-0.5">{r.contribution_pct}%</p>
                    <p className="text-[10px] text-zinc-500">of {r.kpi}</p>
                  </div>
                ))}
              </div>
            )}
          </>}
        </div>
      )}
    </div>
  );
}
