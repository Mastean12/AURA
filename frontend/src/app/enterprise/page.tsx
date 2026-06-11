"use client";

import { useState, useEffect } from "react";
import {
  Building2, FileText, Layers, GitCompare, Bot, Briefcase,
  Loader2, Download, Lightbulb, AlertTriangle, Target, TrendingUp,
  Shield, ChevronDown,
} from "lucide-react";
import {
  listDocuments, getIndustryDashboard, getMultiDocumentAnalysis,
  getComparison, getAutonomousAnalysis, getExecutiveBriefing,
} from "@/lib/api";
import type {
  DocumentResponse, IndustryDashboardResponse, MultiDocumentResponse,
  ComparisonResponse, AutonomousAnalysisResponse, ExecutiveBriefingResponse,
} from "@/types";

export default function EnterprisePage() {
  const [docs, setDocs] = useState<DocumentResponse[]>([]);
  const [fetched, setFetched] = useState(false);

  const [selectedDoc, setSelectedDoc] = useState<number | null>(null);
  const [industry, setIndustry] = useState<IndustryDashboardResponse | null>(null);
  const [industryLoading, setIndustryLoading] = useState(false);

  const [multiDocIds, setMultiDocIds] = useState<number[]>([]);
  const [multiResult, setMultiResult] = useState<MultiDocumentResponse | null>(null);
  const [multiLoading, setMultiLoading] = useState(false);

  const [compA, setCompA] = useState<number | null>(null);
  const [compB, setCompB] = useState<number | null>(null);
  const [compResult, setCompResult] = useState<ComparisonResponse | null>(null);
  const [compLoading, setCompLoading] = useState(false);

  const [autoDocIds, setAutoDocIds] = useState<number[]>([]);
  const [autoAnalysis, setAutoAnalysis] = useState<AutonomousAnalysisResponse | null>(null);
  const [autoLoading, setAutoLoading] = useState(false);

  const [briefing, setBriefing] = useState<ExecutiveBriefingResponse | null>(null);
  const [briefingLoading, setBriefingLoading] = useState(false);

  useEffect(() => {
    if (!fetched) listDocuments().then(setDocs).finally(() => setFetched(true));
  }, []);

  function toggleMultiDoc(id: number) {
    setMultiDocIds(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  }

  function toggleAutoDoc(id: number) {
    setAutoDocIds(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  }

  async function runIndustry() {
    if (!selectedDoc) return;
    setIndustryLoading(true);
    try { setIndustry(await getIndustryDashboard(selectedDoc)); } finally { setIndustryLoading(false); }
  }

  async function runMultiDocument() {
    if (multiDocIds.length < 2) return;
    setMultiLoading(true);
    try { setMultiResult(await getMultiDocumentAnalysis(multiDocIds)); } finally { setMultiLoading(false); }
  }

  async function runComparison() {
    if (!compA || !compB) return;
    setCompLoading(true);
    try {
      const labelA = docs.find(d => d.id === compA)?.title || "Doc A";
      const labelB = docs.find(d => d.id === compB)?.title || "Doc B";
      setCompResult(await getComparison(compA, compB, labelA, labelB));
    } finally { setCompLoading(false); }
  }

  async function runAutonomous() {
    if (autoDocIds.length < 1) return;
    setAutoLoading(true);
    try { setAutoAnalysis(await getAutonomousAnalysis(autoDocIds)); } finally { setAutoLoading(false); }
  }

  async function runBriefing() {
    if (!selectedDoc) return;
    setBriefingLoading(true);
    try { setBriefing(await getExecutiveBriefing(selectedDoc)); } finally { setBriefingLoading(false); }
  }

  // AI-powered analyses are triggered manually via the Generate buttons below

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Enterprise Intelligence</h1>
          <p className="text-sm text-zinc-500">Industry dashboards, multi-document intelligence, cross-doc comparison & autonomous analyst</p>
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
        {!fetched && <div className="h-10 w-40 animate-pulse rounded-xl bg-zinc-800" />}
      </div>

      {selectedDoc && (
        <div className="space-y-6">
          {/* Executive Briefing */}
          {briefingLoading ? (
            <div className="h-40 animate-pulse rounded-xl bg-zinc-800/50" />
          ) : briefing && (
            <div className="rounded-xl border border-blue-900/30 bg-blue-950/20 p-5">
              <div className="flex items-center gap-2 mb-3">
                <Briefcase className="h-5 w-5 text-blue-400" />
                <h2 className="text-sm font-medium uppercase tracking-wider text-blue-400">Executive Briefing</h2>
                <span className="ml-auto rounded-full bg-blue-950 px-2 py-0.5 text-xs text-blue-400">
                  {Math.round(briefing.confidence * 100)}% confidence
                </span>
              </div>
              <p className="text-sm leading-relaxed text-zinc-200 mb-3">{briefing.summary}</p>
              <p className="text-xs text-zinc-400 mb-3">{briefing.business_health}</p>
              <div className="grid gap-4 sm:grid-cols-2">
                <div>
                  <p className="text-xs font-medium uppercase tracking-wider text-red-400 mb-1">Critical Risks</p>
                  <ul className="space-y-1">
                    {briefing.critical_risks.map((r, i) => (
                      <li key={i} className="flex gap-1.5 text-xs text-zinc-300"><span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-red-500" />{r}</li>
                    ))}
                    {briefing.critical_risks.length === 0 && <li className="text-xs text-zinc-500">No critical risks identified.</li>}
                  </ul>
                </div>
                <div>
                  <p className="text-xs font-medium uppercase tracking-wider text-emerald-400 mb-1">Growth Opportunities</p>
                  <ul className="space-y-1">
                    {briefing.growth_opportunities.map((o, i) => (
                      <li key={i} className="flex gap-1.5 text-xs text-zinc-300"><span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-500" />{o}</li>
                    ))}
                    {briefing.growth_opportunities.length === 0 && <li className="text-xs text-zinc-500">No opportunities identified.</li>}
                  </ul>
                </div>
              </div>
              {briefing.forecast_outlook && (
                <p className="mt-3 text-xs text-zinc-400">{briefing.forecast_outlook}</p>
              )}
              {briefing.recommended_actions.length > 0 && (
                <div className="mt-3">
                  <p className="text-xs font-medium uppercase tracking-wider text-purple-400 mb-1">Recommended Actions</p>
                  <ul className="space-y-1">
                    {briefing.recommended_actions.map((a, i) => (
                      <li key={i} className="flex gap-1.5 text-xs text-zinc-300"><span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-purple-500" />{a}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Industry Intelligence */}
          {industryLoading ? (
            <div className="h-32 animate-pulse rounded-xl bg-zinc-800/50" />
          ) : industry && (
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
              <div className="flex items-center gap-2 mb-3">
                <Building2 className="h-5 w-5 text-emerald-400" />
                <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Industry Intelligence Dashboard</h2>
                <span className="ml-auto rounded-full bg-emerald-950 px-2 py-0.5 text-xs text-emerald-400">
                  {industry.detected_industry}
                </span>
              </div>
              <p className="text-sm text-zinc-300 mb-4">{industry.industry_summary}</p>
              {industry.industry_kpis.length > 0 && (
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4 mb-4">
                  {industry.industry_kpis.map((kpi, i) => (
                    <div key={i} className="rounded-lg border border-zinc-800 bg-zinc-900/70 p-3">
                      <p className="text-[10px] uppercase tracking-wider text-zinc-500">{kpi.label}</p>
                      <p className="mt-1 text-lg font-semibold text-zinc-200">{kpi.value}</p>
                      <p className="text-[10px] text-zinc-600">{kpi.column}</p>
                    </div>
                  ))}
                </div>
              )}
              {industry.recommendations.length > 0 && (
                <div>
                  <p className="text-xs font-medium uppercase tracking-wider text-zinc-500 mb-1">Industry Recommendations</p>
                  <ul className="space-y-1">
                    {industry.recommendations.map((r, i) => (
                      <li key={i} className="flex gap-1.5 text-xs text-zinc-400"><span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-emerald-500" />{r}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Autonomous Analysis */}
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Bot className="h-5 w-5 text-purple-400" />
                <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Autonomous AI Analyst</h2>
              </div>
              <div className="flex items-center gap-2">
                <div className="flex flex-wrap gap-1 max-w-48">
                  {docs.slice(0, 6).map(d => (
                    <button key={d.id} onClick={() => toggleAutoDoc(d.id)}
                      className={`px-2 py-0.5 text-[10px] rounded ${
                        autoDocIds.includes(d.id) ? "bg-purple-600/30 text-purple-300" : "bg-zinc-800 text-zinc-500 hover:text-zinc-300"
                      }`}>
                      {d.title.slice(0, 12)}
                    </button>
                  ))}
                </div>
                <button onClick={runAutonomous} disabled={autoLoading || autoDocIds.length === 0}
                  className="flex items-center gap-1 rounded-lg bg-purple-600 px-3 py-1.5 text-xs font-medium hover:bg-purple-500 disabled:opacity-50">
                  {autoLoading ? <Loader2 className="h-3 w-3 animate-spin" /> : <Bot className="h-3 w-3" />}
                  Analyze
                </button>
              </div>
            </div>

            {autoLoading ? (
              <div className="h-48 animate-pulse rounded-xl bg-zinc-800/50" />
            ) : autoAnalysis ? (
              <div className="space-y-4">
                {/* Business Health */}
                <div className="flex items-center gap-4 p-3 rounded-lg border border-zinc-800 bg-zinc-900/70">
                  <div className={`h-14 w-14 rounded-full flex items-center justify-center text-lg font-bold border-2 ${
                    autoAnalysis.business_health.overall_score >= 70 ? "border-emerald-500 text-emerald-400 bg-emerald-950/30" :
                    autoAnalysis.business_health.overall_score >= 40 ? "border-amber-500 text-amber-400 bg-amber-950/30" :
                    "border-red-500 text-red-400 bg-red-950/30"
                  }`}>
                    {autoAnalysis.business_health.overall_score}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-zinc-200">Business Health: {autoAnalysis.business_health.label}</p>
                    <p className="text-xs text-zinc-500">Completeness: {autoAnalysis.business_health.completeness}% | Quality: {autoAnalysis.business_health.quality}%</p>
                  </div>
                  <span className="ml-auto text-xs text-zinc-500">{(autoAnalysis.overall_confidence * 100).toFixed(0)}% conf</span>
                </div>

                <div className="grid gap-4 sm:grid-cols-2">
                  {/* Top Risks */}
                  <div className="rounded-lg border border-red-800/30 bg-red-950/20 p-3">
                    <p className="text-xs font-medium uppercase tracking-wider text-red-400 mb-2">Top 5 Risks</p>
                    {autoAnalysis.top_risks.map((r, i) => (
                      <div key={i} className="mb-2 last:mb-0">
                        <div className="flex items-center gap-1.5 text-xs">
                          <span className={`h-1.5 w-1.5 rounded-full ${r.severity === "high" ? "bg-red-500" : "bg-amber-500"}`} />
                          <span className="text-zinc-300 font-medium">{r.title}</span>
                          <span className="ml-auto text-[10px] text-zinc-500 capitalize">{r.severity}</span>
                        </div>
                        <p className="text-[10px] text-zinc-500 ml-3">{r.mitigation}</p>
                      </div>
                    ))}
                    {autoAnalysis.top_risks.length === 0 && <p className="text-xs text-zinc-500">No risks identified.</p>}
                  </div>

                  {/* Top Opportunities */}
                  <div className="rounded-lg border border-emerald-800/30 bg-emerald-950/20 p-3">
                    <p className="text-xs font-medium uppercase tracking-wider text-emerald-400 mb-2">Top 5 Opportunities</p>
                    {autoAnalysis.top_opportunities.map((o, i) => (
                      <div key={i} className="mb-2 last:mb-0">
                        <div className="flex items-center gap-1.5 text-xs">
                          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
                          <span className="text-zinc-300">{o.title}</span>
                          <span className="ml-auto text-[10px] text-zinc-500 capitalize">{o.estimated_impact}</span>
                        </div>
                      </div>
                    ))}
                    {autoAnalysis.top_opportunities.length === 0 && <p className="text-xs text-zinc-500">No opportunities identified.</p>}
                  </div>
                </div>

                {/* Forecasts */}
                {autoAnalysis.forecasts.length > 0 && (
                  <div>
                    <p className="text-xs font-medium uppercase tracking-wider text-zinc-500 mb-2">Forecasts</p>
                    <div className="grid gap-2 sm:grid-cols-3">
                      {autoAnalysis.forecasts.map((f, i) => (
                        <div key={i} className="rounded-lg border border-zinc-800 bg-zinc-900/70 p-2 text-center">
                          <p className="text-[10px] text-zinc-500">{f.metric}</p>
                          <p className={`text-xs font-semibold ${
                            f.trend === "up" ? "text-emerald-400" : f.trend === "down" ? "text-red-400" : "text-zinc-300"
                          }`}>{f.trend} ({f.horizon})</p>
                          <p className="text-[10px] text-zinc-600">{(f.confidence * 100).toFixed(0)}%</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Strategic Recommendations */}
                {autoAnalysis.strategic_recommendations.length > 0 && (
                  <div>
                    <p className="text-xs font-medium uppercase tracking-wider text-purple-400 mb-2">Strategic Recommendations</p>
                    <div className="space-y-2">
                      {autoAnalysis.strategic_recommendations.map((r, i) => (
                        <div key={i} className="flex items-start gap-2 rounded-lg border border-zinc-800 bg-zinc-900/70 p-2">
                          <div className="min-w-0 flex-1">
                            <p className="text-xs font-medium text-zinc-200">{r.title}</p>
                            <p className="text-[10px] text-zinc-500">{r.expected_outcome}</p>
                          </div>
                          <div className="shrink-0 text-right text-[10px]">
                            <span className={`rounded px-1 py-0.5 font-medium ${
                              r.impact === "high" ? "bg-red-900/50 text-red-300" : "bg-amber-900/50 text-amber-300"
                            }`}>{r.impact}</span>
                            <p className="text-zinc-600 mt-0.5">{(r.confidence * 100).toFixed(0)}%</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-sm text-zinc-600 text-center py-8">Select documents and click Analyze for autonomous AI analysis.</p>
            )}
          </div>

          {/* Multi-Document Intelligence */}
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <Layers className="h-5 w-5 text-cyan-400" />
                <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Multi-Document Intelligence</h2>
              </div>
              <div className="flex items-center gap-2">
                <div className="flex flex-wrap gap-1 max-w-48">
                  {docs.map(d => (
                    <button key={d.id} onClick={() => toggleMultiDoc(d.id)}
                      className={`px-2 py-0.5 text-[10px] rounded ${
                        multiDocIds.includes(d.id) ? "bg-cyan-600/30 text-cyan-300" : "bg-zinc-800 text-zinc-500 hover:text-zinc-300"
                      }`}>
                      {d.title.slice(0, 12)}
                    </button>
                  ))}
                </div>
                <button onClick={runMultiDocument} disabled={multiLoading || multiDocIds.length < 2}
                  className="flex items-center gap-1 rounded-lg bg-cyan-600 px-3 py-1.5 text-xs font-medium hover:bg-cyan-500 disabled:opacity-50">
                  {multiLoading ? <Loader2 className="h-3 w-3 animate-spin" /> : <Layers className="h-3 w-3" />}
                  Analyze
                </button>
              </div>
            </div>

            {multiLoading ? (
              <div className="h-32 animate-pulse rounded-xl bg-zinc-800/50" />
            ) : multiResult ? (
              <div className="space-y-3">
                <p className="text-sm text-zinc-300">{multiResult.consolidated_summary}</p>
                <div className="grid gap-3 sm:grid-cols-3">
                  <div>
                    <p className="text-[10px] font-medium uppercase tracking-wider text-cyan-400 mb-1">Themes</p>
                    <ul className="space-y-0.5">
                      {multiResult.themes.map((t, i) => (
                        <li key={i} className="flex gap-1 text-xs text-zinc-400"><span className="mt-1 h-1 w-1 rounded-full bg-cyan-500 shrink-0" />{t}</li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <p className="text-[10px] font-medium uppercase tracking-wider text-amber-400 mb-1">Conflicts</p>
                    <ul className="space-y-0.5">
                      {multiResult.conflicts.map((c, i) => (
                        <li key={i} className="flex gap-1 text-xs text-zinc-400"><span className="mt-1 h-1 w-1 rounded-full bg-amber-500 shrink-0" />{c}</li>
                      ))}
                      {multiResult.conflicts.length === 0 && <li className="text-xs text-zinc-600">No conflicts detected.</li>}
                    </ul>
                  </div>
                  <div>
                    <p className="text-[10px] font-medium uppercase tracking-wider text-violet-400 mb-1">Cross-References</p>
                    <ul className="space-y-0.5">
                      {multiResult.cross_references.map((r, i) => (
                        <li key={i} className="flex gap-1 text-xs text-zinc-400"><span className="mt-1 h-1 w-1 rounded-full bg-violet-500 shrink-0" />{r}</li>
                      ))}
                      {multiResult.cross_references.length === 0 && <li className="text-xs text-zinc-600">No cross-references found.</li>}
                    </ul>
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-sm text-zinc-600 text-center py-8">Select 2+ documents for cross-document intelligence.</p>
            )}
          </div>

          {/* Cross-Document Comparison */}
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                <GitCompare className="h-5 w-5 text-orange-400" />
                <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Cross-Document Comparison</h2>
              </div>
              <div className="flex items-center gap-2">
                <select value={compA ?? ""} onChange={e => setCompA(Number(e.target.value) || null)}
                  className="rounded-lg border border-zinc-800 bg-zinc-900 px-2 py-1 text-xs text-zinc-300 outline-none focus:border-orange-600">
                  <option value="">Doc A</option>
                  {docs.map(d => <option key={d.id} value={d.id}>{d.title.slice(0, 20)}</option>)}
                </select>
                <span className="text-zinc-600 text-xs">vs</span>
                <select value={compB ?? ""} onChange={e => setCompB(Number(e.target.value) || null)}
                  className="rounded-lg border border-zinc-800 bg-zinc-900 px-2 py-1 text-xs text-zinc-300 outline-none focus:border-orange-600">
                  <option value="">Doc B</option>
                  {docs.map(d => <option key={d.id} value={d.id}>{d.title.slice(0, 20)}</option>)}
                </select>
                <button onClick={runComparison} disabled={compLoading || !compA || !compB}
                  className="flex items-center gap-1 rounded-lg bg-orange-600 px-3 py-1.5 text-xs font-medium hover:bg-orange-500 disabled:opacity-50">
                  {compLoading ? <Loader2 className="h-3 w-3 animate-spin" /> : <GitCompare className="h-3 w-3" />}
                  Compare
                </button>
              </div>
            </div>

            {compLoading ? (
              <div className="h-32 animate-pulse rounded-xl bg-zinc-800/50" />
            ) : compResult ? (
              <div className="space-y-3">
                <p className="text-sm text-zinc-300">{compResult.comparison_summary}</p>
                <div className="grid gap-3 sm:grid-cols-2">
                  <div>
                    <p className="text-[10px] font-medium uppercase tracking-wider text-emerald-400 mb-1">Similarities</p>
                    <ul className="space-y-0.5">
                      {compResult.similarities.map((s, i) => (
                        <li key={i} className="flex gap-1 text-xs text-zinc-400"><span className="mt-1 h-1 w-1 rounded-full bg-emerald-500 shrink-0" />{s}</li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <p className="text-[10px] font-medium uppercase tracking-wider text-red-400 mb-1">Differences</p>
                    <ul className="space-y-0.5">
                      {compResult.differences.map((d, i) => (
                        <li key={i} className="flex gap-1 text-xs text-zinc-400"><span className="mt-1 h-1 w-1 rounded-full bg-red-500 shrink-0" />{d}</li>
                      ))}
                    </ul>
                  </div>
                </div>
                {compResult.key_changes.length > 0 && (
                  <div>
                    <p className="text-[10px] font-medium uppercase tracking-wider text-amber-400 mb-1">Key Changes</p>
                    <ul className="space-y-0.5">
                      {compResult.key_changes.map((c, i) => (
                        <li key={i} className="flex gap-1 text-xs text-zinc-400"><span className="mt-1 h-1 w-1 rounded-full bg-amber-500 shrink-0" />{c}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {compResult.recommended_actions.length > 0 && (
                  <div>
                    <p className="text-[10px] font-medium uppercase tracking-wider text-purple-400 mb-1">Recommended Actions</p>
                    <ul className="space-y-0.5">
                      {compResult.recommended_actions.map((a, i) => (
                        <li key={i} className="flex gap-1 text-xs text-zinc-400"><span className="mt-1 h-1 w-1 rounded-full bg-purple-500 shrink-0" />{a}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-sm text-zinc-600 text-center py-8">Select two documents to compare.</p>
            )}
          </div>
        </div>
      )}

      {!selectedDoc && fetched && docs.length > 0 && (
        <p className="text-sm text-zinc-600 text-center py-12">Select a document above to start enterprise analysis.</p>
      )}
      {fetched && docs.length === 0 && (
        <p className="text-sm text-zinc-600 text-center py-12">Upload documents first from the Upload page.</p>
      )}
    </div>
  );
}
