"use client";

import { useState, useEffect } from "react";
import {
  FileText,
  ScrollText,
  Lightbulb,
  ListChecks,
  ShieldAlert,
  Download,
  Loader2,
} from "lucide-react";
import { getSummary, listDocuments, exportReport } from "@/lib/api";
import type { DocumentResponse, SummaryResponse } from "@/types";

const SUMMARY_TYPES = [
  { id: 1, label: "Executive Summary", icon: ScrollText, desc: "High-level overview" },
  { id: 2, label: "Key Findings", icon: ListChecks, desc: "Important discoveries" },
  { id: 3, label: "Recommendations", icon: Lightbulb, desc: "Actionable suggestions" },
  { id: 4, label: "Risks", icon: ShieldAlert, desc: "Potential issues" },
] as const;

export default function ReportsPage() {
  const [docs, setDocs] = useState<DocumentResponse[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<DocumentResponse | null>(null);
  const [summaryType, setSummaryType] = useState<number>(1);
  const [result, setResult] = useState<SummaryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [fetched, setFetched] = useState(false);

  useEffect(() => {
    if (!fetched) listDocuments().then(setDocs).finally(() => setFetched(true));
  }, []);

  async function generate() {
    if (!selectedDoc) return;
    setLoading(true);
    setResult(null);
    try {
      const data = await getSummary(selectedDoc.id, summaryType);
      setResult(data);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }

  async function handleExport() {
    if (!selectedDoc) return;
    setExporting(true);
    try {
      const blob = await exportReport(selectedDoc.id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `aura-report-${selectedDoc.id}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      // ignore
    } finally {
      setExporting(false);
    }
  }

  function renderContent() {
    if (!result || !result.content.length) return null;
    const item = result.content[0] as Record<string, unknown>;

    if (summaryType === 1) {
      const title = item.title as string | undefined;
      const summary = item.summary as string | undefined;
      const key_points = item.key_points as string[] | undefined;
      return (
        <div className="space-y-4">
          {title && <h3 className="text-lg font-medium">{title}</h3>}
          {summary && <p className="text-sm leading-relaxed text-zinc-300">{summary}</p>}
          {Array.isArray(key_points) && (
            <ul className="space-y-1">
              {key_points.map((p, i) => (
                <li key={i} className="flex gap-2 text-sm text-zinc-400">
                  <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-blue-400" />
                  {p}
                </li>
              ))}
            </ul>
          )}
        </div>
      );
    }

    if (summaryType === 2) {
      const findings = item.findings as Record<string, string>[] | undefined;
      if (!Array.isArray(findings)) return null;
      return (
        <div className="space-y-3">
          {findings.map((f, i) => (
            <div key={i} className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-4">
              <div className="flex items-start justify-between gap-2">
                <p className="text-sm text-zinc-200">{f.finding}</p>
                <span
                  className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium uppercase ${
                    f.significance === "high"
                      ? "bg-red-950 text-red-400"
                      : f.significance === "medium"
                      ? "bg-amber-950 text-amber-400"
                      : "bg-zinc-800 text-zinc-400"
                  }`}
                >
                  {f.significance}
                </span>
              </div>
            </div>
          ))}
        </div>
      );
    }

    if (summaryType === 3) {
      const recommendations = item.recommendations as Record<string, string>[] | undefined;
      if (!Array.isArray(recommendations)) return null;
      return (
        <div className="space-y-3">
          {recommendations.map((r, i) => (
            <div key={i} className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-4">
              <div className="flex items-start justify-between gap-2">
                <div className="space-y-1">
                  <p className="text-sm text-zinc-200">{r.recommendation}</p>
                  {r.impact && (
                    <p className="text-xs text-zinc-500">Impact: {r.impact}</p>
                  )}
                </div>
                <span
                  className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium uppercase ${
                    r.priority === "high"
                      ? "bg-red-950 text-red-400"
                      : r.priority === "medium"
                      ? "bg-amber-950 text-amber-400"
                      : "bg-emerald-950 text-emerald-400"
                  }`}
                >
                  {r.priority}
                </span>
              </div>
            </div>
          ))}
        </div>
      );
    }

    if (summaryType === 4) {
      const risks = item.risks as Record<string, string>[] | undefined;
      if (!Array.isArray(risks)) return null;
      return (
        <div className="space-y-3">
          {risks.map((r, i) => (
            <div key={i} className="rounded-lg border border-red-900/50 bg-red-950/20 p-4">
              <div className="flex items-start justify-between gap-2">
                <div className="space-y-1">
                  <p className="text-sm text-zinc-200">{r.risk}</p>
                  {r.mitigation && (
                    <p className="text-xs text-zinc-500">
                      Mitigation: {r.mitigation}
                    </p>
                  )}
                </div>
                <span
                  className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-medium uppercase ${
                    r.severity === "high"
                      ? "bg-red-950 text-red-400"
                      : r.severity === "medium"
                      ? "bg-amber-950 text-amber-400"
                      : "bg-zinc-800 text-zinc-400"
                  }`}
                >
                  {r.severity}
                </span>
              </div>
            </div>
          ))}
        </div>
      );
    }

    return null;
  }

  return (
    <div className="mx-auto max-w-5xl space-y-8 p-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Reports</h1>
        <p className="mt-1 text-sm text-zinc-400">
          Generate AI-powered summaries and analysis
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {SUMMARY_TYPES.map(({ id, label, icon: Icon, desc }) => (
          <button
            key={id}
            onClick={() => setSummaryType(id)}
            className={`rounded-xl border p-4 text-left transition-colors ${
              summaryType === id
                ? "border-blue-600 bg-blue-600/10"
                : "border-zinc-800 bg-zinc-900/50 hover:border-zinc-700"
            }`}
          >
            <Icon
              className={`h-5 w-5 ${
                summaryType === id ? "text-blue-400" : "text-zinc-500"
              }`}
            />
            <p className="mt-2 text-sm font-medium">{label}</p>
            <p className="mt-0.5 text-xs text-zinc-500">{desc}</p>
          </button>
        ))}
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <select
          value={selectedDoc?.id ?? ""}
          onChange={(e) =>
            setSelectedDoc(docs.find((d) => d.id === Number(e.target.value)) ?? null)
          }
          className="rounded-xl border border-zinc-800 bg-zinc-900/70 px-4 py-3 text-sm text-zinc-100 outline-none focus:border-blue-600"
        >
          <option value="">Select a document...</option>
          {docs.map((d) => (
            <option key={d.id} value={d.id}>
              {d.title}
            </option>
          ))}
        </select>

        <button
          onClick={generate}
          disabled={!selectedDoc || loading}
          className="flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-4 py-3 text-sm font-medium hover:bg-blue-500 disabled:opacity-50"
        >
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <FileText className="h-4 w-4" />
          )}
          {loading ? "Generating..." : "Generate Report"}
        </button>
        <button
          onClick={handleExport}
          disabled={!selectedDoc || exporting}
          className="flex items-center justify-center gap-2 rounded-xl border border-zinc-700 px-4 py-3 text-sm font-medium text-zinc-300 hover:bg-zinc-800 disabled:opacity-50"
        >
          {exporting ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Download className="h-4 w-4" />
          )}
          {exporting ? "Exporting..." : "Export PDF"}
        </button>
      </div>

      {result && (
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-6">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">
              {result.summary_type.replace(/_/g, " ")}
            </h2>
            <button
              onClick={() => {
                const blob = new Blob([JSON.stringify(result, null, 2)], {
                  type: "application/json",
                });
                const url = URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = url;
                a.download = `${result.summary_type}-${result.doc_id}.json`;
                a.click();
                URL.revokeObjectURL(url);
              }}
              className="flex items-center gap-1.5 rounded-lg border border-zinc-800 px-3 py-1.5 text-xs text-zinc-400 hover:bg-zinc-800"
            >
              <Download className="h-3.5 w-3.5" />
              Export JSON
            </button>
          </div>
          {renderContent()}
        </div>
      )}
    </div>
  );
}
