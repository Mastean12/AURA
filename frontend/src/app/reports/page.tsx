"use client";

import { useState, useEffect } from "react";
import {
  FileText, Download, Loader2, ScrollText, Brain, Building2, Globe,
} from "lucide-react";
import { listDocuments, exportReport, getSummary } from "@/lib/api";
import type { DocumentResponse, SummaryResponse } from "@/types";

const REPORT_TYPES = [
  {
    id: "executive-briefing-pdf",
    label: "Executive Briefing",
    icon: ScrollText,
    desc: "2-5 page briefing for managers and directors",
    color: "text-emerald-400",
    border: "border-emerald-800/30",
    bg: "bg-emerald-950/20",
    activeBg: "bg-emerald-600/20",
  },
  {
    id: "board-report",
    label: "Board Report",
    icon: Building2,
    desc: "10-20 page comprehensive board report",
    color: "text-blue-400",
    border: "border-blue-800/30",
    bg: "bg-blue-950/20",
    activeBg: "bg-blue-600/20",
  },
  {
    id: "intelligence-report",
    label: "Intelligence Report",
    icon: Brain,
    desc: "Research-grade analysis for strategy teams",
    color: "text-purple-400",
    border: "border-purple-800/30",
    bg: "bg-purple-950/20",
    activeBg: "bg-purple-600/20",
  },
  {
    id: "analytics-export",
    label: "Analytics Export",
    icon: FileText,
    desc: "PDF export with charts and statistics",
    color: "text-zinc-400",
    border: "border-zinc-800",
    bg: "bg-zinc-900/50",
    activeBg: "bg-zinc-800",
  },
] as const;

type ReportType = (typeof REPORT_TYPES)[number]["id"];

export default function ReportsPage() {
  const [docs, setDocs] = useState<DocumentResponse[]>([]);
  const [reportType, setReportType] = useState<ReportType>("executive-briefing-pdf");
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [generating, setGenerating] = useState(false);
  const [fetched, setFetched] = useState(false);

  useEffect(() => { if (!fetched) listDocuments().then(setDocs).finally(() => setFetched(true)); }, []);

  function toggleDoc(id: number) {
    setSelectedIds(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]);
  }

  async function handleGenerate() {
    if (selectedIds.length === 0) return;
    setGenerating(true);
    try {
      let blob: Blob;
      if (reportType === "analytics-export") {
        blob = await exportReport(selectedIds[0]);
      } else {
        const url = `http://localhost:8000/api/v1/reports/${reportType}`;
        const res = await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ doc_ids: selectedIds, company_name: "" }),
        });
        if (!res.ok) throw new Error("Report generation failed");
        blob = await res.blob();
      }
      const dlUrl = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = dlUrl;
      a.download = `aura-${reportType}-${Date.now()}.pdf`;
      a.click();
      URL.revokeObjectURL(dlUrl);
    } catch (e) {
      console.error("Report failed:", e);
    } finally {
      setGenerating(false);
    }
  }

  const activeConfig = REPORT_TYPES.find(r => r.id === reportType)!;

  return (
    <div className="mx-auto max-w-5xl space-y-8 p-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Reports</h1>
        <p className="mt-1 text-sm text-zinc-500">
          Generate executive-grade intelligence reports and board-ready PDFs
        </p>
      </div>

      {/* Report type selector */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {REPORT_TYPES.map(({ id, label, icon: Icon, desc, border, bg, activeBg }) => (
          <button key={id} onClick={() => setReportType(id as ReportType)}
            className={`rounded-xl border p-4 text-left transition-colors ${
              reportType === id ? `${activeBg} ${border}` : "border-zinc-800 bg-zinc-900/50 hover:border-zinc-700"
            }`}>
            <Icon className={`h-5 w-5 ${reportType === id ? activeConfig.color : "text-zinc-500"}`} />
            <p className="mt-2 text-sm font-medium">{label}</p>
            <p className="mt-0.5 text-xs text-zinc-500">{desc}</p>
          </button>
        ))}
      </div>

      {/* Document selector */}
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-4">
        <p className="text-xs font-medium uppercase tracking-wider text-zinc-500 mb-2">
          Select documents {reportType === "analytics-export" ? "" : "(select 1+)"}
        </p>
        <div className="flex flex-wrap gap-2">
          {docs.map(d => (
            <button key={d.id} onClick={() => toggleDoc(d.id)}
              className={`rounded-xl border px-3 py-1.5 text-xs transition-colors ${
                selectedIds.includes(d.id) ? `${activeConfig.activeBg} ${activeConfig.border}` : "border-zinc-800 bg-zinc-900/50 text-zinc-400 hover:border-zinc-700"
              }`}>
              {d.title.slice(0, 30)}
            </button>
          ))}
        </div>
        <div className="mt-3 flex items-center gap-3">
          <button onClick={handleGenerate} disabled={generating || selectedIds.length === 0}
            className="flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-2 text-xs font-medium hover:bg-blue-500 disabled:opacity-50">
            {generating ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Download className="h-3.5 w-3.5" />}
            {generating ? "Generating..." : `Generate ${activeConfig.label}`}
          </button>
          {reportType === "analytics-export" && selectedIds.length > 0 && (
            <span className="text-xs text-zinc-600">Exporting analytics for doc #{selectedIds[0]}</span>
          )}
          {reportType !== "analytics-export" && selectedIds.length > 0 && (
            <span className="text-xs text-zinc-600">{selectedIds.length} document(s) selected</span>
          )}
        </div>
      </div>

      {/* Info */}
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 p-5">
        <h3 className="text-sm font-medium text-zinc-200 mb-2">About {activeConfig.label}</h3>
        <div className="space-y-2 text-xs text-zinc-500">
          {reportType === "executive-briefing-pdf" && (
            <>
              <p>Length: 2-5 pages. Audience: Managers, Directors, Executives.</p>
              <p>Sections: Executive Summary, Business Health Score, Top Risks, Top Opportunities, Recommended Actions, Conclusion.</p>
            </>
          )}
          {reportType === "board-report" && (
            <>
              <p>Length: 10-20 pages. Audience: Board Members, Investors, NGO Leadership.</p>
              <p>Sections: Cover, TOC, Executive Summary, Health Assessment, KPI Dashboard, Risk Analysis, Opportunity Analysis, Forecasting, Strategic Recommendations, Scenario Analysis, Appendices.</p>
            </>
          )}
          {reportType === "intelligence-report" && (
            <>
              <p>Length: 8-15 pages. Audience: Researchers, Consultants, Strategy Teams.</p>
              <p>Sections: Executive Summary, Key Findings, Evidence Analysis, Comparative Analysis, Strategic Implications, Recommendations, Supporting Evidence.</p>
            </>
          )}
          {reportType === "analytics-export" && (
            <>
              <p>Length: varies. Audience: Technical teams, analysts.</p>
              <p>Sections: Cover, Executive Summary, Dataset Overview, Health, KPI Summary, Visualizations, Risks, Opportunities, Recommendations.</p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
