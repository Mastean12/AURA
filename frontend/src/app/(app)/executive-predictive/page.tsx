"use client";

import { useState, useEffect } from "react";
import {
  TrendingUp, AlertTriangle, Target, Loader2, DollarSign, Users,
  Brain, Zap, Shield, FileText, BarChart3, GitCompare, Bell,
  ChevronDown, ChevronRight, Activity, Eye, EyeOff, BrainCircuit,
  Layers, Sigma, ScatterChart, Table2, CheckCircle2, XCircle,
} from "lucide-react";
import { listDocuments } from "@/lib/api";
import type { DocumentResponse } from "@/types";

const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function ExecutivePredictivePage() {
  const [docs, setDocs] = useState<DocumentResponse[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<number | null>(null);
  const [fetched, setFetched] = useState(false);
  const [data, setData] = useState<Record<string, any> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showAnalyst, setShowAnalyst] = useState(false);
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    features: false, shap: false, cv: false, residuals: false, models: false,
  });

  useEffect(() => {
    if (!fetched) listDocuments().then(setDocs).finally(() => setFetched(true));
  }, []);

  async function runAnalysis() {
    if (!selectedDoc) return;
    setLoading(true); setError(""); setData(null); setShowAnalyst(false);
    try {
      const token = localStorage.getItem("aura_token");
      const res = await fetch(`${apiBase}/api/v1/predictive-orchestrator/analyze`, {
        method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ doc_id: selectedDoc }),
      });
      if (!res.ok) { const e = await res.json(); setError(e.detail || "Failed"); return; }
      setData(await res.json());
    } catch { setError("Connection failed"); }
    finally { setLoading(false); }
  }

  const ex = data?.executive || {};
  const an = data?.analyst || {};
  const chartRecs = data?.chart_recommendations || [];

  const bi = ex.business_impact || {};
  const kd = ex.key_drivers || [];
  const risks = ex.top_risks || [];
  const opps = ex.top_opportunities || [];
  const actions = ex.recommended_actions || [];
  const fe = ex.financial_exposure || {};
  const dc = ex.decision_confidence || {};
  const se = ex.source_evidence || {};

  const modelInfo = an.model_info || {};
  const metrics = an.metrics || {};
  const feats = an.feature_importance || [];
  const shaps = an.shap_values || [];
  const perms = an.permutation_importance || [];
  const cv = an.cross_validation || {};
  const conf = an.confidence || {};
  const residuals = an.residual_analysis || {};
  const classReport = an.classification_report || {};
  const intervals = an.prediction_intervals || {};
  const allModels = an.automl_details?.all_models || [];
  const cm = metrics.confusion_matrix || [];

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Executive Predictive Dashboard</h1>
          <p className="text-sm text-zinc-500">Strategic intelligence with full analyst transparency</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-zinc-600">
          <Brain className="h-4 w-4 text-blue-400" />
          <span>Executive View</span>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        {docs.map(d => (
          <button key={d.id} onClick={() => setSelectedDoc(d.id)}
            className={`rounded-xl border px-4 py-2 text-sm transition-colors ${selectedDoc === d.id ? "border-blue-600 bg-blue-600/20 text-blue-300" : "border-zinc-800 bg-zinc-900/50 text-zinc-400 hover:border-zinc-700"}`}>
            {d.title.slice(0, 30)}
          </button>
        ))}
      </div>

      {selectedDoc && (
        <div className="space-y-4">
          <div className="flex flex-wrap items-center gap-3">
            <button onClick={runAnalysis} disabled={loading}
              className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 px-6 py-3 text-sm font-medium hover:from-blue-500 hover:to-purple-500 shadow-lg shadow-blue-600/20 disabled:opacity-50">
              {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : <BrainCircuit className="h-5 w-5" />}
              Run Full Predictive Analysis
            </button>
          </div>
          {error && <p className="text-xs text-red-400">{error}</p>}
          {loading && <div className="space-y-4">{[1,2,3,4,5].map(i => <div key={i} className="h-20 animate-pulse rounded-xl bg-zinc-800/50" />)}</div>}

          {data && <>
            {/* ===== EXECUTIVE VIEW ===== */}
            {!showAnalyst && <>
              {/* Executive Summary + KPI Cards */}
              <div className="rounded-xl border border-blue-900/30 bg-gradient-to-br from-blue-950/20 to-zinc-900/50 p-5">
                <div className="flex items-center gap-2 mb-3">
                  <FileText className="h-5 w-5 text-blue-400" />
                  <h2 className="text-sm font-medium uppercase tracking-wider text-blue-400">Executive Prediction Summary</h2>
                  <span className="ml-auto text-[10px] text-zinc-500">{data.problem_type} · {data.target}</span>
                </div>
                <p className="text-sm leading-relaxed text-zinc-200 mb-4">{ex.executive_summary || "Analysis complete."}</p>
                <div className="grid gap-3 sm:grid-cols-5">
                  {[
                    { label: "Financial Exposure", value: bi.financial_exposure || "—", icon: DollarSign, color: "text-amber-400" },
                    { label: "At Risk", value: bi.at_risk_percentage ? `${bi.at_risk_percentage}%` : "—", icon: Users, color: "text-red-400" },
                    { label: "Impact Level", value: bi.impact_level || "—", icon: AlertTriangle, color: bi.impact_level === "Critical" ? "text-red-400" : bi.impact_level === "High" ? "text-amber-400" : "text-blue-400" },
                    { label: "Confidence", value: dc.overall ? `${dc.overall}%` : "—", icon: Brain, color: "text-emerald-400" },
                    { label: "Urgency", value: bi.urgency?.split(" ")[0] || "—", icon: Activity, color: "text-purple-400" },
                  ].map(m => (
                    <div key={m.label} className="rounded-lg bg-zinc-800/30 p-3 text-center">
                      <m.icon className={`mx-auto h-4 w-4 ${m.color} mb-1`} />
                      <p className="text-sm font-bold text-zinc-200">{m.value}</p>
                      <p className="text-[9px] text-zinc-500">{m.label}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Key Drivers */}
              {kd.length > 0 && (
                <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <Target className="h-5 w-5 text-amber-400" />
                    <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Key Drivers</h2>
                  </div>
                  <div className="space-y-2">
                    {kd.map((d: any, i: number) => (
                      <div key={i} className="rounded-lg bg-zinc-800/30 p-3">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs font-semibold text-zinc-200">{d.factor}</span>
                          <span className={`rounded px-1.5 py-0.5 text-[9px] font-medium uppercase ${
                            d.direction === "primary" ? "bg-amber-900/50 text-amber-300"
                              : d.direction === "significant" ? "bg-blue-900/50 text-blue-300"
                                : "bg-zinc-800 text-zinc-400"
                          }`}>{d.direction}</span>
                        </div>
                        <p className="text-[10px] text-zinc-400 leading-relaxed">{d.narrative}</p>
                        <div className="mt-1 h-1.5 rounded-full bg-zinc-800 overflow-hidden">
                          <div className={`h-full rounded-full ${
                            i === 0 ? "bg-amber-500" : i <= 2 ? "bg-blue-500" : "bg-zinc-500"
                          }`} style={{ width: `${Math.min(d.influence_pct, 100)}%` }} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Business Health Forecast */}
              <div className="grid gap-4 lg:grid-cols-2">
                {/* Financial Exposure */}
                <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <DollarSign className="h-5 w-5 text-emerald-400" />
                    <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Financial Exposure</h2>
                  </div>
                  <div className="space-y-2">
                    {[
                      ["Total at Risk", fe.total_at_risk, "text-red-400"],
                      ["Best Case", fe.best_case, "text-emerald-400"],
                      ["Expected Case", fe.expected_case, "text-amber-400"],
                      ["Worst Case", fe.worst_case, "text-red-400"],
                      ["Confidence Range", fe.confidence_range, "text-blue-400"],
                    ].map(([label, val, color]) => (
                      <div key={label as string} className="flex justify-between text-xs">
                        <span className="text-zinc-500">{label as string}</span>
                        <span className={`font-semibold ${color as string}`}>{val as string}</span>
                      </div>
                    ))}
                  </div>
                  {fe.narrative && <p className="mt-2 text-[10px] text-zinc-500 leading-relaxed">{fe.narrative}</p>}
                </div>

                {/* Top Risks */}
                <div className="rounded-xl border border-red-800/30 bg-red-950/20 p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <Shield className="h-5 w-5 text-red-400" />
                    <h2 className="text-sm font-medium uppercase tracking-wider text-red-400">Top Risks</h2>
                  </div>
                  <div className="space-y-2">
                    {risks.slice(0, 5).map((r: any, i: number) => (
                      <div key={i} className="rounded-lg bg-zinc-800/30 p-3">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs font-semibold text-zinc-200">{r.risk}</span>
                          <span className={`rounded px-1.5 py-0.5 text-[9px] font-medium uppercase ${
                            r.severity === "Critical" ? "bg-red-900/50 text-red-300"
                              : r.severity === "High" ? "bg-amber-900/50 text-amber-300"
                                : "bg-blue-900/50 text-blue-300"
                          }`}>{r.severity}</span>
                        </div>
                        <div className="flex gap-3 text-[10px] text-zinc-500">
                          <span>Probability: <span className="text-zinc-300">{r.probability?.toFixed(0)}%</span></span>
                          <span>Impact: <span className="text-amber-300">{r.financial_impact}</span></span>
                        </div>
                        {r.recommended_action && (
                          <p className="text-[9px] text-zinc-600 mt-1">Action: {r.recommended_action}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Top Opportunities + Recommended Actions */}
              <div className="grid gap-4 lg:grid-cols-2">
                {opps.length > 0 && (
                  <div className="rounded-xl border border-emerald-800/30 bg-emerald-950/20 p-5">
                    <div className="flex items-center gap-2 mb-3">
                      <Zap className="h-5 w-5 text-emerald-400" />
                      <h2 className="text-sm font-medium uppercase tracking-wider text-emerald-400">Top Opportunities</h2>
                    </div>
                    <div className="space-y-2">
                      {opps.slice(0, 6).map((o: any, i: number) => (
                        <div key={i} className="rounded-lg bg-zinc-800/30 p-3">
                          <div className="flex items-center justify-between">
                            <span className="text-xs font-semibold text-zinc-200">{o.opportunity}</span>
                            {o.potential_value && o.potential_value !== "TBD" && (
                              <span className="text-[10px] font-semibold text-emerald-300">{o.potential_value}</span>
                            )}
                          </div>
                          {o.description && <p className="text-[9px] text-zinc-500 mt-0.5">{o.description}</p>}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                <div className="rounded-xl border border-purple-800/30 bg-purple-950/20 p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <Target className="h-5 w-5 text-purple-400" />
                    <h2 className="text-sm font-medium uppercase tracking-wider text-purple-400">Recommended Actions</h2>
                  </div>
                  <div className="space-y-2">
                    {actions.slice(0, 6).map((a: any, i: number) => (
                      <div key={i} className="rounded-lg bg-zinc-800/30 p-3">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs font-semibold text-zinc-200">{a.action}</span>
                          <span className={`rounded px-1.5 py-0.5 text-[9px] font-medium uppercase ${
                            a.priority === "High" ? "bg-red-900/50 text-red-300"
                              : a.priority === "Medium" ? "bg-amber-900/50 text-amber-300"
                                : "bg-blue-900/50 text-blue-300"
                          }`}>{a.priority}</span>
                        </div>
                        <div className="flex gap-3 text-[10px] text-zinc-500">
                          {a.expected_roi && <span>ROI: <span className="text-emerald-300">{a.expected_roi}</span></span>}
                          {a.timeline && <span>Timeline: <span className="text-zinc-300">{a.timeline}</span></span>}
                        </div>
                        {a.expected_impact && <p className="text-[9px] text-zinc-600 mt-0.5">{a.expected_impact}</p>}
                      </div>
                    ))}
                    {actions.length === 0 && <p className="text-[10px] text-zinc-500 text-center py-4">No recommendations generated.</p>}
                  </div>
                </div>
              </div>

              {/* Decision Confidence + Source Evidence */}
              <div className="grid gap-4 lg:grid-cols-2">
                <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <Brain className="h-5 w-5 text-blue-400" />
                    <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Decision Confidence</h2>
                  </div>
                  <div className="flex items-center gap-4 mb-3">
                    <div className="relative h-16 w-16">
                      <svg className="h-16 w-16 -rotate-90" viewBox="0 0 36 36">
                        <circle cx="18" cy="18" r="15.5" fill="none" stroke="rgb(39 39 42)" strokeWidth="3" />
                        <circle cx="18" cy="18" r="15.5" fill="none" stroke={dc.overall >= 80 ? "rgb(52 211 153)" : dc.overall >= 60 ? "rgb(251 191 36)" : dc.overall >= 40 ? "rgb(251 146 60)" : "rgb(248 113 113)"}
                          strokeWidth="3" strokeDasharray={`${(dc.overall || 0) / 100 * 97.4} 97.4`} strokeLinecap="round" />
                      </svg>
                      <div className="absolute inset-0 flex items-center justify-center">
                        <span className="text-sm font-bold text-zinc-100">{dc.overall?.toFixed(0) || "—"}</span>
                      </div>
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-zinc-200">{dc.grade || "—"}</p>
                      <p className="text-[10px] text-zinc-500">{dc.grade_description || ""}</p>
                    </div>
                  </div>
                  <div className="space-y-1">
                    {(dc.factors || []).map((f: string, i: number) => (
                      <div key={i} className="flex items-start gap-2 text-[10px]">
                        <CheckCircle2 className="mt-0.5 h-2.5 w-2.5 shrink-0 text-emerald-500" />
                        <span className="text-zinc-400">{f}</span>
                      </div>
                    ))}
                  </div>
                </div>
                <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <FileText className="h-5 w-5 text-zinc-400" />
                    <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Source Evidence</h2>
                  </div>
                  <div className="space-y-2">
                    {[
                      ["Model Performance", se.model_performance],
                      ["Data Quality", se.data_quality],
                      ["Sample Size", se.sample_size?.toLocaleString()],
                      ["Features Analyzed", se.features_analyzed?.toLocaleString()],
                      ["Models Evaluated", se.models_evaluated?.toLocaleString()],
                      ["Overall Confidence", se.overall_confidence],
                    ].filter(([_, v]) => v != null).map(([label, val]) => (
                      <div key={label as string} className="flex justify-between text-[10px]">
                        <span className="text-zinc-500">{label as string}</span>
                        <span className="font-medium text-zinc-300">{val as string}</span>
                      </div>
                    ))}
                  </div>
                  {se.narrative && <p className="mt-2 text-[9px] text-zinc-600 leading-relaxed">{se.narrative}</p>}
                </div>
              </div>
            </>}

            {/* ===== ANALYST VIEW ===== */}
            {showAnalyst && <>
              {/* Model Info + Metrics */}
              <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
                <div className="flex items-center gap-2 mb-3">
                  <Brain className="h-5 w-5 text-violet-400" />
                  <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Model Performance</h2>
                </div>
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
                  <button onClick={() => setExpandedSections(prev => ({ ...prev, models: !prev.models }))}
                    className="flex w-full items-center justify-between text-sm font-medium uppercase tracking-wider text-zinc-500">
                    <div className="flex items-center gap-2">
                      <Layers className="h-5 w-5 text-zinc-400" />
                      <span>All Models Comparison ({allModels.length})</span>
                    </div>
                    {expandedSections.models ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                  </button>
                  {expandedSections.models && (
                    <div className="mt-3 space-y-2">
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
                  )}
                </div>
              )}
            </>}

            {/* === VIEW TOGGLE === */}
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
          </>}

          {!data && !loading && !error && (
            <p className="text-sm text-zinc-600 text-center py-12">Select a document and run the analysis.</p>
          )}
        </div>
      )}
    </div>
  );
}
