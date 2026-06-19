"use client";

import { useState, useEffect } from "react";
import {
  TrendingUp, AlertTriangle, Shield, Lightbulb, Brain, Target,
  Loader2, DollarSign, Users, Clock, ChevronDown, ChevronRight,
  ArrowUpRight, ArrowDownRight, CheckCircle, XCircle, BarChart3,
  FileText,
} from "lucide-react";
import { listDocuments, getAnalytics } from "@/lib/api";
import type { DocumentResponse } from "@/types";

const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function PredictivePage() {
  const [docs, setDocs] = useState<DocumentResponse[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<number | null>(null);
  const [fetched, setFetched] = useState(false);
  const [result, setResult] = useState<Record<string, any> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showTech, setShowTech] = useState(false);

  useEffect(() => {
    if (!fetched) listDocuments().then(setDocs).finally(() => setFetched(true));
  }, []);

  async function runAnalysis() {
    if (!selectedDoc) return;
    setLoading(true);
    setError("");
    try {
      const token = localStorage.getItem("aura_token");
      const res = await fetch(`${apiBase}/api/v1/predictive/analysis`, {
        method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ doc_id: selectedDoc }),
      });
      if (!res.ok) { const err = await res.json(); setError(err.detail || "Analysis failed"); return; }
      setResult(await res.json());
    } catch { setError("Connection failed"); }
    finally { setLoading(false); }
  }

  const bi = result?.business_impact || {};
  const scenarios = result?.scenarios || {};
  const rootCauses = result?.root_causes || [];
  const recs = result?.recommendations || [];
  const opps = result?.opportunities || [];
  const risks = result?.risks || [];
  const tech = result?.technical || {};
  const feats = tech?.feature_importance || [];

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Executive Predictive Intelligence</h1>
          <p className="text-sm text-zinc-500">Business predictions, risks, opportunities, and recommended actions</p>
        </div>
      </div>

      {/* Doc selector */}
      <div className="flex flex-wrap gap-2">
        {docs.map(d => (
          <button key={d.id} onClick={() => setSelectedDoc(d.id)}
            className={`rounded-xl border px-4 py-2 text-sm transition-colors ${
              selectedDoc === d.id ? "border-blue-600 bg-blue-600/20 text-blue-300" : "border-zinc-800 bg-zinc-900/50 text-zinc-400 hover:border-zinc-700"
            }`}>
            {d.title.length > 30 ? d.title.slice(0, 30) + "..." : d.title}
          </button>
        ))}
      </div>

      {selectedDoc && (
        <div className="space-y-4">
          {/* Run button */}
          {!result && !loading && (
            <button onClick={runAnalysis}
              className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 px-6 py-3 text-sm font-medium hover:from-blue-500 hover:to-purple-500 shadow-lg shadow-blue-600/20">
              <Brain className="h-5 w-5" />Run Executive Prediction Analysis
            </button>
          )}
          {loading && <div className="space-y-4">{[1,2,3,4].map(i => <div key={i} className="h-24 animate-pulse rounded-xl bg-zinc-800/50" />)}</div>}
          {error && <p className="text-xs text-red-400">{error}</p>}

          {result && (
            <>
              {/* 1. Executive Summary */}
              <div className="rounded-xl border border-blue-900/30 bg-gradient-to-br from-blue-950/20 to-zinc-900/50 p-5">
                <div className="flex items-center gap-2 mb-3">
                  <FileText className="h-5 w-5 text-blue-400" />
                  <h2 className="text-sm font-medium uppercase tracking-wider text-blue-400">Executive Prediction Summary</h2>
                </div>
                <p className="text-sm leading-relaxed text-zinc-200 mb-3">{result?.executive_summary || "Analysis complete."}</p>
                {bi && (
                  <div className="grid gap-3 sm:grid-cols-5">
                    {[
                      { label: "Population at Risk", value: bi.population_at_risk?.toLocaleString(), unit: `of ${bi.total_population?.toLocaleString()}`, icon: Users, color: "text-red-400" },
                      { label: "Revenue at Risk", value: bi.revenue_at_risk_formatted, icon: DollarSign, color: "text-amber-400" },
                      { label: "Business Impact", value: bi.impact_level, icon: AlertTriangle, color: bi.impact_level === "Critical" ? "text-red-400" : "text-amber-400" },
                      { label: "Confidence", value: `${bi.confidence}%`, icon: Brain, color: "text-blue-400" },
                      { label: "Urgency", value: bi.urgency?.split(" ")[0], unit: bi.urgency?.split(" ").slice(1).join(" "), icon: Clock, color: "text-purple-400" },
                    ].map(m => (
                      <div key={m.label} className="rounded-lg bg-zinc-800/30 p-3 text-center">
                        <m.icon className={`mx-auto h-4 w-4 ${m.color} mb-1`} />
                        <p className="text-lg font-semibold text-zinc-200">{m.value}</p>
                        <p className="text-[10px] text-zinc-500">{m.label}</p>
                        {m.unit && <p className="text-[9px] text-zinc-700">{m.unit}</p>}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* 2. Root Cause Analysis */}
              {rootCauses.length > 0 && (
                <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
                  <div className="flex items-center gap-2 mb-4">
                    <Target className="h-5 w-5 text-amber-400" />
                    <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Why This Is Happening</h2>
                  </div>
                  <div className="space-y-2">
                    {rootCauses.map((cause: string, i: number) => (
                      <div key={i} className="flex items-start gap-2 rounded-lg bg-zinc-800/30 p-3">
                        <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-amber-600/20 text-[10px] font-semibold text-amber-400">{i + 1}</span>
                        <p className="text-xs text-zinc-300">{cause}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 3. Risk + Opportunity Grid */}
              <div className="grid gap-4 lg:grid-cols-2">
                {/* Risks */}
                <div className="rounded-xl border border-red-800/30 bg-red-950/20 p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <AlertTriangle className="h-5 w-5 text-red-400" />
                    <h2 className="text-sm font-medium uppercase tracking-wider text-red-400">Top Risks</h2>
                  </div>
                  {risks.map((r: any, i: number) => (
                    <div key={i} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-semibold text-zinc-200">{r.name}</span>
                        <span className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${
                          r.severity === "Critical" ? "bg-red-900/50 text-red-300" :
                          r.severity === "High" ? "bg-amber-900/50 text-amber-300" : "bg-blue-900/50 text-blue-300"
                        }`}>{r.severity}</span>
                      </div>
                      <p className="text-xs text-zinc-400">{r.impact}</p>
                      <div className="flex gap-2 text-[10px] text-zinc-500">
                        <span>Confidence: {r.confidence}</span>
                        <span>Affected: {r.affected}</span>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Opportunities */}
                <div className="rounded-xl border border-emerald-800/30 bg-emerald-950/20 p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <Lightbulb className="h-5 w-5 text-emerald-400" />
                    <h2 className="text-sm font-medium uppercase tracking-wider text-emerald-400">Top Opportunities</h2>
                  </div>
                  <div className="space-y-3">
                    {opps.map((o: any, i: number) => (
                      <div key={i} className="rounded-lg bg-zinc-800/30 p-3">
                        <p className="text-xs font-semibold text-zinc-200">{o.title}</p>
                        <p className="text-[11px] text-zinc-400 mt-1">{o.description}</p>
                        <p className="text-[10px] text-emerald-400 mt-1">{o.revenue_impact}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* 4. Scenario Analysis */}
              {scenarios.expected_case != null && (
                <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
                  <div className="flex items-center gap-2 mb-4">
                    <TrendingUp className="h-5 w-5 text-violet-400" />
                    <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Scenario Analysis</h2>
                  </div>
                  <div className="grid gap-4 sm:grid-cols-3">
                    {[
                      { label: "Best Case", value: scenarios.best_case, color: "text-emerald-400", bar: "bg-emerald-500" },
                      { label: "Expected Case", value: scenarios.expected_case, color: "text-amber-400", bar: "bg-amber-500" },
                      { label: "Worst Case", value: scenarios.worst_case, color: "text-red-400", bar: "bg-red-500" },
                    ].map(s => {
                      const maxVal = Math.max(scenarios.best_case, scenarios.expected_case, scenarios.worst_case);
                      const pct = maxVal > 0 ? (s.value / maxVal) * 100 : 0;
                      return (
                        <div key={s.label} className="rounded-lg bg-zinc-800/30 p-4">
                          <p className="text-[10px] uppercase tracking-wider text-zinc-500">{s.label}</p>
                          <p className={`text-lg font-bold ${s.color}`}>${s.value?.toLocaleString()}</p>
                          <div className="mt-2 h-2 rounded-full bg-zinc-800 overflow-hidden">
                            <div className={`h-full rounded-full ${s.bar}`} style={{ width: `${pct}%` }} />
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* 5. Recommended Actions */}
              {recs.length > 0 && (
                <div className="rounded-xl border border-purple-800/30 bg-purple-950/20 p-5">
                  <div className="flex items-center gap-2 mb-4">
                    <Shield className="h-5 w-5 text-purple-400" />
                    <h2 className="text-sm font-medium uppercase tracking-wider text-purple-400">Recommended Actions</h2>
                  </div>
                  <div className="space-y-2">
                    {recs.map((r: any, i: number) => (
                      <div key={i} className="flex items-start gap-3 rounded-lg bg-zinc-800/30 p-3">
                        <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-purple-600/20 text-xs font-bold text-purple-400">{r.priority}</span>
                        <div className="min-w-0 flex-1">
                          <p className="text-xs font-semibold text-zinc-200">{r.action}</p>
                          <div className="flex flex-wrap gap-3 mt-1 text-[10px] text-zinc-500">
                            <span>Expected reduction: {r.expected_churn_reduction}</span>
                            <span>Revenue impact: {r.revenue_impact}</span>
                            <span>Effort: {r.effort}</span>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* 6. Advanced Analytics (collapsible) */}
              <div className="rounded-xl border border-zinc-800 bg-zinc-900/30">
                <button onClick={() => setShowTech(!showTech)}
                  className="flex w-full items-center justify-between px-5 py-3 text-xs font-medium text-zinc-500 hover:text-zinc-300">
                  <span>Advanced Analytics (for analysts)</span>
                  {showTech ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                </button>
                {showTech && (
                  <div className="border-t border-zinc-800 p-5 space-y-4">
                    <div className="grid gap-3 sm:grid-cols-4">
                      <div className="rounded-lg bg-zinc-800/30 p-3 text-center">
                        <p className="text-[10px] text-zinc-500">Model</p>
                        <p className="text-xs font-semibold text-zinc-200 capitalize">{tech.model || "—"}</p>
                      </div>
                      {Object.entries(tech.metrics_display || {}).filter(([_, v]) => v != null).map(([key, val]) => (
                        <div key={key} className="rounded-lg bg-zinc-800/30 p-3 text-center">
                          <p className="text-[10px] text-zinc-500 uppercase">{key}</p>
                          <p className="text-xs font-semibold text-zinc-200">{typeof val === "number" ? (key === "mape" ? `${val.toFixed(1)}%` : val.toFixed(3)) : "—"}</p>
                        </div>
                      ))}
                      <div className="rounded-lg bg-zinc-800/30 p-3 text-center">
                        <p className="text-[10px] text-zinc-500">Target</p>
                        <p className="text-xs font-semibold text-zinc-200">{tech.target || "—"}</p>
                      </div>
                      <div className="rounded-lg bg-zinc-800/30 p-3 text-center">
                        <p className="text-[10px] text-zinc-500">Data Quality</p>
                        <p className="text-xs font-semibold text-zinc-200">{tech.data_quality?.score || "—"}/100 <span className="text-[10px] text-zinc-600">({tech.data_quality?.grade})</span></p>
                      </div>
                    </div>

                    {/* Feature Importance */}
                    {feats.length > 0 && (
                      <div>
                        <p className="text-[10px] font-medium uppercase text-zinc-500 mb-2">Feature Importance (SHAP)</p>
                        <div className="space-y-1">
                          {feats.slice(0, 10).map((f: any, i: number) => (
                            <div key={i} className="flex items-center gap-2 text-[10px]">
                              <span className="text-zinc-600 w-4">{i + 1}.</span>
                              <span className="text-zinc-300 w-36 truncate">{f.feature}</span>
                              <div className="flex-1 h-1.5 rounded-full bg-zinc-800 overflow-hidden">
                                <div className="h-full rounded-full bg-amber-500" style={{ width: `${Math.min(f.importance * 100, 100)}%` }} />
                              </div>
                              <span className="text-zinc-500 w-10 text-right">{(f.importance * 100).toFixed(1)}%</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            </>
          )}

          {!result && !loading && !error && (
            <p className="text-sm text-zinc-600 text-center py-12">Select a document and run the executive prediction analysis.</p>
          )}
        </div>
      )}
    </div>
  );
}
