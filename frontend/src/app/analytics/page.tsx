"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import type React from "react";
import {
  Brain, Shield, BarChart3, PieChart, TrendingUp, MessageSquare,
  FileText, Download, Send, Loader2, Table, Hash, AlertTriangle,
  Layers, Lightbulb, Flag, Target, Bot, User, DollarSign, Users,
  Clock, TrendingDown, Building2, ShoppingCart, LineChart,
  ArrowUpRight, ArrowDownRight,
} from "lucide-react";
import {
  getAnalytics, listDocuments, getInsights, getDatasetHealth,
  getAllCharts, analyticsChat, exportReport, getExecutiveSummary,
  getKPIs, getChartInsight,
} from "@/lib/api";
import type {
  DocumentResponse, AnalyticsResponse, ChartsResponse,
  InsightsResponse, HealthResponse, AnalyticsChatResponse,
  ExecutiveSummaryResponse, KPIItem, KPIResponse, ChartInsightResponse,
} from "@/types";

export default function AnalyticsPage() {
  const [docs, setDocs] = useState<DocumentResponse[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<number | null>(null);
  const [analytics, setAnalytics] = useState<AnalyticsResponse | null>(null);
  const [charts, setCharts] = useState<ChartsResponse | null>(null);
  const [insights, setInsights] = useState<InsightsResponse | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [execSummary, setExecSummary] = useState<ExecutiveSummaryResponse | null>(null);
  const [kpis, setKpis] = useState<KPIItem[]>([]);
  const [chartInsights, setChartInsights] = useState<Record<string, string>>({});
  const [healthLoading, setHealthLoading] = useState(false);
  const [insightsLoading, setInsightsLoading] = useState(false);
  const [chartsLoading, setChartsLoading] = useState(false);
  const [execSummaryLoading, setExecSummaryLoading] = useState(false);
  const [kpisLoading, setKpisLoading] = useState(false);
  const [chartInsightsLoading, setChartInsightsLoading] = useState(false);
  const [fetched, setFetched] = useState(false);

  const [chatMessages, setChatMessages] = useState<{role:string;content:string}[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const chatSession = useRef("session-" + Math.random().toString(36).slice(2));
  const chatBottom = useRef<HTMLDivElement>(null);

  const [exporting, setExporting] = useState(false);

  useEffect(() => { if (!fetched) listDocuments().then(setDocs).finally(() => setFetched(true)); }, []);
  useEffect(() => { chatBottom.current?.scrollIntoView({ behavior: "smooth" }); }, [chatMessages]);

  async function loadChartInsights() {
    if (!charts || !selectedDoc) return;
    setChartInsightsLoading(true);
    setChartInsights({});
    const chartTypes = ["bar", "pie", "line", "area", "histogram", "distribution"];
    const results: Record<string, string> = {};
    for (const ct of chartTypes) {
      if (charts[ct as keyof ChartsResponse]) {
        try {
          const res = await getChartInsight(selectedDoc, ct, charts.column);
          results[ct] = res.insight;
        } catch {
          results[ct] = "Chart insight temporarily unavailable.";
        }
      }
    }
    setChartInsights(results);
    setChartInsightsLoading(false);
  }

  async function selectDocument(docId: number) {
    setSelectedDoc(docId);
    setAnalytics(null); setCharts(null); setInsights(null); setHealth(null);
    setExecSummary(null); setKpis([]); setChartInsights({});
    setChatMessages([]);
    const a = await getAnalytics(docId);
    setAnalytics(a);
    setHealthLoading(true); setChartsLoading(true); setKpisLoading(true);
    Promise.all([
      getDatasetHealth(docId).then(setHealth).finally(() => setHealthLoading(false)),
      getAllCharts(docId).then(setCharts).finally(() => setChartsLoading(false)),
      getKPIs(docId).then((r: KPIResponse) => setKpis(r.kpis)).finally(() => setKpisLoading(false)),
    ]);
  }

  async function analyzeInsights() {
    if (!selectedDoc) return;
    setInsightsLoading(true);
    try { setInsights(await getInsights(selectedDoc)); } finally { setInsightsLoading(false); }
  }

  async function analyzeExecutiveSummary() {
    if (!selectedDoc) return;
    setExecSummaryLoading(true);
    try { setExecSummary(await getExecutiveSummary(selectedDoc)); } finally { setExecSummaryLoading(false); }
  }

  async function analyzeChartInsights() {
    if (!charts || !selectedDoc) return;
    setChartInsightsLoading(true);
    setChartInsights({});
    const chartTypes = ["bar", "pie", "line", "area", "histogram", "distribution"];
    const results: Record<string, string> = {};
    for (const ct of chartTypes) {
      if (charts[ct as keyof ChartsResponse]) {
        try {
          const res = await getChartInsight(selectedDoc, ct, charts.column);
          results[ct] = res.insight;
        } catch {
          results[ct] = "Chart insight temporarily unavailable.";
        }
      }
    }
    setChartInsights(results);
    setChartInsightsLoading(false);
  }

  async function sendChat() {
    if (!chatInput.trim() || !selectedDoc || chatLoading) return;
    const q = chatInput;
    setChatInput("");
    setChatMessages(prev => [...prev, { role: "user", content: q }]);
    setChatLoading(true);
    try {
      const res = await analyticsChat(selectedDoc, q, chatSession.current);
      setChatMessages(prev => [...prev, { role: "assistant", content: res.answer }]);
    } catch {
      setChatMessages(prev => [...prev, { role: "assistant", content: "Error getting response." }]);
    } finally { setChatLoading(false); }
  }

  async function handleExport() {
    if (!selectedDoc) return;
    setExporting(true);
    try {
      const blob = await exportReport(selectedDoc);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = `aura-report-${selectedDoc}.pdf`; a.click();
      URL.revokeObjectURL(url);
    } finally { setExporting(false); }
  }

  const missingTotal = analytics?.columns.reduce((s, c) => s + c.missing, 0) ?? 0;
  const numericCount = analytics?.columns.filter(c => c.dtype === "numeric").length ?? 0;
  const catCount = analytics?.columns.filter(c => c.dtype === "categorical").length ?? 0;

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Analytics</h1>
          <p className="text-sm text-zinc-500">AI-powered executive intelligence platform</p>
        </div>
        <button onClick={handleExport} disabled={!selectedDoc || exporting}
          className="flex items-center gap-2 rounded-xl bg-blue-600 px-4 py-2 text-sm font-medium hover:bg-blue-500 disabled:opacity-50">
          {exporting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
          {exporting ? "Exporting..." : "Export Report"}
        </button>
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
          {/* SECTION 1: Executive Summary — manual trigger */}
          {execSummaryLoading ? (
            <div className="h-24 animate-pulse rounded-xl bg-zinc-800/50" />
          ) : execSummary ? (
            <div className="rounded-xl border border-emerald-900/30 bg-emerald-950/20 p-5">
              <div className="flex items-center gap-2 mb-3">
                <FileText className="h-5 w-5 text-emerald-400" />
                <h2 className="text-sm font-medium uppercase tracking-wider text-emerald-400">AURA Executive Summary</h2>
                <span className="ml-auto rounded-full bg-emerald-950 px-2 py-0.5 text-xs text-emerald-400">
                  {Math.round(execSummary.confidence * 100)}% confidence
                </span>
              </div>
              <p className="text-sm leading-relaxed text-zinc-200">{execSummary.summary}</p>
            </div>
          ) : (
            <button onClick={analyzeExecutiveSummary} className="flex items-center gap-2 rounded-xl border border-emerald-800/30 bg-emerald-950/20 px-5 py-4 text-sm text-emerald-400 hover:bg-emerald-950/40 w-full">
              <FileText className="h-5 w-5" />
              Generate Executive Summary
            </button>
          )}

          {/* SECTION 2: Business Health Score */}
          {healthLoading ? (
            <div className="h-32 animate-pulse rounded-xl bg-zinc-800/50" />
          ) : health && (
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Shield className="h-5 w-5 text-zinc-400" />
                  <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Business Health Score</h2>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`text-3xl font-bold ${
                    health.color === "green" ? "text-emerald-400" : health.color === "yellow" ? "text-amber-400" : "text-red-400"
                  }`}>{health.overall}<span className="text-lg text-zinc-600">/100</span></span>
                  <span className={`rounded-full px-3 py-1 text-xs font-medium ${
                    health.color === "green" ? "bg-emerald-950 text-emerald-400" : health.color === "yellow" ? "bg-amber-950 text-amber-400" : "bg-red-950 text-red-400"
                  }`}>{health.label}</span>
                </div>
              </div>
              <div className="mt-4 grid grid-cols-4 gap-4">
                {[
                  { label: "Completeness", value: health.completeness },
                  { label: "Quality", value: health.quality },
                  { label: "Consistency", value: health.consistency },
                  { label: "Missing Data", value: health.missing_data },
                ].map(m => (
                  <div key={m.label}>
                    <div className="flex justify-between text-xs text-zinc-500 mb-1">
                      <span>{m.label}</span><span>{m.value}%</span>
                    </div>
                    <div className="h-1.5 overflow-hidden rounded-full bg-zinc-800">
                      <div className={`h-full rounded-full transition-all ${
                        m.value >= 80 ? "bg-emerald-500" : m.value >= 50 ? "bg-amber-500" : "bg-red-500"
                      }`} style={{ width: `${m.value}%` }} />
                    </div>
                  </div>
                ))}
              </div>
              <p className="mt-3 text-xs text-zinc-500">{health.explanation}</p>
            </div>
          )}

          {/* SECTION 3: Smart KPI Cards */}
          {kpisLoading ? (
            <div className="h-24 animate-pulse rounded-xl bg-zinc-800/50" />
          ) : kpis.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-3">
                <BarChart3 className="h-5 w-5 text-zinc-400" />
                <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Smart KPI Cards</h2>
              </div>
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                {kpis.map((kpi, i) => (
                  <KPICard key={`${kpi.label}-${i}`} kpi={kpi} />
                ))}
              </div>
            </div>
          )}

          {/* SECTION 4: AURA Intelligence — manual trigger */}
          {insightsLoading ? (
            <div className="h-48 animate-pulse rounded-xl bg-zinc-800/50" />
          ) : insights ? (
            <div className="rounded-xl border border-blue-900/30 bg-blue-950/20 p-5">
              <div className="flex items-center gap-2 mb-4">
                <Brain className="h-5 w-5 text-blue-400" />
                <h2 className="text-sm font-medium uppercase tracking-wider text-blue-400">AURA Intelligence</h2>
                <span className="ml-auto rounded-full bg-blue-950 px-2 py-0.5 text-xs text-blue-400">
                  {insights.confidence_score}% confidence
                </span>
              </div>
              <p className="mb-4 text-sm leading-relaxed text-zinc-200">{insights.executive_summary}</p>
              <div className="grid gap-4 sm:grid-cols-2">
                <InsightCard icon={Lightbulb} title="Key Findings" items={insights.key_findings} color="emerald" />
                <InsightCard icon={AlertTriangle} title="Risks" items={insights.risks} color="red" />
                <InsightCard icon={Target} title="Opportunities" items={insights.opportunities} color="blue" />
                <InsightCard icon={Flag} title="Recommendations" items={insights.recommendations} color="purple" />
              </div>
            </div>
          ) : (
            <button onClick={analyzeInsights} className="flex items-center gap-2 rounded-xl border border-blue-900/30 bg-blue-950/20 px-5 py-4 text-sm text-blue-400 hover:bg-blue-950/40 w-full">
              <Brain className="h-5 w-5" />
              Analyze Intelligence (Findings, Risks, Opportunities)
            </button>
          )}

          {/* Basic KPI Cards (Rows, Columns, etc) */}
          {analytics && (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
              {[
                { label: "Rows", value: analytics.row_count, icon: Table, color: "text-blue-400", bg: "bg-blue-600/10" },
                { label: "Columns", value: analytics.column_count, icon: Hash, color: "text-emerald-400", bg: "bg-emerald-600/10" },
                { label: "Missing", value: missingTotal, icon: AlertTriangle, color: "text-amber-400", bg: "bg-amber-600/10" },
                { label: "Numeric", value: numericCount, icon: BarChart3, color: "text-purple-400", bg: "bg-purple-600/10" },
                { label: "Categories", value: catCount, icon: Layers, color: "text-cyan-400", bg: "bg-cyan-600/10" },
              ].map(k => (
                <div key={k.label} className={`rounded-xl border border-zinc-800 ${k.bg} p-4`}>
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium uppercase tracking-wider text-zinc-500">{k.label}</span>
                    <k.icon className={`h-4 w-4 ${k.color}`} />
                  </div>
                  <p className={`mt-2 text-2xl font-semibold ${k.color}`}>{k.value}</p>
                </div>
              ))}
            </div>
          )}

          {/* Column table */}
          {analytics && (
            <div className="overflow-x-auto rounded-xl border border-zinc-800">
              <table className="w-full text-left text-sm">
                <thead><tr className="border-b border-zinc-800 bg-zinc-900/70">
                  {["Name","Type","Total","Missing","Mean","Unique","Top"].map(h => (
                    <th key={h} className="px-4 py-3 font-medium text-zinc-400">{h}</th>
                  ))}
                </tr></thead>
                <tbody>
                  {analytics.columns.map(col => (
                    <tr key={col.name} className="border-b border-zinc-800/50 hover:bg-zinc-900/30">
                      <td className="px-4 py-3 font-medium">{col.name}</td>
                      <td className="px-4 py-3 text-zinc-400">{col.dtype}</td>
                      <td className="px-4 py-3">{col.total}</td>
                      <td className="px-4 py-3">{col.missing > 0 ? <span className="text-amber-400">{col.missing}</span> : col.missing}</td>
                      <td className="px-4 py-3">{col.numeric ? col.numeric.mean : "—"}</td>
                      <td className="px-4 py-3">{col.categorical ? (col.categorical.unique as number) : "—"}</td>
                      <td className="px-4 py-3 text-zinc-400">
                        {col.categorical ? ((col.categorical.top_values as {value:string}[])?.slice(0,2).map(t=>t.value).join(", ")) : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* SECTION 5: Visualizations */}
          {chartsLoading ? (
            <div className="h-64 animate-pulse rounded-xl bg-zinc-800/50" />
          ) : charts && (
            <div>
              <div className="mb-3 flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-zinc-400" />
                <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Visualizations</h2>
                <span className="text-xs text-zinc-600">— {charts.column}</span>
              </div>
              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                {[
                  { key: "bar", label: "Bar Chart", icon: BarChart3 },
                  { key: "pie", label: "Pie Chart", icon: PieChart },
                  { key: "line", label: "Line Chart", icon: TrendingUp },
                  { key: "area", label: "Area Chart", icon: TrendingUp },
                  { key: "histogram", label: "Histogram", icon: BarChart3 },
                  { key: "distribution", label: "Distribution", icon: BarChart3 },
                ].map(({ key, label, icon: Icon }) => (
                  charts[key as keyof typeof charts] ? (
                    <div key={key} className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4">
                      <h3 className="mb-2 flex items-center gap-1.5 text-xs font-medium uppercase tracking-wider text-zinc-500">
                        <Icon className="h-3.5 w-3.5" />{label}
                      </h3>
                      <ChartFrame data={charts[key as keyof typeof charts] as Record<string, unknown>} />
                    </div>
                  ) : null
                ))}
                {charts.correlation && (
                  <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4 sm:col-span-2 xl:col-span-3">
                    <h3 className="mb-2 flex items-center gap-1.5 text-xs font-medium uppercase tracking-wider text-zinc-500">
                      <BarChart3 className="h-3.5 w-3.5" />Correlation Heatmap
                    </h3>
                    <CorrelationFrame data={charts.correlation} />
                  </div>
                )}
              </div>
            </div>
          )}

          {/* SECTION 6: Chart Insight Cards — manual trigger */}
          {chartInsightsLoading ? (
            <div className="h-32 animate-pulse rounded-xl bg-zinc-800/50" />
          ) : Object.keys(chartInsights).length > 0 ? (
            <div>
              <div className="mb-3 flex items-center gap-2">
                <LineChart className="h-5 w-5 text-zinc-400" />
                <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Chart Insight Cards</h2>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                {Object.entries(chartInsights).map(([chartType, insight]) => (
                  <div key={chartType} className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <BarChart3 className="h-4 w-4 text-zinc-400" />
                      <h3 className="text-xs font-medium uppercase tracking-wider text-zinc-500">
                        {chartType.charAt(0).toUpperCase() + chartType.slice(1)} Insight
                      </h3>
                    </div>
                    <p className="text-xs leading-relaxed text-zinc-300">{insight}</p>
                  </div>
                ))}
              </div>
            </div>
          ) : charts && (
            <button onClick={analyzeChartInsights} disabled={!charts} className="flex items-center gap-2 rounded-xl border border-zinc-800 bg-zinc-900/50 px-5 py-4 text-sm text-zinc-400 hover:bg-zinc-800/70 w-full disabled:opacity-30">
              <LineChart className="h-5 w-5" />
              Generate Chart Insights
            </button>
          )}

          {/* SECTION 7: Analytics Assistant */}
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/40">
            <div className="flex items-center gap-2 border-b border-zinc-800 px-5 py-3">
              <MessageSquare className="h-4 w-4 text-zinc-400" />
              <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Analytics Assistant</h2>
              <span className="ml-auto text-xs text-zinc-600">Ask about this dataset</span>
            </div>
            <div className="h-64 space-y-3 overflow-y-auto p-4">
              {chatMessages.length === 0 && !chatLoading && (
                <div className="flex h-full items-center justify-center">
                  <div className="text-center">
                    <Bot className="mx-auto mb-2 h-8 w-8 text-zinc-700" />
                    <p className="text-sm text-zinc-600">Ask AURA about this dataset...</p>
                    <div className="mt-3 flex flex-wrap justify-center gap-2">
                      {[
                        "What are the biggest risks?",
                        "What trends do you see?",
                        "What should management do?",
                        "Which department performs best?",
                      ].map(q => (
                        <button key={q} onClick={() => { setChatInput(q); }}
                          className="rounded-full border border-zinc-800 px-3 py-1 text-xs text-zinc-500 hover:border-zinc-600">
                          {q}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )}
              {chatMessages.map((m, i) => (
                <div key={i} className={`flex gap-2 ${m.role === "user" ? "justify-end" : ""}`}>
                  {m.role === "assistant" && <Bot className="mt-1 h-6 w-6 shrink-0 text-blue-400" />}
                  <div className={`max-w-[80%] rounded-xl px-3 py-2 text-sm ${
                    m.role === "user" ? "bg-blue-600 text-white" : "bg-zinc-800 text-zinc-200"
                  }`}>{m.content}</div>
                  {m.role === "user" && <User className="mt-1 h-6 w-6 shrink-0 text-zinc-500" />}
                </div>
              ))}
              {chatLoading && (
                <div className="flex gap-2">
                  <Bot className="mt-1 h-6 w-6 shrink-0 text-blue-400" />
                  <div className="rounded-xl bg-zinc-800 px-3 py-2 text-sm text-zinc-400"><span className="animate-pulse">Thinking...</span></div>
                </div>
              )}
              <div ref={chatBottom} />
            </div>
            <div className="flex gap-2 border-t border-zinc-800 p-3">
              <input value={chatInput} onChange={e => setChatInput(e.target.value)}
                onKeyDown={e => e.key === "Enter" && !e.shiftKey && (e.preventDefault(), sendChat())}
                placeholder="Ask about this dataset..." className="flex-1 rounded-lg border border-zinc-800 bg-zinc-900/70 px-3 py-2 text-sm text-zinc-100 placeholder-zinc-600 outline-none focus:border-blue-600" />
              <button onClick={sendChat} disabled={!chatInput.trim() || chatLoading}
                className="flex h-9 w-9 items-center justify-center rounded-lg bg-blue-600 text-white hover:bg-blue-500 disabled:opacity-30">
                <Send className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function KPICard({ kpi }: { kpi: KPIItem }) {
  const colorMap: Record<string, string> = {
    Finance: "text-emerald-400 bg-emerald-600/10 border-emerald-800/30",
    Sales: "text-blue-400 bg-blue-600/10 border-blue-800/30",
    HR: "text-purple-400 bg-purple-600/10 border-purple-800/30",
    Operations: "text-amber-400 bg-amber-600/10 border-amber-800/30",
  };
  const iconMap: Record<string, React.ElementType> = {
    Finance: DollarSign,
    Sales: ShoppingCart,
    HR: Users,
    Operations: Clock,
  };
  const Icon = iconMap[kpi.category] || BarChart3;
  const colorClass = colorMap[kpi.category] || "text-zinc-400 bg-zinc-600/10 border-zinc-800/30";

  return (
    <div className={`rounded-xl border p-4 ${colorClass}`}>
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs font-medium uppercase tracking-wider opacity-70">{kpi.category}</span>
        <Icon className="h-4 w-4" />
      </div>
      <p className="text-xs text-zinc-500">{kpi.label}</p>
      <p className="mt-1 text-xl font-semibold">{kpi.value}</p>
      {kpi.change !== null && (
        <div className={`mt-1 flex items-center gap-1 text-xs ${
          kpi.change >= 0 ? "text-emerald-400" : "text-red-400"
        }`}>
          {kpi.change >= 0 ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}
          {Math.abs(kpi.change).toFixed(1)}%
        </div>
      )}
    </div>
  );
}

function InsightCard({ icon: Icon, title, items, color }: { icon: React.ElementType; title: string; items: string[]; color: string }) {
  const colors: Record<string, string> = { emerald: "text-emerald-400 border-emerald-800/30 bg-emerald-950/20", red: "text-red-400 border-red-800/30 bg-red-950/20", blue: "text-blue-400 border-blue-800/30 bg-blue-950/20", purple: "text-purple-400 border-purple-800/30 bg-purple-950/20" };
  const dotColors: Record<string, string> = { emerald: "bg-emerald-500", red: "bg-red-500", blue: "bg-blue-500", purple: "bg-purple-500" };
  if (!items.length) return null;
  return (
    <div className={`rounded-lg border p-3 ${colors[color] || ""}`}>
      <div className="mb-2 flex items-center gap-1.5 text-xs font-medium uppercase tracking-wider">
        <Icon className="h-3.5 w-3.5" />{title}
      </div>
      <ul className="space-y-1">
        {items.map((item, i) => (
          <li key={i} className="flex gap-2 text-xs">
            <span className={`mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full ${dotColors[color] || "bg-zinc-500"}`} />
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}

function ChartFrame({ data }: { data: Record<string, unknown> | undefined }) {
  if (!data) return <div className="h-32 rounded-lg bg-zinc-900/70" />;
  const plotlyData = (data.data as Record<string, unknown>[]);
  if (!plotlyData?.length) return <div className="h-32 rounded-lg bg-zinc-900/70" />;
  const trace = plotlyData[0];
  const type = trace?.type as string;
  const labels = (trace?.labels as string[]) ?? (trace?.x as string[]) ?? [];
  const values = (trace?.values as number[]) ?? (trace?.y as number[]) ?? [];
  if (!labels.length && !values.length) return <div className="h-32 rounded-lg bg-zinc-900/70" />;
  const maxVal = Math.max(...values, 1);
  const colors = ["#636efa", "#ef553b", "#00cc96", "#ab63fa", "#ffa15a", "#19d3f3"];

  if (type === "pie") {
    const total = values.reduce((a, b) => a + b, 0);
    return (
      <div className="flex flex-wrap items-center justify-center gap-3 py-2">
        {labels.slice(0, 8).map((l, i) => (
          <div key={l} className="flex items-center gap-1.5 text-xs">
            <span className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: colors[i % colors.length] }} />
            <span className="text-zinc-300">{l}</span>
            <span className="text-zinc-500">{((values[i] / total) * 100).toFixed(0)}%</span>
          </div>
        ))}
      </div>
    );
  }

  if (type === "heatmap") return <HeatmapFrame data={data} />;

  return (
    <div className="space-y-1 py-1">
      {labels.slice(0, 10).map((l, i) => (
        <div key={l} className="flex items-center gap-2 text-xs">
          <span className="w-16 truncate text-zinc-400">{l}</span>
          <div className="flex-1 overflow-hidden rounded-full bg-zinc-800">
            <div className="h-2 rounded-full" style={{ width: `${(values[i] / maxVal) * 100}%`, backgroundColor: colors[i % colors.length] }} />
          </div>
          <span className="w-8 text-right text-zinc-300">{values[i]}</span>
        </div>
      ))}
    </div>
  );
}

function HeatmapFrame({ data }: { data: Record<string, unknown> }) {
  const trace = (data.data as Record<string, unknown>[])?.[0];
  const z = trace?.z as number[][];
  const x = trace?.x as string[];
  const y = trace?.y as string[];
  if (!z?.length) return <div className="h-32 rounded-lg bg-zinc-900/70" />;
  return (
    <div className="overflow-x-auto">
      <table className="mx-auto text-xs">
        <thead><tr>
          <th />
          {x?.map(h => <th key={h} className="px-2 py-1 text-zinc-500">{h}</th>)}
        </tr></thead>
        <tbody>
          {z.map((row, i) => (
            <tr key={i}>
              <td className="pr-2 text-zinc-500">{y?.[i]}</td>
              {row.map((v, j) => (
                <td key={j} className="px-2 py-1 text-center font-medium"
                  style={{ backgroundColor: v >= 0.7 ? "#ef553b" : v >= 0.4 ? "#fdae61" : v >= 0.1 ? "#e0f3f8" : "#abd9e9",
                           color: v >= 0.4 ? "white" : "black" }}>
                  {v.toFixed(2)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function CorrelationFrame({ data }: { data: Record<string, unknown> }) {
  return <HeatmapFrame data={data} />;
}
