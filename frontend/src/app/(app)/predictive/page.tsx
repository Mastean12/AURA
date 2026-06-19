"use client";

import { useState, useEffect } from "react";
import {
  TrendingUp, AlertTriangle, Shield, Lightbulb, Brain, Target,
  Loader2, DollarSign, Users, Clock, ChevronDown, ChevronRight,
  FileText, BarChart3, Building2, GitCompare, Bell, Zap,
} from "lucide-react";
import { listDocuments } from "@/lib/api";
import type { DocumentResponse } from "@/types";

const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function PredictivePage() {
  const [docs, setDocs] = useState<DocumentResponse[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<number | null>(null);
  const [fetched, setFetched] = useState(false);
  const [data, setData] = useState<Record<string, any> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showTech, setShowTech] = useState(false);

  useEffect(() => {
    if (!fetched) listDocuments().then(setDocs).finally(() => setFetched(true));
  }, []);

  async function runAnalysis() {
    if (!selectedDoc) return;
    setLoading(true); setError("");
    try {
      const token = localStorage.getItem("aura_token");
      const res = await fetch(`${apiBase}/api/v1/predictive/analysis`, {
        method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ doc_id: selectedDoc }),
      });
      if (!res.ok) { const err = await res.json(); setError(err.detail || "Failed"); return; }
      setData(await res.json());
    } catch { setError("Connection failed"); }
    finally { setLoading(false); }
  }

  const bi = data?.business_impact || {};
  const scenarios = data?.scenarios || {};
  const segs = data?.segment_analysis || [];
  const sims = data?.what_if_simulations || [];
  const warns = data?.early_warnings || [];
  const presc = data?.prescriptive_recommendations || [];
  const industry = data?.industry_intelligence || {};
  const timeline = data?.forecast_timeline || {};
  const tfc = timeline?.forecasts || {};
  const drivers = data?.prediction_explanation?.drivers || [];
  const tech = data?.technical || {};
  const feats = tech?.feature_importance || [];

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Executive Predictive Intelligence</h1>
          <p className="text-sm text-zinc-500">Full-spectrum business prediction, simulation, and decision support</p>
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
          {!data && !loading && (
            <button onClick={runAnalysis} className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 px-6 py-3 text-sm font-medium hover:from-blue-500 hover:to-purple-500 shadow-lg shadow-blue-600/20">
              <Brain className="h-5 w-5" />Run Full Executive Analysis
            </button>
          )}
          {loading && <div className="space-y-4">{[1,2,3,4,5].map(i => <div key={i} className="h-20 animate-pulse rounded-xl bg-zinc-800/50" />)}</div>}
          {error && <p className="text-xs text-red-400">{error}</p>}

          {data && <>
            {/* Executive Summary + Business Impact */}
            <div className="rounded-xl border border-blue-900/30 bg-gradient-to-br from-blue-950/20 to-zinc-900/50 p-5">
              <div className="flex items-center gap-2 mb-3">
                <FileText className="h-5 w-5 text-blue-400" />
                <h2 className="text-sm font-medium uppercase tracking-wider text-blue-400">Executive Prediction Summary</h2>
                <span className="ml-auto text-xs text-zinc-500">{industry.detected_industry ? `${industry.detected_industry}` : ""}</span>
              </div>
              <p className="text-sm leading-relaxed text-zinc-200 mb-3">{data?.executive_summary || data?.prediction_explanation?.summary || "Analysis complete."}</p>
              <div className="grid gap-3 sm:grid-cols-5">
                {[
                  { label: "At Risk", value: bi.population_at_risk?.toLocaleString(), unit: `of ${bi.total_population?.toLocaleString()}`, icon: Users, color: "text-red-400" },
                  { label: "Revenue at Risk", value: bi.revenue_at_risk_formatted, icon: DollarSign, color: "text-amber-400" },
                  { label: "Impact", value: bi.impact_level, icon: AlertTriangle, color: bi.impact_level === "Critical" ? "text-red-400" : "text-amber-400" },
                  { label: "Confidence", value: `${bi.confidence}%`, icon: Brain, color: "text-blue-400" },
                  { label: "Urgency", value: bi.urgency?.split(" ")[0], unit: bi.urgency?.split(" ").slice(1).join(" "), icon: Clock, color: "text-purple-400" },
                ].map(m => (
                  <div key={m.label} className="rounded-lg bg-zinc-800/30 p-3 text-center">
                    <m.icon className={`mx-auto h-4 w-4 ${m.color} mb-1`} />
                    <p className="text-sm font-bold text-zinc-200">{m.value}</p>
                    <p className="text-[9px] text-zinc-500">{m.label}</p>
                    {m.unit && <p className="text-[8px] text-zinc-600">{m.unit}</p>}
                  </div>
                ))}
              </div>
            </div>

            {/* Prediction Explanation + Drivers */}
            {drivers.length > 0 && (
              <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
                <div className="flex items-center gap-2 mb-3">
                  <Target className="h-5 w-5 text-amber-400" />
                  <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Why This Is Happening</h2>
                </div>
                <div className="space-y-1.5">
                  {drivers.map((d: any, i: number) => (
                    <div key={i} className="flex items-center gap-2">
                      <span className="text-[10px] text-zinc-600 w-5">{i + 1}.</span>
                      <span className="text-xs text-zinc-200 w-40 truncate">{toTitle(d.feature)}</span>
                      <div className="flex-1 h-1.5 rounded-full bg-zinc-800 overflow-hidden">
                        <div className="h-full rounded-full bg-amber-500" style={{ width: `${Math.min(d.pct || d.importance * 100, 100)}%` }} />
                      </div>
                      <span className="text-[10px] text-zinc-500 w-12 text-right">{d.pct ? `${d.pct}%` : `${(d.importance * 100).toFixed(1)}%`}</span>
                    </div>
                  ))}
                </div>
                <p className="mt-2 text-xs text-zinc-500 leading-relaxed">{data?.prediction_explanation?.summary}</p>
              </div>
            )}

            {/* Forecast Timeline */}
            {Object.keys(tfc).length > 0 && (
              <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
                <div className="flex items-center gap-2 mb-3">
                  <TrendingUp className="h-5 w-5 text-violet-400" />
                  <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Forecast Timeline</h2>
                  {timeline.annual_growth_pct != null && (
                    <span className={`ml-auto text-xs font-semibold ${timeline.annual_growth_pct >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                      {timeline.annual_growth_pct >= 0 ? "+" : ""}{timeline.annual_growth_pct}% annual
                    </span>
                  )}
                </div>
                <div className="grid gap-3 sm:grid-cols-4">
                  {[
                    ["30 Days", tfc.forecast_30_days],
                    ["90 Days", tfc.forecast_90_days],
                    ["180 Days", tfc.forecast_180_days],
                    ["365 Days", tfc.forecast_365_days],
                  ].filter(([_, f]) => f).map(([label, f]: any) => {
                    const lastVal = f.forecast?.[f.forecast.length - 1] || 0;
                    const firstVal = f.forecast?.[0] || 1;
                    const change = ((lastVal - firstVal) / firstVal) * 100;
                    return (
                      <div key={label} className="rounded-lg bg-zinc-800/30 p-3 text-center">
                        <p className="text-[10px] text-zinc-500">{label}</p>
                        <p className="text-sm font-bold text-zinc-200">{lastVal.toFixed(1)}</p>
                        <p className={`text-[10px] font-medium ${change >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                          {change >= 0 ? "+" : ""}{change.toFixed(1)}%
                        </p>
                        <div className="mt-1 h-1 rounded-full bg-zinc-800 overflow-hidden">
                          <div className={`h-full rounded-full ${f.direction === "up" ? "bg-emerald-500" : "bg-red-500"}`} style={{ width: `${Math.min(Math.abs(change), 100)}%` }} />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Segments + What-If Grid */}
            <div className="grid gap-4 lg:grid-cols-2">
              {segs.length > 0 && (
                <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <Users className="h-5 w-5 text-cyan-400" />
                    <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Segment Risk Scores</h2>
                  </div>
                  <div className="space-y-1.5">
                    {segs.map((s: any, i: number) => (
                      <div key={i} className="flex items-center gap-2 text-xs">
                        <span className="text-zinc-500 w-32 truncate">{s.segment}</span>
                        <div className="flex-1 h-1.5 rounded-full bg-zinc-800 overflow-hidden">
                          <div className={`h-full rounded-full ${s.risk_score >= 70 ? "bg-red-500" : s.risk_score >= 40 ? "bg-amber-500" : "bg-blue-500"}`}
                            style={{ width: `${Math.min(s.risk_score, 100)}%` }} />
                        </div>
                        <span className="text-zinc-400 w-8 text-right">{s.risk_score}%</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {sims.length > 0 && (
                <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <GitCompare className="h-5 w-5 text-orange-400" />
                    <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">What-If Simulations</h2>
                  </div>
                  <div className="space-y-2">
                    {sims.map((s: any, i: number) => (
                      <div key={i} className="rounded-lg bg-zinc-800/30 p-3">
                        <p className="text-xs font-semibold text-zinc-200">{s.scenario}</p>
                        <div className="flex items-center gap-4 mt-1 text-[10px] text-zinc-500">
                          <span>Before: <span className="text-zinc-300">{s.current_value}%</span></span>
                          <ArrowRight className="h-3 w-3 text-zinc-600" />
                          <span>After: <span className={s.change_pct < 0 ? "text-emerald-400" : "text-amber-400"}>{s.simulated_value}%</span></span>
                          <span className={s.change_pct < 0 ? "text-emerald-400" : "text-red-400"}>({s.change_pct > 0 ? "+" : ""}{s.change_pct}%)</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Early Warnings */}
            {warns.length > 0 && (
              <div className="rounded-xl border border-red-800/30 bg-red-950/20 p-5">
                <div className="flex items-center gap-2 mb-3">
                  <Bell className="h-5 w-5 text-red-400" />
                  <h2 className="text-sm font-medium uppercase tracking-wider text-red-400">Early Warning System</h2>
                </div>
                <div className="space-y-2">
                  {warns.map((w: any, i: number) => (
                    <div key={i} className="flex items-start gap-3 rounded-lg bg-zinc-800/30 p-3">
                      <span className={`mt-1 h-2 w-2 shrink-0 rounded-full ${w.severity === "critical" ? "bg-red-500" : w.severity === "high" ? "bg-amber-500" : "bg-blue-500"}`} />
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="text-xs font-semibold text-zinc-200">{w.alert}</p>
                          <span className={`rounded px-1.5 py-0.5 text-[9px] font-medium uppercase ${w.severity === "critical" ? "bg-red-900/50 text-red-300" : w.severity === "high" ? "bg-amber-900/50 text-amber-300" : "bg-blue-900/50 text-blue-300"}`}>{w.severity}</span>
                        </div>
                        <p className="text-[10px] text-zinc-400 mt-0.5">{w.impact}</p>
                        <p className="text-[10px] text-zinc-600 mt-0.5">Action: {w.recommended_action}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Prescriptive Recommendations + Opportunities */}
            <div className="grid gap-4 lg:grid-cols-2">
              {presc.length > 0 && (
                <div className="rounded-xl border border-purple-800/30 bg-purple-950/20 p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <Zap className="h-5 w-5 text-purple-400" />
                    <h2 className="text-sm font-medium uppercase tracking-wider text-purple-400">Prescriptive Recommendations</h2>
                  </div>
                  <div className="space-y-2">
                    {presc.map((r: any, i: number) => (
                      <div key={i} className="rounded-lg bg-zinc-800/30 p-3">
                        <div className="flex items-start justify-between gap-2">
                          <div className="min-w-0">
                            <p className="text-xs font-semibold text-zinc-200">{r.recommendation}</p>
                            <div className="flex flex-wrap gap-2 mt-1 text-[10px] text-zinc-500">
                              <span>Impact: <span className="text-emerald-400">{r.expected_impact}</span></span>
                              <span>Revenue: <span className="text-amber-400">{r.revenue_preserved}</span></span>
                              <span>ROI: <span className="text-blue-400">{r.roi}</span></span>
                            </div>
                          </div>
                          <span className="shrink-0 rounded bg-purple-900/50 px-1.5 py-0.5 text-[9px] text-purple-300">{r.priority_score?.toFixed(0)}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {(data?.opportunities || []).length > 0 && (
                <div className="rounded-xl border border-emerald-800/30 bg-emerald-950/20 p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <Lightbulb className="h-5 w-5 text-emerald-400" />
                    <h2 className="text-sm font-medium uppercase tracking-wider text-emerald-400">Opportunities</h2>
                  </div>
                  <div className="space-y-2">
                    {(data?.opportunities || []).map((o: any, i: number) => (
                      <div key={i} className="rounded-lg bg-zinc-800/30 p-3">
                        <p className="text-xs font-semibold text-zinc-200">{o.title}</p>
                        <p className="text-[10px] text-zinc-400 mt-0.5">{o.description}</p>
                        <p className="text-[10px] text-emerald-400 mt-0.5">{o.revenue_impact}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Industry KPIs + Scenario Analysis */}
            <div className="grid gap-4 lg:grid-cols-2">
              {industry.industry_kpis && (
                <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <Building2 className="h-5 w-5 text-zinc-400" />
                    <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Industry KPIs — {industry.detected_industry}</h2>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    {industry.industry_kpis.map((kpi: string, i: number) => (
                      <div key={i} className="rounded-lg bg-zinc-800/30 px-3 py-2 text-[10px] text-zinc-300">{kpi}</div>
                    ))}
                  </div>
                </div>
              )}
              {scenarios.expected_case != null && (
                <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <TrendingUp className="h-5 w-5 text-violet-400" />
                    <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Scenario Analysis</h2>
                  </div>
                  <div className="grid grid-cols-3 gap-2">
                    {[
                      { label: "Best Case", value: scenarios.best_case, color: "text-emerald-400", bar: "bg-emerald-500" },
                      { label: "Expected", value: scenarios.expected_case, color: "text-amber-400", bar: "bg-amber-500" },
                      { label: "Worst Case", value: scenarios.worst_case, color: "text-red-400", bar: "bg-red-500" },
                    ].map(s => (
                      <div key={s.label} className="rounded-lg bg-zinc-800/30 p-3 text-center">
                        <p className="text-[10px] text-zinc-500">{s.label}</p>
                        <p className={`text-sm font-bold ${s.color}`}>${s.value?.toLocaleString()}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Advanced Analytics (collapsible) */}
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/30">
              <button onClick={() => setShowTech(!showTech)} className="flex w-full items-center justify-between px-5 py-3 text-xs font-medium text-zinc-500 hover:text-zinc-300">
                <span>Advanced Analytics (for analysts)</span>
                {showTech ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
              </button>
              {showTech && <div className="border-t border-zinc-800 p-5 space-y-4">
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
                </div>
                {feats.length > 0 && <div>
                  <p className="text-[10px] font-medium uppercase text-zinc-500 mb-2">Feature Importance</p>
                  <div className="space-y-1">
                    {feats.slice(0, 10).map((f: any, i: number) => (
                      <div key={i} className="flex items-center gap-2 text-[10px]">
                        <span className="text-zinc-600 w-4">{i + 1}.</span>
                        <span className="text-zinc-300 w-36 truncate">{f.feature}</span>
                        <div className="flex-1 h-1.5 rounded-full bg-zinc-800 overflow-hidden">
                          <div className="h-full rounded-full bg-amber-500" style={{ width: `${Math.min(f.importance * 100 || f.pct, 100)}%` }} />
                        </div>
                        <span className="text-zinc-500 w-10 text-right">{f.pct ? `${f.pct}%` : `${(f.importance * 100).toFixed(1)}%`}</span>
                      </div>
                    ))}
                  </div>
                </div>}
              </div>}
            </div>
          </>}

          {!data && !loading && !error && <p className="text-sm text-zinc-600 text-center py-12">Select a document and run the analysis.</p>}
        </div>
      )}
    </div>
  );
}

function toTitle(s: string) {
  return s.replace(/_/g, " ").replace(/\w\S*/g, w => w[0].toUpperCase() + w.slice(1).toLowerCase());
}

function ArrowRight(props: React.SVGProps<SVGSVGElement>) {
  return <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></svg>;
}
