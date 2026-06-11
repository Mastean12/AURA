"use client";

import { useState, useEffect } from "react";
import {
  TrendingUp, AlertTriangle, Shield, Lightbulb, BarChart3, LineChart,
  Loader2, ChevronDown, ArrowUpRight, ArrowDownRight, Minus, Layers,
  DollarSign, Clock, Users, Database, Download,
} from "lucide-react";
import {
  listDocuments, getAnalytics, getForecast, getAnomalies,
  getRiskScore, getRecommendations,
} from "@/lib/api";
import type {
  DocumentResponse, AnalyticsResponse, ForecastResponse,
  AnomalyResponse, RiskScoreResponse, RecommendationResponse,
  ForecastPoint, AnomalyItem, RiskCategory, RecommendationItem,
} from "@/types";

export default function PredictivePage() {
  const [docs, setDocs] = useState<DocumentResponse[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<number | null>(null);
  const [analytics, setAnalytics] = useState<AnalyticsResponse | null>(null);
  const [fetched, setFetched] = useState(false);

  const [forecastCol, setForecastCol] = useState("");
  const [forecastPeriods, setForecastPeriods] = useState(30);
  const [forecast, setForecast] = useState<ForecastResponse | null>(null);
  const [forecastLoading, setForecastLoading] = useState(false);

  const [anomalyCol, setAnomalyCol] = useState("");
  const [anomalies, setAnomalies] = useState<AnomalyResponse | null>(null);
  const [anomaliesLoading, setAnomaliesLoading] = useState(false);

  const [risk, setRisk] = useState<RiskScoreResponse | null>(null);
  const [riskLoading, setRiskLoading] = useState(false);

  const [recommendations, setRecommendations] = useState<RecommendationResponse | null>(null);
  const [recommendationsLoading, setRecommendationsLoading] = useState(false);

  useEffect(() => {
    if (!fetched) listDocuments().then(setDocs).finally(() => setFetched(true));
  }, []);

  async function selectDocument(docId: number) {
    setSelectedDoc(docId);
    setAnalytics(null);
    setForecast(null);
    setAnomalies(null);
    setRisk(null);
    setRecommendations(null);
    const a = await getAnalytics(docId);
    setAnalytics(a);
    if (a.columns.length > 0) {
      const numCol = a.columns.find(c => c.dtype === "numeric");
      setForecastCol(numCol?.name ?? a.columns[0].name);
      setAnomalyCol(numCol?.name ?? a.columns[0].name);
    }
  }

  async function runForecast() {
    if (!selectedDoc || !forecastCol) return;
    setForecastLoading(true);
    try {
      const r = await getForecast(selectedDoc, forecastCol, forecastPeriods);
      setForecast(r);
    } finally { setForecastLoading(false); }
  }

  async function runAnomalies() {
    if (!selectedDoc || !anomalyCol) return;
    setAnomaliesLoading(true);
    try {
      const r = await getAnomalies(selectedDoc, anomalyCol);
      setAnomalies(r);
    } finally { setAnomaliesLoading(false); }
  }

  async function runRisk() {
    if (!selectedDoc) return;
    setRiskLoading(true);
    try {
      const r = await getRiskScore(selectedDoc);
      setRisk(r);
    } finally { setRiskLoading(false); }
  }

  async function runRecommendations() {
    if (!selectedDoc) return;
    setRecommendationsLoading(true);
    try {
      const r = await getRecommendations(selectedDoc);
      setRecommendations(r);
    } finally { setRecommendationsLoading(false); }
  }

  // AI-powered analyses are triggered manually via the Run buttons below

  const numericCols = analytics?.columns.filter(c => c.dtype === "numeric") ?? [];

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Predictive Intelligence</h1>
          <p className="text-sm text-zinc-500">AI-powered forecasting, anomaly detection, risk scoring & recommendations</p>
        </div>
      </div>

      {/* Doc selector */}
      <div className="flex flex-wrap gap-2">
        {docs.map(d => (
          <button key={d.id} onClick={() => selectDocument(d.id)}
            className={`rounded-xl border px-4 py-2 text-sm transition-colors ${
              selectedDoc === d.id ? "border-blue-600 bg-blue-600/20 text-blue-300" : "border-zinc-800 bg-zinc-900/50 text-zinc-400 hover:border-zinc-700"
            }`}>
            {d.title.length > 30 ? d.title.slice(0, 30) + "..." : d.title}
          </button>
        ))}
        {!fetched && <div className="h-10 w-40 animate-pulse rounded-xl bg-zinc-800" />}
        {fetched && docs.length === 0 && <p className="text-sm text-zinc-600">No documents uploaded yet.</p>}
      </div>

      {selectedDoc && (
        <div className="space-y-6">
          {/* SECTION 1: Forecast Dashboard */}
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <LineChart className="h-5 w-5 text-violet-400" />
                <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Forecast Dashboard</h2>
              </div>
              <div className="flex items-center gap-2">
                <select value={forecastCol} onChange={e => setForecastCol(e.target.value)}
                  className="rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-1.5 text-xs text-zinc-300 outline-none focus:border-violet-600">
                  {numericCols.map(c => <option key={c.name} value={c.name}>{c.name}</option>)}
                </select>
                <select value={forecastPeriods} onChange={e => setForecastPeriods(Number(e.target.value))}
                  className="rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-1.5 text-xs text-zinc-300 outline-none focus:border-violet-600">
                  <option value={30}>30 days</option>
                  <option value={90}>90 days</option>
                  <option value={365}>12 months</option>
                </select>
                <button onClick={runForecast} disabled={forecastLoading}
                  className="flex items-center gap-1 rounded-lg bg-violet-600 px-3 py-1.5 text-xs font-medium hover:bg-violet-500 disabled:opacity-50">
                  {forecastLoading ? <Loader2 className="h-3 w-3 animate-spin" /> : <TrendingUp className="h-3 w-3" />}
                  Forecast
                </button>
              </div>
            </div>

            {forecastLoading ? (
              <div className="h-64 animate-pulse rounded-xl bg-zinc-800/50" />
            ) : forecast && forecast.forecast.length > 0 ? (
              <div className="space-y-4">
                <ForecastChart data={forecast} />
                <div className="grid grid-cols-4 gap-3 text-center text-xs">
                  <div className="rounded-lg bg-zinc-800/50 p-3">
                    <p className="text-zinc-500 mb-1">Trend</p>
                    <span className={`font-semibold ${
                      forecast.trend_direction === "up" ? "text-emerald-400" :
                      forecast.trend_direction === "down" ? "text-red-400" : "text-zinc-300"
                    }`}>
                      {forecast.trend_direction === "up" ? "Upward ↗" :
                       forecast.trend_direction === "down" ? "Downward ↘" : "Stable →"}
                    </span>
                  </div>
                  <div className="rounded-lg bg-zinc-800/50 p-3">
                    <p className="text-zinc-500 mb-1">Strength</p>
                    <p className="font-semibold text-zinc-200">{(forecast.trend_strength * 100).toFixed(0)}%</p>
                  </div>
                  <div className="rounded-lg bg-zinc-800/50 p-3">
                    <p className="text-zinc-500 mb-1">Confidence</p>
                    <p className="font-semibold text-zinc-200">{(forecast.confidence_avg * 100).toFixed(0)}%</p>
                  </div>
                  <div className="rounded-lg bg-zinc-800/50 p-3">
                    <p className="text-zinc-500 mb-1">Periods</p>
                    <p className="font-semibold text-zinc-200">{forecastPeriods}</p>
                  </div>
                </div>
                <p className="text-xs leading-relaxed text-zinc-400">{forecast.explanation}</p>
              </div>
            ) : (
              <p className="text-sm text-zinc-600 text-center py-12">Select a numeric column and run forecast.</p>
            )}
          </div>

          {/* SECTION 2: Anomaly Alerts Center */}
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-5 w-5 text-amber-400" />
                <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Anomaly Alerts Center</h2>
                {anomalies && anomalies.anomaly_count > 0 && (
                  <span className="rounded-full bg-amber-950 px-2 py-0.5 text-xs text-amber-400">
                    {anomalies.high_severity_count} high
                  </span>
                )}
              </div>
              <div className="flex items-center gap-2">
                <select value={anomalyCol} onChange={e => setAnomalyCol(e.target.value)}
                  className="rounded-lg border border-zinc-800 bg-zinc-900 px-3 py-1.5 text-xs text-zinc-300 outline-none focus:border-amber-600">
                  {numericCols.map(c => <option key={c.name} value={c.name}>{c.name}</option>)}
                </select>
                <button onClick={runAnomalies} disabled={anomaliesLoading}
                  className="flex items-center gap-1 rounded-lg bg-amber-600 px-3 py-1.5 text-xs font-medium hover:bg-amber-500 disabled:opacity-50">
                  {anomaliesLoading ? <Loader2 className="h-3 w-3 animate-spin" /> : <AlertTriangle className="h-3 w-3" />}
                  Detect
                </button>
              </div>
            </div>

            {anomaliesLoading ? (
              <div className="h-48 animate-pulse rounded-xl bg-zinc-800/50" />
            ) : anomalies && anomalies.anomalies.length > 0 ? (
              <div className="space-y-2 max-h-80 overflow-y-auto">
                <div className="flex items-center gap-2 mb-2 text-xs text-zinc-500">
                  <span>{anomalies.summary}</span>
                </div>
                {anomalies.anomalies.map((a, i) => (
                  <AnomalyCard key={i} anomaly={a} />
                ))}
              </div>
            ) : anomalies && anomalies.anomalies.length === 0 ? (
              <p className="text-sm text-zinc-500 text-center py-8">{anomalies.summary || "No anomalies detected."}</p>
            ) : (
              <p className="text-sm text-zinc-600 text-center py-8">Run anomaly detection on a numeric column.</p>
            )}
          </div>

          {/* SECTION 3: Risk Scorecard */}
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Shield className="h-5 w-5 text-red-400" />
                <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Risk Scorecard</h2>
              </div>
              <button onClick={runRisk} disabled={riskLoading}
                className="flex items-center gap-1 rounded-lg bg-zinc-700 px-3 py-1.5 text-xs font-medium hover:bg-zinc-600 disabled:opacity-50">
                {riskLoading ? <Loader2 className="h-3 w-3 animate-spin" /> : <Shield className="h-3 w-3" />}
                Refresh
              </button>
            </div>

            {riskLoading ? (
              <div className="h-48 animate-pulse rounded-xl bg-zinc-800/50" />
            ) : risk ? (
              <div className="space-y-4">
                <div className="flex items-center gap-4 p-4 rounded-xl border border-zinc-800 bg-zinc-900/70">
                  <div className="shrink-0">
                    <div className={`h-20 w-20 rounded-full flex items-center justify-center text-2xl font-bold border-4 ${
                      risk.overall_score >= 70 ? "border-red-500 text-red-400 bg-red-950/30" :
                      risk.overall_score >= 40 ? "border-amber-500 text-amber-400 bg-amber-950/30" :
                      "border-emerald-500 text-emerald-400 bg-emerald-950/30"
                    }`}>
                      {risk.overall_score}
                    </div>
                  </div>
                  <div>
                    <p className="text-lg font-semibold text-zinc-200 capitalize">{risk.overall_level} Risk</p>
                    <p className="text-xs text-zinc-400 mt-1">{risk.overall_explanation}</p>
                  </div>
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                  {risk.categories.map((cat, i) => (
                    <RiskCategoryCard key={i} category={cat} />
                  ))}
                </div>
              </div>
            ) : (
              <p className="text-sm text-zinc-600 text-center py-12">Run risk scoring on this dataset.</p>
            )}
          </div>

          {/* SECTION 4: AI Recommendations Panel */}
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Lightbulb className="h-5 w-5 text-purple-400" />
                <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">AI Recommendations Panel</h2>
                {recommendations && recommendations.total_count > 0 && (
                  <span className="rounded-full bg-purple-950 px-2 py-0.5 text-xs text-purple-400">
                    {recommendations.high_priority_count} high priority
                  </span>
                )}
              </div>
              <button onClick={runRecommendations} disabled={recommendationsLoading}
                className="flex items-center gap-1 rounded-lg bg-purple-600 px-3 py-1.5 text-xs font-medium hover:bg-purple-500 disabled:opacity-50">
                {recommendationsLoading ? <Loader2 className="h-3 w-3 animate-spin" /> : <Lightbulb className="h-3 w-3" />}
                Generate
              </button>
            </div>

            {recommendationsLoading ? (
              <div className="h-48 animate-pulse rounded-xl bg-zinc-800/50" />
            ) : recommendations && recommendations.recommendations.length > 0 ? (
              <div className="space-y-3">
                {recommendations.recommendations.map((rec, i) => (
                  <RecommendationCard key={i} rec={rec} />
                ))}
              </div>
            ) : (
              <p className="text-sm text-zinc-600 text-center py-12">Generate AI-powered recommendations.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function ForecastChart({ data }: { data: ForecastResponse }) {
  const allPoints = [...data.historical, ...data.forecast];
  if (allPoints.length === 0) return <div className="h-64 rounded-lg bg-zinc-800/50" />;

  const values = allPoints.map(p => p.value);
  const lowers = allPoints.map(p => p.lower_bound);
  const uppers = allPoints.map(p => p.upper_bound);
  const maxVal = Math.max(...uppers, 1);
  const minVal = Math.min(...lowers, 0);
  const range = maxVal - minVal || 1;

  const hCount = data.historical.length;
  const fCount = data.forecast.length;
  const total = hCount + fCount;
  const barW = Math.max(4, Math.min(12, 600 / total));

  return (
    <div className="relative h-64 overflow-x-auto">
      <svg viewBox={`0 0 ${total * barW + 40} 260`} className="h-full w-full">
        <line x1={hCount * barW + 20} y1={10} x2={hCount * barW + 20} y2={230} stroke="#52525b" strokeWidth={1} strokeDasharray="4" />
        <text x={hCount * barW + 22} y={20} fill="#a1a1aa" fontSize={10}>Forecast →</text>

        {allPoints.map((p, i) => {
          const x = i * barW + 20;
          const yVal = 230 - ((p.value - minVal) / range) * 200;
          const yLow = 230 - ((p.lower_bound - minVal) / range) * 200;
          const yHigh = 230 - ((p.upper_bound - minVal) / range) * 200;
          const isForecast = i >= hCount;
          return (
            <g key={i}>
              <rect x={x} y={yLow} width={barW} height={yHigh - yLow} fill={isForecast ? "rgba(139, 92, 246, 0.15)" : "rgba(99, 102, 241, 0.08)"} rx={1} />
              <line x1={x + barW / 2} y1={yVal} x2={x + barW / 2} y2={yVal} stroke={isForecast ? "#a78bfa" : "#6366f1"} strokeWidth={barW > 6 ? 2 : 1} />
            </g>
          );
        })}

        {[0, hCount - 1, hCount, total - 1].filter(i => i >= 0 && i < allPoints.length).map(i => {
          const x = i * barW + 20;
          const label = i === 0 ? "Start" : i === hCount - 1 ? "Now" : i === hCount ? "Day 1" : `Day ${i + 1}`;
          return <text key={i} x={x} y={248} fill="#71717a" fontSize={9} transform={`rotate(-30, ${x}, 248)`}>{label}</text>;
        })}
      </svg>
    </div>
  );
}

function AnomalyCard({ anomaly }: { anomaly: AnomalyItem }) {
  const severityColors: Record<string, string> = {
    high: "border-red-800/30 bg-red-950/20 text-red-400",
    medium: "border-amber-800/30 bg-amber-950/20 text-amber-400",
    low: "border-blue-800/30 bg-blue-950/20 text-blue-400",
  };
  const severityDots: Record<string, string> = {
    high: "bg-red-500",
    medium: "bg-amber-500",
    low: "bg-blue-500",
  };

  return (
    <div className={`rounded-lg border p-3 ${severityColors[anomaly.severity] || severityColors.low}`}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <span className={`mt-1 h-2 w-2 shrink-0 rounded-full ${severityDots[anomaly.severity] || severityDots.low}`} />
          <div className="min-w-0">
            <div className="flex items-center gap-2">
              <span className="text-xs font-medium capitalize">{anomaly.type}</span>
              <span className={`rounded px-1.5 py-0.5 text-[10px] font-medium uppercase ${
                anomaly.severity === "high" ? "bg-red-900/50 text-red-300" :
                anomaly.severity === "medium" ? "bg-amber-900/50 text-amber-300" :
                "bg-blue-900/50 text-blue-300"
              }`}>{anomaly.severity}</span>
              <span className="text-[10px] text-zinc-500">Index {anomaly.index}</span>
            </div>
            <p className="text-xs mt-0.5 leading-relaxed opacity-80">{anomaly.explanation}</p>
          </div>
        </div>
        <div className="shrink-0 text-right text-xs">
          <p className="text-zinc-400">Value: <span className="font-semibold text-zinc-200">{anomaly.value}</span></p>
          <p className="text-zinc-500">Expected: {anomaly.expected.toFixed(1)}</p>
          <p className="text-zinc-500">Dev: {anomaly.deviation.toFixed(1)}%</p>
        </div>
      </div>
    </div>
  );
}

const riskIcons: Record<string, React.ElementType> = {
  "Financial Risk": DollarSign,
  "Operational Risk": Clock,
  "Data Quality Risk": Database,
  "Performance Risk": TrendingUp,
};

function RiskCategoryCard({ category }: { category: RiskCategory }) {
  const Icon = riskIcons[category.name] || Shield;
  const levelColors: Record<string, string> = {
    critical: "border-red-800/30 bg-red-950/20",
    high: "border-red-800/20 bg-red-950/10",
    moderate: "border-amber-800/30 bg-amber-950/20",
    low: "border-emerald-800/30 bg-emerald-950/20",
  };
  const textColors: Record<string, string> = {
    critical: "text-red-400",
    high: "text-red-300",
    moderate: "text-amber-400",
    low: "text-emerald-400",
  };

  return (
    <div className={`rounded-lg border p-3 ${levelColors[category.level] || "border-zinc-800"}`}>
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-1.5 text-xs font-medium uppercase tracking-wider text-zinc-500">
          <Icon className="h-3.5 w-3.5" />
          {category.name}
        </div>
        <div className="flex items-center gap-2">
          <span className={`text-lg font-bold ${textColors[category.level] || "text-zinc-300"}`}>{category.score}</span>
          <span className="text-[10px] text-zinc-600">/100</span>
        </div>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-zinc-800 mb-2">
        <div className={`h-full rounded-full ${
          category.score >= 70 ? "bg-red-500" : category.score >= 40 ? "bg-amber-500" : "bg-emerald-500"
        }`} style={{ width: `${category.score}%` }} />
      </div>
      <p className="text-[11px] text-zinc-400 mb-1">{category.explanation}</p>
      {category.mitigations.length > 0 && (
        <ul className="space-y-0.5">
          {category.mitigations.map((m, i) => (
            <li key={i} className="flex gap-1.5 text-[10px] text-zinc-500">
              <span className="mt-1 h-1 w-1 shrink-0 rounded-full bg-zinc-600" />
              {m}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

const categoryColors: Record<string, string> = {
  "Revenue Growth": "border-emerald-800/30 bg-emerald-950/20 text-emerald-400",
  "Cost Optimization": "border-blue-800/30 bg-blue-950/20 text-blue-400",
  "Operational Efficiency": "border-violet-800/30 bg-violet-950/20 text-violet-400",
  "Risk Reduction": "border-red-800/30 bg-red-950/20 text-red-400",
  "Strategic Opportunities": "border-purple-800/30 bg-purple-950/20 text-purple-400",
};

const impactColors: Record<string, string> = {
  high: "bg-red-900/50 text-red-300",
  medium: "bg-amber-900/50 text-amber-300",
  low: "bg-blue-900/50 text-blue-300",
};

function RecommendationCard({ rec }: { rec: RecommendationItem }) {
  return (
    <div className={`rounded-lg border p-3 ${categoryColors[rec.category] || "border-zinc-800 bg-zinc-900/50"}`}>
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs font-semibold">{rec.title}</span>
            <span className="rounded px-1.5 py-0.5 text-[10px] font-medium bg-zinc-800 text-zinc-400 uppercase">
              {rec.category}
            </span>
          </div>
          <p className="text-xs text-zinc-400 mt-1">{rec.description}</p>
        </div>
        <div className="shrink-0 text-right space-y-1">
          <div className="flex gap-1 justify-end">
            <span className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${impactColors[rec.impact] || "bg-zinc-800 text-zinc-400"}`}>
              {rec.impact}
            </span>
            <span className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${impactColors[rec.urgency] || "bg-zinc-800 text-zinc-400"}`}>
              {rec.urgency}
            </span>
          </div>
          <p className="text-[10px] text-zinc-600">{(rec.confidence * 100).toFixed(0)}% conf.</p>
        </div>
      </div>
    </div>
  );
}
