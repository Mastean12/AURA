"use client";

import { useState, useEffect } from "react";
import {
  TrendingUp, AlertTriangle, Target, Loader2, DollarSign,
  Sliders, GitCompare, BarChart3, Shield, Zap, ChevronDown,
  ChevronRight, FileText, ArrowUp, ArrowDown, Activity,
  Brain,
} from "lucide-react";
import { listDocuments } from "@/lib/api";
import type { DocumentResponse } from "@/types";

const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const catEmoji: Record<string, string> = {
  growth: "🚀",
  risk: "⚠️",
  efficiency: "⚡",
  retention: "🎯",
};

export default function ScenariosPage() {
  const [docs, setDocs] = useState<DocumentResponse[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<number | null>(null);
  const [fetched, setFetched] = useState(false);
  const [templates, setTemplates] = useState<any[]>([]);
  const [adjustments, setAdjustments] = useState<Record<string, number>>({});
  const [results, setResults] = useState<Record<string, any>>({});
  const [comparison, setComparison] = useState<Record<string, any> | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showDetail, setShowDetail] = useState<Record<string, boolean>>({});

  useEffect(() => {
    if (!fetched) {
      listDocuments().then(d => setDocs(d)).finally(() => setFetched(true));
      fetch(`${apiBase}/api/v1/scenarios/templates`).then(r => r.json()).then(d => {
        setTemplates(d.templates || []);
        const init: Record<string, number> = {};
        (d.templates || []).forEach((t: any) => { init[t.id] = t.default_pct || 10; });
        setAdjustments(init);
      }).catch(() => {});
    }
  }, []);

  async function runScenario(scenarioId: string) {
    if (!selectedDoc) return;
    setLoading(true); setError("");
    try {
      const token = localStorage.getItem("aura_token");
      const res = await fetch(`${apiBase}/api/v1/scenarios/simulate`, {
        method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ doc_id: selectedDoc, scenario_id: scenarioId, adjustment_pct: adjustments[scenarioId] || 0 }),
      });
      if (!res.ok) { const e = await res.json(); setError(e.detail || "Failed"); return; }
      const data = await res.json();
      setResults(prev => ({ ...prev, [scenarioId]: data }));
    } catch { setError("Connection failed"); }
    finally { setLoading(false); }
  }

  async function runAllScenarios() {
    if (!selectedDoc) return;
    setLoading(true); setError(""); setResults({}); setComparison(null);
    try {
      const token = localStorage.getItem("aura_token");
      const res = await fetch(`${apiBase}/api/v1/scenarios/simulate`, {
        method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ doc_id: selectedDoc, scenario_id: "", adjustment_pct: 0 }),
      });
      if (!res.ok) { const e = await res.json(); setError(e.detail || "Failed"); return; }
      const data = await res.json();
      setComparison(data);
    } catch { setError("Connection failed"); }
    finally { setLoading(false); }
  }

  const comparisonScenarios = comparison?.scenarios || [];

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Scenario Simulation Engine</h1>
          <p className="text-sm text-zinc-500">Test strategic "what-if" scenarios before making decisions</p>
        </div>
        <div className="flex items-center gap-2 text-xs text-zinc-600">
          <Activity className="h-4 w-4 text-blue-400" />
          <span>Phase 2 — Section 4</span>
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
            <button onClick={runAllScenarios} disabled={loading}
              className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-blue-600 to-purple-600 px-6 py-3 text-sm font-medium hover:from-blue-500 hover:to-purple-500 shadow-lg shadow-blue-600/20 disabled:opacity-50">
              {loading ? <Loader2 className="h-5 w-5 animate-spin" /> : <GitCompare className="h-5 w-5" />}
              Run Scenario Analysis
            </button>
          </div>
          {error && <p className="text-xs text-red-400">{error}</p>}

          {/* === SCENARIO COMPARISON CARDS === */}
          {comparisonScenarios.length > 0 && (
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
              <div className="flex items-center gap-2 mb-4">
                <GitCompare className="h-5 w-5 text-violet-400" />
                <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Scenario Comparison</h2>
              </div>
              <div className="grid gap-4 md:grid-cols-3">
                {comparisonScenarios.map((s: any) => {
                  const isBest = s.label === "Best Case";
                  const isWorst = s.label === "Worst Case";
                  const borderColor = isBest ? "border-emerald-800/40" : isWorst ? "border-red-800/40" : "border-amber-800/40";
                  const bgColor = isBest ? "bg-emerald-950/20" : isWorst ? "bg-red-950/20" : "bg-amber-950/20";
                  const textColor = isBest ? "text-emerald-400" : isWorst ? "text-red-400" : "text-amber-400";
                  const icon = isBest ? ArrowUp : isWorst ? ArrowDown : TrendingUp;
                  const Icon = icon;
                  return (
                    <div key={s.label} className={`rounded-xl border ${borderColor} ${bgColor} p-4`}>
                      <div className="flex items-center justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <Icon className={`h-4 w-4 ${textColor}`} />
                          <span className={`text-xs font-semibold ${textColor}`}>{s.label}</span>
                        </div>
                        <span className={`rounded px-2 py-0.5 text-[9px] font-medium ${textColor} bg-zinc-800/50`}>{s.scenario}</span>
                      </div>
                      <div className="space-y-2">
                        {[
                          { label: "Revenue Impact", value: s.revenue_impact, fmt: "currency" },
                          { label: "Risk Score", value: s.risk_score, fmt: "pct" },
                          { label: "Confidence", value: s.confidence, fmt: "pct" },
                        ].map((m: any) => (
                          <div key={m.label} className="flex justify-between text-[11px]">
                            <span className="text-zinc-500">{m.label}</span>
                            <span className={`font-semibold ${m.label === "Risk Score" ? (s.risk_score > 60 ? "text-red-400" : s.risk_score > 30 ? "text-amber-400" : "text-emerald-400") : ""}`}>
                              {m.fmt === "currency"
                                ? `$${Math.abs(s.revenue_impact || 0).toLocaleString()}`
                                : `${Math.round(s[m.label === "Revenue Impact" ? "revenue_impact" : m.label === "Risk Score" ? "risk_score" : "confidence"])}%`}
                            </span>
                          </div>
                        ))}
                      </div>
                      <div className="mt-3 h-1.5 rounded-full bg-zinc-800 overflow-hidden">
                        <div className={`h-full rounded-full ${isBest ? "bg-emerald-500" : isWorst ? "bg-red-500" : "bg-amber-500"}`}
                          style={{ width: `${Math.min(s.confidence || 50, 100)}%` }} />
                      </div>
                      <p className="text-[9px] text-zinc-600 mt-1">{s.change_pct > 0 ? "+" : ""}{s.change_pct}% change</p>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* === INTERACTIVE SCENARIO PANEL === */}
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
            <div className="flex items-center gap-2 mb-4">
              <Sliders className="h-5 w-5 text-orange-400" />
              <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">What-If Scenario Simulator</h2>
            </div>
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
              {templates.map((t: any) => {
                const res = results[t.id];
                const expanded = showDetail[t.id];
                return (
                  <div key={t.id} className="rounded-xl border border-zinc-800 bg-zinc-900/70 p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-lg">{catEmoji[t.category] || "📊"}</span>
                      <span className={`rounded px-1.5 py-0.5 text-[9px] font-medium uppercase ${
                        t.category === "risk" ? "bg-red-900/50 text-red-300"
                          : t.category === "growth" ? "bg-emerald-900/50 text-emerald-300"
                            : t.category === "efficiency" ? "bg-blue-900/50 text-blue-300"
                              : "bg-purple-900/50 text-purple-300"
                      }`}>{t.category}</span>
                    </div>
                    <p className="text-xs font-medium text-zinc-200 mb-2">{t.label.replace("X%", `${adjustments[t.id] || t.default_pct}%`)}</p>
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-[10px] text-zinc-500">0%</span>
                      <input type="range" min="1" max="100" value={adjustments[t.id] || t.default_pct}
                        onChange={e => setAdjustments(prev => ({ ...prev, [t.id]: Number(e.target.value) }))}
                        className="flex-1 h-1 appearance-none rounded-full bg-zinc-800 accent-blue-500 cursor-pointer" />
                      <span className="text-[10px] text-zinc-500">100%</span>
                    </div>
                    <div className="flex items-center gap-2 mb-2">
                      <button onClick={() => runScenario(t.id)} disabled={loading}
                        className="flex-1 rounded-lg bg-blue-600/30 py-1.5 text-[10px] font-medium text-blue-300 hover:bg-blue-600/50 transition-colors disabled:opacity-50">
                        Simulate
                      </button>
                      {res && (
                        <button onClick={() => setShowDetail(prev => ({ ...prev, [t.id]: !expanded }))}
                          className="rounded-lg bg-zinc-800/50 p-1.5 text-zinc-500 hover:text-zinc-300">
                          {expanded ? <ChevronDown className="h-3 w-3" /> : <ChevronRight className="h-3 w-3" />}
                        </button>
                      )}
                    </div>
                    {res && (
                      <div className="rounded-lg bg-zinc-800/30 p-2">
                        <div className="grid grid-cols-2 gap-1">
                          <div className="text-center">
                            <p className="text-[9px] text-zinc-600">Before</p>
                            <p className="text-[10px] font-semibold text-zinc-300">{res.current_value?.toLocaleString()}</p>
                          </div>
                          <div className="text-center">
                            <p className="text-[9px] text-zinc-600">After</p>
                            <p className={`text-[10px] font-semibold ${res.direction === "increase" ? "text-emerald-400" : "text-red-400"}`}>
                              {res.simulated_value?.toLocaleString()}
                            </p>
                          </div>
                        </div>
                        <div className="flex justify-between text-[9px] text-zinc-600 mt-1">
                          <span className="flex items-center gap-0.5">
                            <DollarSign className="h-2.5 w-2.5" />
                            {res.revenue_impact?.toFixed(0)}
                          </span>
                          <span className="flex items-center gap-0.5">
                            <Shield className="h-2.5 w-2.5" />
                            {res.risk_score}%
                          </span>
                          <span className="flex items-center gap-0.5">
                            <Brain className="h-2.5 w-2.5" />
                            {res.confidence}%
                          </span>
                        </div>
                      </div>
                    )}
                    {res && expanded && (
                      <div className="mt-2 space-y-1 rounded-lg bg-zinc-800/40 p-2">
                        {[
                          ["Revenue Impact", res.revenue_impact, "currency"],
                          ["Profit Impact", res.profit_impact, "currency"],
                          ["Cost Impact", res.cost_impact, "currency"],
                          ["ROI", res.roi, "decimal"],
                          ["Risk Score", res.risk_score, "pct"],
                          ["Confidence", res.confidence, "pct"],
                        ].map(([label, val, fmt]: any) => (
                          <div key={label} className="flex justify-between text-[10px]">
                            <span className="text-zinc-500">{label}</span>
                            <span className={`font-medium ${
                              label === "Risk Score" ? (val > 60 ? "text-red-400" : val > 30 ? "text-amber-400" : "text-emerald-400")
                                : label === "Confidence" ? "text-blue-400"
                                  : label === "ROI" ? (val > 1 ? "text-emerald-400" : "text-zinc-300")
                                    : val >= 0 ? "text-emerald-400" : "text-red-400"
                            }`}>
                              {fmt === "currency" ? `$${Math.abs(val || 0).toLocaleString()}` : fmt === "pct" ? `${Math.round(val || 0)}%` : `${(val || 0).toFixed(2)}x`}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>

          {/* === BUSINESS IMPACT DASHBOARD === */}
          {Object.keys(results).length > 0 && (
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
              <div className="flex items-center gap-2 mb-4">
                <BarChart3 className="h-5 w-5 text-blue-400" />
                <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Business Impact Dashboard</h2>
              </div>
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                {[
                  {
                    label: "Total Revenue Impact",
                    value: Object.values(results).reduce((s: number, r: any) => s + (r.revenue_impact || 0), 0),
                    icon: DollarSign, color: "text-blue-400", bg: "bg-blue-950/20",
                    desc: "Sum of all simulated revenue changes",
                  },
                  {
                    label: "Average Risk Score",
                    value: Object.values(results).reduce((s: number, r: any) => s + (r.risk_score || 0), 0) / Math.max(Object.keys(results).length, 1),
                    icon: Shield, color: "text-amber-400", bg: "bg-amber-950/20", suffix: "%",
                    desc: "Mean risk across all scenarios",
                  },
                  {
                    label: "Best ROI",
                    value: Math.max(...Object.values(results).map((r: any) => r.roi || 0)),
                    icon: Zap, color: "text-emerald-400", bg: "bg-emerald-950/20", suffix: "x",
                    desc: "Highest return on investment",
                  },
                  {
                    label: "Avg Confidence",
                    value: Object.values(results).reduce((s: number, r: any) => s + (r.confidence || 0), 0) / Math.max(Object.keys(results).length, 1),
                    icon: Brain, color: "text-purple-400", bg: "bg-purple-950/20", suffix: "%",
                    desc: "Average prediction confidence",
                  },
                ].map((m: any) => (
                  <div key={m.label} className={`rounded-xl ${m.bg} border border-zinc-800 p-4`}>
                    <div className="flex items-center gap-2 mb-2">
                      <m.icon className={`h-4 w-4 ${m.color}`} />
                      <p className="text-[10px] font-medium uppercase tracking-wider text-zinc-500">{m.label}</p>
                    </div>
                    <p className={`text-lg font-bold ${m.color}`}>
                      {m.suffix === "%" ? `${Math.round(m.value)}%` : m.suffix === "x" ? `${m.value.toFixed(2)}x` : `$${Math.abs(m.value).toLocaleString()}`}
                    </p>
                    <p className="text-[9px] text-zinc-600 mt-1">{m.desc}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {!loading && Object.keys(results).length === 0 && !comparison && !error && (
            <p className="text-sm text-zinc-600 text-center py-12">Select a scenario and click Simulate, or run the full Scenario Analysis.</p>
          )}
        </div>
      )}
    </div>
  );
}
