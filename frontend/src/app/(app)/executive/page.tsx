"use client";

import { useState, useEffect } from "react";
import {
  Brain, Shield, AlertTriangle, Target, Lightbulb, CheckCircle, Loader2,
  TrendingUp, DollarSign, Users, Clock, Database, Eye, EyeOff,
  BarChart3, Activity, Layers, Sigma, ScatterChart, Table2,
} from "lucide-react";
import { listDocuments } from "@/lib/api";
import type { DocumentResponse } from "@/types";

const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function ExecutivePage() {
  const [docs, setDocs] = useState<DocumentResponse[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<number | null>(null);
  const [data, setData] = useState<Record<string, any> | null>(null);
  const [loading, setLoading] = useState(false);
  const [fetched, setFetched] = useState(false);
  const [showAnalyst, setShowAnalyst] = useState(false);

  useEffect(() => { if (!fetched) listDocuments().then(setDocs).finally(() => setFetched(true)); }, []);

  async function runAnalysis() {
    if (!selectedDoc) return;
    setLoading(true); setData(null); setShowAnalyst(false);
    try {
      const token = localStorage.getItem("aura_token");
      const res = await fetch(`${apiBase}/api/v1/analytics/executive-intelligence-v3`, {
        method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ doc_id: selectedDoc }),
      });
      if (res.ok) setData(await res.json());
    } catch {} finally { setLoading(false); }
  }

  const bh = data?.business_health || {};
  const findings = data?.key_findings || [];
  const rootCauses = data?.root_causes || [];
  const risks = data?.risks || [];
  const opps = data?.opportunities || [];
  const recs = data?.recommendations || [];
  const impact = data?.business_impact || {};
  const charts = data?.charts || [];
  const dq = data?.data_quality || {};
  const confidence = data?.confidence || 0;
  const growthRates = data?.growth_rates || [];
  const regional = data?.regional_breakdown || [];
  const departmentData = data?.department_breakdown || [];
  const marginAnalysis = data?.margin_analysis;

  const an = data?.analyst || {};
  const modelInfo = an.model_info || {};
  const metrics = an.metrics || {};
  const feats = an.feature_importance || [];
  const shaps = an.shap_values || [];
  const perms = an.permutation_importance || [];
  const cv = an.cross_validation || {};
  const residuals = an.residual_analysis || {};
  const classReport = an.classification_report || {};
  const intervals = an.prediction_intervals || {};
  const allModels = an.automl_details?.all_models || [];
  const cm = metrics.confusion_matrix || [];

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Executive Intelligence</h1>
          <p className="text-sm text-zinc-500">AI-powered business consulting and decision support</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-zinc-600">
          <Brain className="h-4 w-4 text-blue-400" />
          <span>{showAnalyst ? "Analyst View" : "Executive View"}</span>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        {docs.map(d => (
          <button key={d.id} onClick={() => { setSelectedDoc(d.id); setData(null); }}
            className={`rounded-xl border px-4 py-2 text-sm transition-colors ${selectedDoc === d.id ? "border-blue-600 bg-blue-600/20 text-blue-300" : "border-zinc-800 bg-zinc-900/50 text-zinc-400 hover:border-zinc-700"}`}>
            {d.title.slice(0, 30)}
          </button>
        ))}
      </div>

      {selectedDoc && (
        <div className="space-y-4">
          {!data && !loading && (
            <button onClick={runAnalysis} className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 px-6 py-3 text-sm font-medium hover:from-blue-500 hover:to-purple-500 shadow-lg shadow-blue-600/20">
              <Brain className="h-5 w-5" />Run Executive Intelligence Analysis
            </button>
          )}
          {loading && <div className="space-y-4">{[1,2,3,4,5].map(i => <div key={i} className="h-24 animate-pulse rounded-xl bg-zinc-800/50" />)}</div>}

          {data && <>
            {!showAnalyst && <>
              {/* Business Health Dashboard */}
              <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-2">
                    <Shield className="h-5 w-5 text-zinc-400" />
                    <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Business Health Dashboard</h2>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`text-xl font-bold ${bh.overall >= 70 ? "text-emerald-400" : bh.overall >= 40 ? "text-amber-400" : "text-red-400"}`}>
                      {bh.overall || "—"}<span className="text-xs text-zinc-600">/100</span>
                    </span>
                    <span className="text-xs text-zinc-500">Confidence: <span className="text-zinc-200 font-semibold">{(confidence * 100).toFixed(0)}%</span></span>
                    <span className="text-xs text-zinc-500">Data Quality: <span className="text-zinc-200 font-semibold">{dq.score || "—"}</span></span>
                  </div>
                </div>
                <div className="grid gap-3 sm:grid-cols-3 lg:grid-cols-6">
                  {[
                    { label: "Revenue Health", value: bh.revenue_health, icon: DollarSign },
                    { label: "Cost Health", value: bh.cost_health, icon: TrendingUp, invert: true },
                    { label: "Growth Health", value: bh.growth_health, icon: TrendingUp },
                    { label: "Risk Health", value: bh.risk_health, icon: Shield, invert: true },
                    { label: "Operations Health", value: bh.operations_health, icon: Clock },
                    { label: "Customer Health", value: bh.customer_health, icon: Users },
                  ].filter(m => m.value).map(m => (
                    <div key={m.label} className="text-center">
                      <m.icon className={`mx-auto h-4 w-4 mb-1 ${m.value >= 70 ? "text-emerald-400" : m.value >= 40 ? "text-amber-400" : "text-red-400"}`} />
                      <p className="text-[10px] uppercase text-zinc-500">{m.label}</p>
                      <p className={`text-lg font-bold ${m.value >= 70 ? "text-emerald-400" : m.value >= 40 ? "text-amber-400" : "text-red-400"}`}>{m.value}</p>
                      <div className="mt-1 h-1 rounded-full bg-zinc-800 overflow-hidden">
                        <div className={`h-full rounded-full ${m.value >= 70 ? "bg-emerald-500" : m.value >= 40 ? "bg-amber-500" : "bg-red-500"}`} style={{ width: `${m.value}%` }} />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Executive Summary */}
              {data.executive_summary && (
                <div className="rounded-xl border border-blue-900/30 bg-blue-950/20 p-5">
                  <div className="flex items-center gap-2 mb-2">
                    <Brain className="h-5 w-5 text-blue-400" />
                    <h2 className="text-sm font-medium uppercase tracking-wider text-blue-400">Executive Summary</h2>
                  </div>
                  <p className="text-sm leading-relaxed text-zinc-200">{data.executive_summary}</p>
                </div>
              )}

              {/* Impact cards */}
              {impact.revenue_impact && (
                <div className="grid gap-4 sm:grid-cols-2">
                  {[{ label: "Revenue Impact", value: impact.revenue_impact, icon: DollarSign, color: "text-emerald-400" },
                    { label: "Cost Impact", value: impact.cost_impact, icon: TrendingUp, color: "text-red-400" },
                    { label: "Operational Impact", value: impact.operational_impact, icon: Clock, color: "text-blue-400" },
                    { label: "Customer Impact", value: impact.customer_impact, icon: Users, color: "text-purple-400" },
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

              {/* Growth Rates + Regional + Department Breakdown */}
              {(growthRates.length > 0 || regional.length > 0 || departmentData.length > 0) && (
                <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
                  <h2 className="text-xs font-medium uppercase tracking-wider text-zinc-500 mb-3">Growth & Performance Breakdown</h2>
                  <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                    {growthRates.map((g: any, i: number) => (
                      <div key={i} className="rounded-lg bg-zinc-800/30 p-3">
                        <p className="text-[10px] text-zinc-500">{g.metric}</p>
                        <p className={`text-lg font-bold mt-0.5 ${g.change_pct >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                          {g.change_pct >= 0 ? "+" : ""}{g.change_pct}%
                        </p>
                        <p className="text-[10px] text-zinc-500">{g.directional_word} from {g.earlier_avg} to {g.recent_avg}</p>
                      </div>
                    ))}
                    {regional.map((r: any, i: number) => (
                      <div key={`reg-${i}`} className="rounded-lg bg-blue-950/30 border border-blue-800/30 p-3">
                        <p className="text-[10px] text-blue-400">{r.segment}</p>
                        <p className="text-sm font-bold text-zinc-200 mt-0.5">{r.contribution_pct}%</p>
                        <p className="text-[10px] text-zinc-500">of {r.kpi}</p>
                      </div>
                    ))}
                    {departmentData.map((d: any, i: number) => (
                      <div key={`dept-${i}`} className="rounded-lg bg-amber-950/30 border border-amber-800/30 p-3">
                        <p className="text-[10px] text-amber-400">{d.kpi} by Department</p>
                        <p className="text-xs text-zinc-300 mt-1">Best: <span className="text-emerald-400 font-medium">{d.best_department}</span> ({d.best_value})</p>
                        <p className="text-xs text-zinc-300">Worst: <span className="text-red-400 font-medium">{d.worst_department}</span> ({d.worst_value})</p>
                        <p className="text-[10px] text-zinc-500 mt-0.5">{d.gap_pct}% gap</p>
                      </div>
                    ))}
                  </div>
                  {marginAnalysis && (
                    <div className="mt-3 rounded-lg bg-red-950/30 border border-red-800/30 p-3">
                      <p className="text-xs font-medium text-red-400">⚠ Margin Alert</p>
                      <p className="text-xs text-zinc-300 mt-1">{marginAnalysis.insight}</p>
                      <p className="text-[10px] text-zinc-500 mt-1">Recommendation: {marginAnalysis.recommendation}</p>
                    </div>
                  )}
                </div>
              )}

              {/* Key Findings */}
              {findings.length > 0 && (
                <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <Lightbulb className="h-5 w-5 text-emerald-400" />
                    <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Executive Findings</h2>
                  </div>
                  <div className="grid gap-3 sm:grid-cols-2">
                    {findings.map((f: any, i: number) => (
                      <div key={i} className="rounded-lg bg-zinc-800/30 p-3">
                        <div className="flex items-start gap-2">
                          <span className={`mt-1 h-2 w-2 shrink-0 rounded-full ${f.impact === "high" ? "bg-red-500" : f.impact === "medium" ? "bg-amber-500" : "bg-blue-500"}`} />
                          <div>
                            <p className="text-xs font-semibold text-zinc-200">{f.title}</p>
                            {f.detail && <p className="text-[11px] text-zinc-400 mt-0.5">{f.detail}</p>}
                            {f.confidence && <p className="text-[10px] text-zinc-600 mt-0.5">{(f.confidence * 100).toFixed(0)}% confidence</p>}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Root Causes */}
              {rootCauses.length > 0 && (
                <div className="rounded-xl border border-amber-800/30 bg-amber-950/20 p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <AlertTriangle className="h-5 w-5 text-amber-400" />
                    <h2 className="text-sm font-medium uppercase tracking-wider text-amber-400">Root Cause Analysis</h2>
                  </div>
                  <div className="grid gap-3 sm:grid-cols-2">
                    {rootCauses.map((rc: any, i: number) => (
                      <div key={i} className="rounded-lg bg-zinc-800/30 p-3">
                        <div className="flex items-center gap-1.5 mb-1">
                          <span className="text-[10px] font-medium uppercase text-zinc-500">{rc.impact_area || "Business"}</span>
                        </div>
                        <p className="text-xs font-medium text-zinc-200">{rc.cause}</p>
                        {rc.evidence && <p className="text-[11px] text-zinc-400 mt-0.5">Evidence: {rc.evidence}</p>}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Risk + Opportunity grid */}
              <div className="grid gap-4 lg:grid-cols-2">
                {risks.length > 0 && (
                  <div className="rounded-xl border border-red-800/30 bg-red-950/20 p-5">
                    <div className="flex items-center gap-2 mb-3">
                      <AlertTriangle className="h-5 w-5 text-red-400" />
                      <h2 className="text-sm font-medium uppercase tracking-wider text-red-400">Business Risks</h2>
                    </div>
                    <div className="space-y-2">
                      {risks.map((r: any, i: number) => (
                        <div key={i} className="rounded-lg bg-zinc-800/30 p-3">
                          <div className="flex items-center justify-between mb-1">
                            <p className="text-xs font-semibold text-zinc-200">{r.name}</p>
                            <span className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${r.severity === "Critical" || r.severity === "High" ? "bg-red-900/50 text-red-300" : r.severity === "Medium" ? "bg-amber-900/50 text-amber-300" : "bg-blue-900/50 text-blue-300"}`}>{r.severity}</span>
                          </div>
                          <p className="text-[11px] text-zinc-400">{r.description}</p>
                          {r.financial_exposure && <p className="text-[10px] text-amber-400 mt-0.5">Exposure: {r.financial_exposure}</p>}
                          {r.mitigation && <p className="text-[10px] text-zinc-500 mt-0.5">Mitigation: {r.mitigation}</p>}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {opps.length > 0 && (
                  <div className="rounded-xl border border-emerald-800/30 bg-emerald-950/20 p-5">
                    <div className="flex items-center gap-2 mb-3">
                      <Target className="h-5 w-5 text-emerald-400" />
                      <h2 className="text-sm font-medium uppercase tracking-wider text-emerald-400">Growth Opportunities</h2>
                    </div>
                    <div className="space-y-2">
                      {opps.map((o: any, i: number) => (
                        <div key={i} className="rounded-lg bg-zinc-800/30 p-3">
                          <div className="flex items-center justify-between mb-1">
                            <p className="text-xs font-semibold text-zinc-200">{o.name}</p>
                            <span className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${o.impact === "high" ? "bg-emerald-900/50 text-emerald-300" : "bg-amber-900/50 text-amber-300"}`}>{o.impact}</span>
                          </div>
                          <p className="text-[11px] text-zinc-400">{o.description}</p>
                          {o.estimated_value && <p className="text-[10px] text-emerald-400 mt-0.5">Value: {o.estimated_value}</p>}
                          {o.action && <p className="text-[10px] text-zinc-500 mt-0.5">Action: {o.action}</p>}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Recommendations */}
              {recs.length > 0 && (
                <div className="rounded-xl border border-purple-800/30 bg-purple-950/20 p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <CheckCircle className="h-5 w-5 text-purple-400" />
                    <h2 className="text-sm font-medium uppercase tracking-wider text-purple-400">Recommended Actions</h2>
                  </div>
                  <div className="space-y-2">
                    {recs.map((r: any, i: number) => (
                      <div key={i} className="flex items-start gap-3 rounded-lg bg-zinc-800/30 p-3">
                        <span className={`mt-0.5 h-2 w-2 shrink-0 rounded-full ${r.priority === "Critical" || r.priority === "High" ? "bg-red-500" : r.priority === "Medium" ? "bg-amber-500" : "bg-blue-500"}`} />
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-2">
                            <p className="text-xs font-semibold text-zinc-200">{r.title}</p>
                            <span className={`rounded px-1.5 py-0.5 text-[9px] font-medium uppercase ${r.priority === "Critical" || r.priority === "High" ? "bg-red-900/50 text-red-300" : r.priority === "Medium" ? "bg-amber-900/50 text-amber-300" : "bg-blue-900/50 text-blue-300"}`}>{r.priority}</span>
                          </div>
                          {r.description && <p className="text-[11px] text-zinc-400 mt-0.5">{r.description}</p>}
                          <div className="flex gap-3 mt-0.5 text-[10px] text-zinc-500">
                            {r.expected_outcome && <span>Outcome: {r.expected_outcome}</span>}
                            {r.roi && <span>ROI: {r.roi}</span>}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Charts */}
              {charts.length > 0 && (
                <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
                  <h2 className="text-xs font-medium uppercase tracking-wider text-zinc-500 mb-3">Key Visualizations</h2>
                  <div className="grid gap-4 sm:grid-cols-2">
                    {charts.map((ch: any, i: number) => (
                      <div key={i} className="rounded-lg bg-zinc-800/30 p-2">
                        <p className="text-[10px] text-zinc-500 mb-1">{ch.column} ({ch.chart_type})</p>
                        <iframe srcDoc={ch.html} className="w-full h-56 rounded-lg border-0" title={ch.column} />
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>}

            {/* ===== ANALYST VIEW ===== */}
            {showAnalyst && <>
              {/* Model Info + Metrics */}
              {(modelInfo.selected_model || Object.keys(metrics).length > 0) && (
                <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <Database className="h-5 w-5 text-violet-400" />
                    <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Model Performance</h2>
                  </div>
                  {modelInfo.selected_model && (
                    <div className="grid gap-3 sm:grid-cols-4 mb-4">
                      {[
                        ["Model", modelInfo.selected_model],
                        ["Problem Type", modelInfo.problem_type],
                        ["Target", modelInfo.target],
                        ["Features", modelInfo.features],
                        ["Samples", modelInfo.samples],
                        ["Models Tested", modelInfo.models_tested],
                        ["Best Metric", modelInfo.best_metric?.toFixed(4)],
                      ].filter(([_, v]) => v != null && v !== "").map(([label, val]) => (
                        <div key={label as string} className="rounded-lg bg-zinc-800/30 p-3 text-center">
                          <p className="text-[9px] text-zinc-500 uppercase">{label as string}</p>
                          <p className="text-xs font-semibold text-zinc-200">{val as string}</p>
                        </div>
                      ))}
                    </div>
                  )}
                  <div className="grid gap-3 sm:grid-cols-4">
                    {Object.entries(metrics).filter(([k, v]) => k !== "confusion_matrix" && v != null && v !== "").map(([key, val]) => (
                      <div key={key} className="rounded-lg bg-zinc-800/30 p-3 text-center">
                        <p className="text-[9px] text-zinc-500 uppercase">{key}</p>
                        <p className="text-xs font-semibold text-zinc-200">
                          {key === "mape" ? `${Number(val).toFixed(2)}%` : Number(val).toFixed(4)}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Confusion Matrix */}
              {cm.length > 0 && (
                <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <Table2 className="h-5 w-5 text-cyan-400" />
                    <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Confusion Matrix</h2>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-[10px]">
                      <thead>
                        <tr className="text-zinc-500">
                          <th className="p-1"></th>
                          {cm[0]?.map((_: any, j: number) => <th key={j} className="p-1 text-center">Pred {j}</th>)}
                        </tr>
                      </thead>
                      <tbody>
                        {cm.map((row: number[], i: number) => (
                          <tr key={i}>
                            <td className="p-1 text-zinc-500 font-medium">True {i}</td>
                            {row.map((val: number, j: number) => (
                              <td key={j} className={`p-1 text-center font-medium ${i === j ? "text-emerald-400 bg-emerald-900/20" : "text-red-400 bg-red-900/10"} rounded`}>
                                {val}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Feature Importance + SHAP + Permutation */}
              <div className="grid gap-4 lg:grid-cols-3">
                {feats.length > 0 && (
                  <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
                    <div className="flex items-center gap-2 mb-3">
                      <BarChart3 className="h-5 w-5 text-amber-400" />
                      <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Feature Importance</h2>
                    </div>
                    <div className="space-y-1">
                      {feats.slice(0, 10).map((f: any, i: number) => (
                        <div key={i} className="flex items-center gap-2 text-[10px]">
                          <span className="text-zinc-600 w-3">{i + 1}</span>
                          <span className="text-zinc-300 w-28 truncate">{f.feature}</span>
                          <div className="flex-1 h-1.5 rounded-full bg-zinc-800 overflow-hidden">
                            <div className="h-full rounded-full bg-amber-500" style={{ width: `${Math.min(f.importance * 100 || f.shap_value * 100 || 5, 100)}%` }} />
                          </div>
                          <span className="text-zinc-500 w-10 text-right">{f.importance?.toFixed(3)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {shaps.length > 0 && (
                  <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
                    <div className="flex items-center gap-2 mb-3">
                      <ScatterChart className="h-5 w-5 text-violet-400" />
                      <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">SHAP Values</h2>
                    </div>
                    <div className="space-y-1">
                      {shaps.slice(0, 10).map((s: any, i: number) => (
                        <div key={i} className="flex items-center gap-2 text-[10px]">
                          <span className="text-zinc-600 w-3">{i + 1}</span>
                          <span className="text-zinc-300 w-28 truncate">{s.feature}</span>
                          <div className="flex-1 h-1.5 rounded-full bg-zinc-800 overflow-hidden">
                            <div className="h-full rounded-full bg-violet-500" style={{ width: `${Math.min(s.shap_value * 50, 100)}%` }} />
                          </div>
                          <span className="text-zinc-500 w-10 text-right">{s.shap_value?.toFixed(3)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {perms.length > 0 && (
                  <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
                    <div className="flex items-center gap-2 mb-3">
                      <Activity className="h-5 w-5 text-blue-400" />
                      <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Permutation Importance</h2>
                    </div>
                    <div className="space-y-1">
                      {perms.slice(0, 10).map((p: any, i: number) => (
                        <div key={i} className="flex items-center gap-2 text-[10px]">
                          <span className="text-zinc-600 w-3">{i + 1}</span>
                          <span className="text-zinc-300 w-28 truncate">{p.feature}</span>
                          <div className="flex-1 h-1.5 rounded-full bg-zinc-800 overflow-hidden">
                            <div className="h-full rounded-full bg-blue-500" style={{ width: `${Math.min(Math.abs(p.importance * 50), 100)}%` }} />
                          </div>
                          <span className="text-zinc-500 w-10 text-right">{p.importance?.toFixed(3)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Cross-validation + Prediction Intervals + Residuals */}
              <div className="grid gap-4 lg:grid-cols-3">
                {cv.cv_mean != null && (
                  <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
                    <div className="flex items-center gap-2 mb-3">
                      <Layers className="h-5 w-5 text-cyan-400" />
                      <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Cross-Validation</h2>
                    </div>
                    <div className="space-y-1">
                      {[
                        ["Mean", cv.cv_mean?.toFixed(4)],
                        ["Std", cv.cv_std?.toFixed(4)],
                        ["Min", cv.cv_min?.toFixed(4)],
                        ["Max", cv.cv_max?.toFixed(4)],
                        ["Folds", cv.cv_folds],
                      ].filter(([_, v]) => v != null).map(([label, val]) => (
                        <div key={label as string} className="flex justify-between text-[10px]">
                          <span className="text-zinc-500">{label as string}</span>
                          <span className="font-medium text-zinc-300">{val as string}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                {intervals.method != null && !intervals.error && (
                  <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
                    <div className="flex items-center gap-2 mb-3">
                      <Activity className="h-5 w-5 text-orange-400" />
                      <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Prediction Intervals</h2>
                    </div>
                    <div className="space-y-1">
                      {[
                        ["Method", intervals.method],
                        ["Confidence Level", `${(intervals.confidence_level * 100).toFixed(0)}%`],
                        ["Width", intervals.interval_width?.toFixed(4)],
                      ].filter(([_, v]) => v != null).map(([label, val]) => (
                        <div key={label as string} className="flex justify-between text-[10px]">
                          <span className="text-zinc-500">{label as string}</span>
                          <span className="font-medium text-zinc-300">{val as string}</span>
                        </div>
                      ))}
                    </div>
                    {intervals.lower_bound && (
                      <div className="mt-2">
                        <p className="text-[9px] text-zinc-600 mb-1">Sample bounds (first 5):</p>
                        <div className="space-y-0.5 text-[9px] text-zinc-500">
                          {intervals.lower_bound.map((l: number, i: number) => (
                            <div key={i} className="flex gap-2">
                              <span className="text-red-400">{l.toFixed(2)}</span>
                              <span className="text-zinc-600">—</span>
                              <span className="text-emerald-400">{intervals.upper_bound?.[i]?.toFixed(2)}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
                {residuals.mean != null && (
                  <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
                    <div className="flex items-center gap-2 mb-3">
                      <Sigma className="h-5 w-5 text-pink-400" />
                      <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Residual Analysis</h2>
                    </div>
                    <div className="space-y-1">
                      {[
                        ["Mean", residuals.mean?.toFixed(4)],
                        ["Std Dev", residuals.std?.toFixed(4)],
                        ["Min", residuals.min?.toFixed(4)],
                        ["Max", residuals.max?.toFixed(4)],
                        ["Normality (p)", residuals.normality_p_value?.toFixed(4)],
                      ].filter(([_, v]) => v != null).map(([label, val]) => (
                        <div key={label as string} className="flex justify-between text-[10px]">
                          <span className="text-zinc-500">{label as string}</span>
                          <span className={`font-medium ${label === "Normality (p)" && Number(val) < 0.05 ? "text-red-400" : "text-zinc-300"}`}>{val as string}</span>
                        </div>
                      ))}
                    </div>
                    {residuals.normality_p_value != null && (
                      <p className="mt-2 text-[9px] text-zinc-600">
                        {residuals.normality_p_value >= 0.05
                          ? "Residuals appear normally distributed (p ≥ 0.05), supporting model assumptions."
                          : "Residuals deviate from normality (p < 0.05). Consider non-linear transformations."}
                      </p>
                    )}
                  </div>
                )}
              </div>

              {/* Classification Report */}
              {Object.keys(classReport).length > 0 && (
                <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <Table2 className="h-5 w-5 text-teal-400" />
                    <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Classification Report</h2>
                  </div>
                  <div className="overflow-x-auto">
                    <table className="w-full text-[10px]">
                      <thead>
                        <tr className="text-zinc-500">
                          <th className="p-1 text-left">Class</th>
                          <th className="p-1 text-right">Precision</th>
                          <th className="p-1 text-right">Recall</th>
                          <th className="p-1 text-right">F1</th>
                          <th className="p-1 text-right">Support</th>
                        </tr>
                      </thead>
                      <tbody>
                        {Object.entries(classReport).map(([cls, m]: [string, any]) => (
                          <tr key={cls} className="border-t border-zinc-800">
                            <td className="p-1 font-medium text-zinc-300">{cls}</td>
                            <td className="p-1 text-right text-zinc-400">{m.precision?.toFixed(3)}</td>
                            <td className="p-1 text-right text-zinc-400">{m.recall?.toFixed(3)}</td>
                            <td className="p-1 text-right text-zinc-400">{m["f1-score"]?.toFixed(3)}</td>
                            <td className="p-1 text-right text-zinc-400">{m.support}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* All Models Comparison */}
              {allModels.length > 0 && (
                <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
                  <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500 mb-3">All Models Comparison ({allModels.length})</h2>
                  <div className="space-y-2">
                    {allModels.map((m: any, i: number) => (
                      <div key={i} className="rounded-lg bg-zinc-800/30 p-3">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs font-semibold text-zinc-200">{m.name}</span>
                          {m.error && <span className="text-[9px] text-red-400">{m.error}</span>}
                        </div>
                        <div className="flex flex-wrap gap-x-4 gap-y-1 text-[10px]">
                          {Object.entries(m.metrics || {}).map(([k, v]) => (
                            <span key={k} className="text-zinc-500">
                              {k}: <span className="text-zinc-300">{typeof v === "number" ? v.toFixed(4) : v}</span>
                            </span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>}

            {/* === VIEW TOGGLE === */}
            {(modelInfo.selected_model || feats.length > 0) && (
              <div className="flex items-center justify-center">
                <button onClick={() => setShowAnalyst(!showAnalyst)}
                  className="flex items-center gap-2 rounded-xl border border-zinc-700 bg-zinc-800/50 px-5 py-2.5 text-xs font-medium text-zinc-400 hover:border-zinc-600 hover:text-zinc-200 transition-colors">
                  {showAnalyst ? <Eye className="h-4 w-4" /> : <EyeOff className="h-4 w-4" />}
                  {showAnalyst ? "Switch to Executive View" : "Show Analyst View (Technical Details)"}
                  <span className="ml-1 rounded bg-zinc-700 px-1.5 py-0.5 text-[9px] text-zinc-500">
                    {showAnalyst ? "Executive" : "Analyst"}
                  </span>
                </button>
              </div>
            )}
          </>}
        </div>
      )}
    </div>
  );
}
