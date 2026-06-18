"use client";

import { useState, useEffect } from "react";
import {
  TrendingUp, AlertTriangle, Shield, Lightbulb, BarChart3, Loader2,
  ArrowUpRight, ArrowDownRight, Brain, Target, LineChart, Database,
  Layers, CheckCircle, XCircle,
} from "lucide-react";
import { listDocuments, getAnalytics } from "@/lib/api";
import type { DocumentResponse, AnalyticsResponse } from "@/types";

const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface AnalysisResult {
  target: string;
  problem: { task: string; subtype: string; unique_values: number };
  model: {
    name: string;
    metrics: Record<string, number>;
    all_models_evaluated: string[];
    n_features: number;
    n_samples: number;
  };
  confidence: {
    confidence: number;
    factors: string[];
    breakdown: Record<string, number>;
  };
  feature_importance: { feature: string; importance: number }[];
  risk: { score: number; level: string; description: string };
  dataset_type: string;
  data_quality: { score: number; grade: string };
}

export default function PredictivePage() {
  const [docs, setDocs] = useState<DocumentResponse[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<number | null>(null);
  const [analytics, setAnalytics] = useState<AnalyticsResponse | null>(null);
  const [fetched, setFetched] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!fetched) listDocuments().then(setDocs).finally(() => setFetched(true));
  }, []);

  async function selectDocument(docId: number) {
    setSelectedDoc(docId);
    setAnalytics(null);
    setResult(null);
    setError("");
    const a = await getAnalytics(docId);
    setAnalytics(a);
  }

  async function runFullAnalysis() {
    if (!selectedDoc) return;
    setLoading(true);
    setError("");
    try {
      const token = localStorage.getItem("aura_token");
      const res = await fetch(`${apiBase}/api/v1/predictive/analysis`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ doc_id: selectedDoc }),
      });
      if (!res.ok) { const err = await res.json(); setError(err.detail || "Analysis failed"); return; }
      const data = await res.json();
      setResult(data);
    } catch { setError("Connection failed"); }
    finally { setLoading(false); }
  }

  const m = (result?.model?.metrics || {}) as Record<string, number>;
  const conf = result?.confidence;
  const risk = result?.risk;
  const imp = result?.feature_importance || [];
  const problem = result?.problem;

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Predictive Intelligence</h1>
          <p className="text-sm text-zinc-500">Business predictions, risk analysis, and executive recommendations</p>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        {docs.map(d => (
          <button key={d.id} onClick={() => selectDocument(d.id)}
            className={`rounded-xl border px-4 py-2 text-sm transition-colors ${
              selectedDoc === d.id ? "border-blue-600 bg-blue-600/20 text-blue-300" : "border-zinc-800 bg-zinc-900/50 text-zinc-400 hover:border-zinc-700"
            }`}>
            {d.title.length > 30 ? d.title.slice(0, 30) + "..." : d.title}
          </button>
        ))}
      </div>

      {selectedDoc && (
        <div className="space-y-4">
          {/* Run Analysis */}
          <div className="rounded-xl border border-zinc-800 bg-gradient-to-br from-purple-950/20 to-zinc-900/50 p-5">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-sm font-semibold text-zinc-200">Business Prediction Engine</h2>
                <p className="text-xs text-zinc-500 mt-0.5">
                  {analytics?.dataset_type ? `Detected: ${analytics.dataset_type}` : "Select a document to analyze"}
                  {analytics?.target_variable ? ` · Target: ${analytics.target_variable}` : ""}
                </p>
              </div>
              <button onClick={runFullAnalysis} disabled={loading}
                className="flex items-center gap-1.5 rounded-lg bg-purple-600 px-5 py-2.5 text-xs font-medium hover:bg-purple-500 disabled:opacity-50 shadow-lg shadow-purple-600/20">
                {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Brain className="h-4 w-4" />}
                {loading ? "Analyzing..." : "Run Full Analysis"}
              </button>
            </div>
            {error && <p className="mt-3 text-xs text-red-400">{error}</p>}
          </div>

          {/* Loading */}
          {loading && <div className="space-y-4">{[1,2,3].map(i => <div key={i} className="h-24 animate-pulse rounded-xl bg-zinc-800/50" />)}</div>}

          {result && (
            <>
              {/* Problem & Target Summary */}
              <div className="grid gap-4 sm:grid-cols-4">
                <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4">
                  <p className="text-[10px] uppercase tracking-wider text-zinc-500">Target</p>
                  <p className="text-lg font-semibold text-zinc-200 mt-1">{result.target || "None"}</p>
                </div>
                <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4">
                  <p className="text-[10px] uppercase tracking-wider text-zinc-500">Problem Type</p>
                  <p className="text-lg font-semibold text-zinc-200 mt-1 capitalize">
                    {problem?.task}{problem?.subtype ? ` (${problem.subtype})` : ""}
                  </p>
                </div>
                <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4">
                  <p className="text-[10px] uppercase tracking-wider text-zinc-500">Best Model</p>
                  <p className="text-lg font-semibold text-blue-400 mt-1">{result.model?.name || "N/A"}</p>
                </div>
                <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4">
                  <p className="text-[10px] uppercase tracking-wider text-zinc-500">Data Quality</p>
                  <p className="text-lg font-semibold text-zinc-200 mt-1">
                    {result.data_quality?.score || "—"}<span className="text-xs text-zinc-600">/100</span>
                    <span className="text-[10px] text-zinc-500 ml-1">({result.data_quality?.grade})</span>
                  </p>
                </div>
              </div>

              {/* Model Performance */}
              <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
                <div className="flex items-center gap-2 mb-4">
                  <BarChart3 className="h-5 w-5 text-violet-400" />
                  <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Model Performance</h2>
                  {result.model?.name && <span className="text-[10px] text-zinc-600">({result.model.name})</span>}
                </div>
                <div className="grid gap-3 sm:grid-cols-4">
                  {Object.entries(m).filter(([k]) => !["n_features", "n_samples"].includes(k)).map(([key, val]) => (
                    <div key={key} className="rounded-lg bg-zinc-800/30 p-3 text-center">
                      <p className="text-[10px] uppercase text-zinc-500">{key}</p>
                      <p className="text-lg font-semibold text-zinc-200 mt-0.5">
                        {typeof val === "number" ? (key === "mape" ? `${val.toFixed(1)}%` : val.toFixed(3)) : "—"}
                      </p>
                    </div>
                  ))}
                  <div className="rounded-lg bg-zinc-800/30 p-3 text-center">
                    <p className="text-[10px] uppercase text-zinc-500">Features</p>
                    <p className="text-lg font-semibold text-zinc-200 mt-0.5">{result.model?.n_features || 0}</p>
                  </div>
                  <div className="rounded-lg bg-zinc-800/30 p-3 text-center">
                    <p className="text-[10px] uppercase text-zinc-500">Samples</p>
                    <p className="text-lg font-semibold text-zinc-200 mt-0.5">{result.model?.n_samples || 0}</p>
                  </div>
                </div>
                {result.model?.all_models_evaluated && result.model.all_models_evaluated.length > 1 && (
                  <p className="mt-2 text-[10px] text-zinc-600">Evaluated: {result.model.all_models_evaluated.join(", ")}</p>
                )}
              </div>

              {/* Confidence */}
              {conf && (
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
                    <div className="flex items-center justify-between mb-3">
                      <h2 className="text-xs font-medium uppercase tracking-wider text-zinc-500">Prediction Confidence</h2>
                      <span className={`text-xl font-bold ${conf.confidence >= 70 ? "text-emerald-400" : conf.confidence >= 40 ? "text-amber-400" : "text-red-400"}`}>
                        {conf.confidence}%
                      </span>
                    </div>
                    <div className="h-2 rounded-full bg-zinc-800 overflow-hidden mb-3">
                      <div className={`h-full rounded-full ${conf.confidence >= 70 ? "bg-emerald-500" : conf.confidence >= 40 ? "bg-amber-500" : "bg-red-500"}`}
                        style={{ width: `${conf.confidence}%` }} />
                    </div>
                    <div className="space-y-1 text-[10px]">
                      {Object.entries(conf.breakdown || {}).map(([key, val]) => (
                        <div key={key} className="flex items-center gap-2">
                          <span className="text-zinc-500 w-28 capitalize">{key.replace(/_/g, " ")}</span>
                          <div className="flex-1 h-1.5 rounded-full bg-zinc-800 overflow-hidden">
                            <div className="h-full rounded-full bg-blue-500" style={{ width: `${val}%` }} />
                          </div>
                          <span className="text-zinc-400 w-8 text-right">{val.toFixed(0)}%</span>
                        </div>
                      ))}
                    </div>
                  </div>
                  <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
                    <h2 className="text-xs font-medium uppercase tracking-wider text-zinc-500 mb-3">Confidence Factors</h2>
                    <ul className="space-y-1.5">
                      {(conf.factors || []).map((f: string, i: number) => (
                        <li key={i} className="flex items-center gap-1.5 text-xs text-zinc-300">
                          <CheckCircle className="h-3.5 w-3.5 text-emerald-500 shrink-0" />
                          {f}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}

              {/* Feature Importance (Top Drivers) */}
              {imp.length > 0 && (
                <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
                  <div className="flex items-center gap-2 mb-4">
                    <Target className="h-5 w-5 text-amber-400" />
                    <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Top Drivers — {result.target}</h2>
                  </div>
                  <div className="space-y-2">
                    {imp.slice(0, 10).map((f, i) => {
                      const pct = Math.min(f.importance * 100, 100);
                      return (
                        <div key={f.feature} className="flex items-center gap-3">
                          <span className="text-[10px] text-zinc-600 w-5">{i + 1}.</span>
                          <span className="text-xs text-zinc-200 w-40 truncate">{f.feature}</span>
                          <div className="flex-1 h-2 rounded-full bg-zinc-800 overflow-hidden">
                            <div className="h-full rounded-full bg-amber-500" style={{ width: `${pct}%` }} />
                          </div>
                          <span className="text-[10px] text-zinc-500 w-12 text-right">{pct.toFixed(1)}%</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Risk Score */}
              {risk && (
                <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <Shield className="h-5 w-5 text-red-400" />
                    <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Risk Assessment</h2>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className={`h-16 w-16 rounded-full flex items-center justify-center text-lg font-bold border-4 ${
                      risk.score >= 70 ? "border-red-500 text-red-400 bg-red-950/30" :
                      risk.score >= 40 ? "border-amber-500 text-amber-400 bg-amber-950/30" :
                      "border-emerald-500 text-emerald-400 bg-emerald-950/30"
                    }`}>
                      {risk.score}
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-zinc-200 capitalize">{risk.level} Risk</p>
                      <p className="text-xs text-zinc-400">{risk.description}</p>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      )}

      {!selectedDoc && fetched && docs.length > 0 && (
        <p className="text-sm text-zinc-600 text-center py-12">Select a document to run predictive analysis.</p>
      )}
    </div>
  );
}
