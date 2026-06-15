"use client";

import { useState, useEffect } from "react";
import {
  Brain, Shield, AlertTriangle, Target, Flag, FileText, Bot,
  Loader2, TrendingUp, DollarSign, Users, Clock, Database,
  CheckCircle, XCircle, BarChart3, Lightbulb,
} from "lucide-react";
import { listDocuments } from "@/lib/api";
import type { DocumentResponse } from "@/types";

interface ExecutiveIntelligence {
  executive_summary: {
    summary: string;
    key_findings: string[];
    business_impact: string;
    strategic_implications: string;
    confidence: number;
    sources: string[];
  };
  business_health: {
    overall: number;
    financial_health: number;
    operational_health: number;
    growth_potential: number;
    risk_exposure: number;
    data_quality: number;
    level: string;
  };
  risks: {
    name: string;
    description: string;
    category: string;
    severity: string;
    probability: string;
    potential_impact: string;
    mitigation: string;
  }[];
  opportunities: {
    name: string;
    description: string;
    category: string;
    expected_impact: string;
    priority: string;
    confidence: number;
    recommended_action: string;
  }[];
  recommendations: {
    title: string;
    reasoning: string;
    expected_benefit: string;
    priority: string;
    confidence: number;
  }[];
  sources: string[];
  confidence_scores: Record<string, number>;
  overall_confidence: number;
}

export default function ExecutivePage() {
  const [docs, setDocs] = useState<DocumentResponse[]>([]);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [data, setData] = useState<ExecutiveIntelligence | null>(null);
  const [loading, setLoading] = useState(false);
  const [fetched, setFetched] = useState(false);

  useEffect(() => { if (!fetched) listDocuments().then(setDocs).finally(() => setFetched(true)); }, []);

  function toggleDoc(id: number) {
    setSelectedIds(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  }

  async function runAnalysis() {
    if (selectedIds.length === 0) return;
    setLoading(true);
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/analytics/executive-intelligence`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ doc_ids: selectedIds }),
      });
      const json = await res.json();
      setData(json);
    } catch { /* ignore */ }
    finally { setLoading(false); }
  }

  const health = data?.business_health;

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Executive Intelligence</h1>
          <p className="text-sm text-zinc-500">AI-powered business insights for leadership decision-making</p>
        </div>
      </div>

      {/* Document multi-selector */}
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-4">
        <p className="text-xs font-medium uppercase tracking-wider text-zinc-500 mb-2">Select documents for analysis</p>
        <div className="flex flex-wrap gap-2">
          {docs.map(d => (
            <button key={d.id} onClick={() => toggleDoc(d.id)}
              className={`rounded-xl border px-3 py-1.5 text-xs transition-colors ${
                selectedIds.includes(d.id) ? "border-blue-600 bg-blue-600/20 text-blue-300" : "border-zinc-800 bg-zinc-900/50 text-zinc-400 hover:border-zinc-700"
              }`}>
              {d.title.slice(0, 28)}
            </button>
          ))}
        </div>
        <button onClick={runAnalysis} disabled={loading || selectedIds.length === 0}
          className="mt-3 flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-2 text-xs font-medium hover:bg-blue-500 disabled:opacity-50">
          {loading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Brain className="h-3.5 w-3.5" />}
          {loading ? "Analyzing..." : `Analyze ${selectedIds.length} document(s)`}
        </button>
      </div>

      {loading && (
        <div className="space-y-4">{[1,2,3,4].map(i => <div key={i} className="h-24 animate-pulse rounded-xl bg-zinc-800/50" />)}</div>
      )}

      {data && (
        <div className="space-y-6">
          {/* Business Health Score */}
          {health && (
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
              <div className="flex items-center gap-2 mb-4">
                <Shield className="h-5 w-5 text-zinc-400" />
                <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Business Health Score</h2>
                <span className={`ml-auto rounded-full px-2.5 py-0.5 text-xs font-medium ${
                  health.level === "excellent" ? "bg-emerald-950 text-emerald-400" :
                  health.level === "good" ? "bg-blue-950 text-blue-400" :
                  health.level === "moderate" ? "bg-amber-950 text-amber-400" :
                  "bg-red-950 text-red-400"
                }`}>{health.overall}/100 - {health.level}</span>
              </div>
              <div className="grid gap-3 sm:grid-cols-5">
                {[
                  { label: "Financial Health", value: health.financial_health, icon: DollarSign },
                  { label: "Operational Health", value: health.operational_health, icon: Clock },
                  { label: "Growth Potential", value: health.growth_potential, icon: TrendingUp },
                  { label: "Risk Exposure", value: 100 - health.risk_exposure, icon: Shield, invert: true },
                  { label: "Data Quality", value: health.data_quality, icon: Database },
                ].map(m => (
                  <div key={m.label} className="text-center">
                    <m.icon className="mx-auto h-4 w-4 text-zinc-500 mb-1" />
                    <p className="text-[10px] uppercase tracking-wider text-zinc-500">{m.label}</p>
                    <p className={`text-lg font-semibold ${
                      m.value >= 70 ? "text-emerald-400" : m.value >= 40 ? "text-amber-400" : "text-red-400"
                    }`}>{m.value}</p>
                    <div className="mt-1 h-1.5 rounded-full bg-zinc-800 overflow-hidden">
                      <div className={`h-full rounded-full ${
                        m.value >= 70 ? "bg-emerald-500" : m.value >= 40 ? "bg-amber-500" : "bg-red-500"
                      }`} style={{ width: `${m.value}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Executive Summary */}
          {data.executive_summary?.summary && (
            <div className="rounded-xl border border-emerald-900/30 bg-emerald-950/20 p-5">
              <div className="flex items-center gap-2 mb-3">
                <FileText className="h-5 w-5 text-emerald-400" />
                <h2 className="text-sm font-medium uppercase tracking-wider text-emerald-400">Executive Summary</h2>
                <span className="ml-auto text-xs text-zinc-500">{(data.confidence_scores.summary * 100).toFixed(0)}% confidence</span>
              </div>
              <p className="text-sm leading-relaxed text-zinc-200">{data.executive_summary.summary}</p>
              {data.executive_summary.key_findings?.length > 0 && (
                <div className="mt-3 grid gap-2 sm:grid-cols-2">
                  {data.executive_summary.key_findings.map((f, i) => (
                    <div key={i} className="flex gap-2 text-xs text-zinc-300">
                      <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-500" />
                      {f}
                    </div>
                  ))}
                </div>
              )}
              {data.executive_summary.business_impact && (
                <p className="mt-3 text-xs text-zinc-400"><span className="font-medium text-zinc-300">Business Impact:</span> {data.executive_summary.business_impact}</p>
              )}
              {data.executive_summary.strategic_implications && (
                <p className="mt-1 text-xs text-zinc-400"><span className="font-medium text-zinc-300">Strategic Implications:</span> {data.executive_summary.strategic_implications}</p>
              )}
            </div>
          )}

          {/* Top Risks */}
          {data.risks?.length > 0 && (
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
              <div className="flex items-center gap-2 mb-4">
                <AlertTriangle className="h-5 w-5 text-red-400" />
                <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Top Risks</h2>
                <span className="ml-auto text-xs text-zinc-500">{(data.confidence_scores.risks * 100).toFixed(0)}% confidence</span>
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                {data.risks.map((r, i) => (
                  <div key={i} className="rounded-lg border border-zinc-800 bg-zinc-900/70 p-3">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-semibold text-zinc-200">{r.name}</span>
                      <span className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${
                        r.severity === "High" ? "bg-red-900/50 text-red-300" :
                        r.severity === "Medium" ? "bg-amber-900/50 text-amber-300" :
                        "bg-blue-900/50 text-blue-300"
                      }`}>{r.severity}</span>
                    </div>
                    <p className="text-[10px] text-zinc-500 mb-1">{r.category}</p>
                    <p className="text-xs text-zinc-400 mb-2">{r.description}</p>
                    <div className="flex items-center gap-2 text-[10px]">
                      <span className="text-zinc-600">Probability: <span className="text-zinc-300">{r.probability}</span></span>
                      <span className="text-zinc-600">Impact: <span className="text-zinc-300">{r.potential_impact?.slice(0, 40)}</span></span>
                    </div>
                    <p className="mt-1 text-[10px] text-zinc-500"><span className="text-zinc-400">Mitigation:</span> {r.mitigation}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Top Opportunities */}
          {data.opportunities?.length > 0 && (
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
              <div className="flex items-center gap-2 mb-4">
                <Target className="h-5 w-5 text-emerald-400" />
                <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Top Opportunities</h2>
                <span className="ml-auto text-xs text-zinc-500">{(data.confidence_scores.opportunities * 100).toFixed(0)}% confidence</span>
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                {data.opportunities.map((o, i) => (
                  <div key={i} className="rounded-lg border border-emerald-800/30 bg-emerald-950/20 p-3">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-semibold text-zinc-200">{o.name}</span>
                      <span className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${
                        o.priority === "High" ? "bg-emerald-900/50 text-emerald-300" :
                        "bg-amber-900/50 text-amber-300"
                      }`}>{o.priority}</span>
                    </div>
                    <p className="text-[10px] text-zinc-500 mb-1">{o.category} · {o.expected_impact} impact</p>
                    <p className="text-xs text-zinc-400 mb-1">{o.description}</p>
                    <p className="text-[10px] text-zinc-500"><span className="text-zinc-400">Action:</span> {o.recommended_action}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Recommendations */}
          {data.recommendations?.length > 0 && (
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
              <div className="flex items-center gap-2 mb-4">
                <Flag className="h-5 w-5 text-purple-400" />
                <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Recommended Actions</h2>
              </div>
              <div className="space-y-2">
                {data.recommendations.map((r, i) => (
                  <div key={i} className="flex items-start gap-3 rounded-lg border border-zinc-800 bg-zinc-900/70 p-3">
                    <div className={`mt-0.5 h-2 w-2 shrink-0 rounded-full ${
                      r.priority === "high" || r.priority === "High" ? "bg-red-500" :
                      r.priority === "medium" || r.priority === "Medium" ? "bg-amber-500" : "bg-blue-500"
                    }`} />
                    <div className="min-w-0 flex-1">
                      <p className="text-xs font-semibold text-zinc-200">{r.title}</p>
                      <p className="text-xs text-zinc-400 mt-0.5">{r.reasoning}</p>
                      <p className="text-[10px] text-zinc-500 mt-0.5">Benefit: {r.expected_benefit}</p>
                    </div>
                    <div className="shrink-0 text-right text-[10px]">
                      <span className={`rounded px-1.5 py-0.5 font-medium ${
                        r.priority === "high" || r.priority === "High" ? "bg-red-900/50 text-red-300" :
                        r.priority === "medium" || r.priority === "Medium" ? "bg-amber-900/50 text-amber-300" :
                        "bg-blue-900/50 text-blue-300"
                      }`}>{r.priority}</span>
                      <p className="text-zinc-600 mt-0.5">{(r.confidence * 100).toFixed(0)}% conf</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Sources & Confidence */}
          <div className="grid gap-4 sm:grid-cols-2">
            {data.sources?.length > 0 && (
              <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4">
                <p className="text-xs font-medium uppercase tracking-wider text-zinc-500 mb-2">Sources</p>
                <div className="flex flex-wrap gap-1.5">
                  {data.sources.map((s, i) => (
                    <span key={i} className="rounded-full bg-zinc-800 px-2 py-0.5 text-[10px] text-zinc-400">{s}</span>
                  ))}
                </div>
              </div>
            )}
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4">
              <p className="text-xs font-medium uppercase tracking-wider text-zinc-500 mb-2">Confidence Indicators</p>
              <div className="space-y-1.5">
                {Object.entries(data.confidence_scores).map(([key, val]) => (
                  <div key={key} className="flex items-center gap-2 text-[10px]">
                    <span className="w-28 text-zinc-500 capitalize">{key.replace(/_/g, " ")}</span>
                    <div className="flex-1 h-1.5 rounded-full bg-zinc-800 overflow-hidden">
                      <div className={`h-full rounded-full ${
                        (val as number) >= 0.7 ? "bg-emerald-500" : (val as number) >= 0.4 ? "bg-amber-500" : "bg-red-500"
                      }`} style={{ width: `${(val as number) * 100}%` }} />
                    </div>
                    <span className="w-8 text-right text-zinc-400">{((val as number) * 100).toFixed(0)}%</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {!loading && !data && fetched && (
        <p className="text-sm text-zinc-600 text-center py-12">Select one or more documents and click Analyze.</p>
      )}
    </div>
  );
}
