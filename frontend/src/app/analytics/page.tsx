"use client";

import { useState, useEffect } from "react";
import {
  BarChart3,
  Table,
  Hash,
  AlertTriangle,
  Layers,
} from "lucide-react";
import { getAnalytics, getCharts, listDocuments } from "@/lib/api";
import type { DocumentResponse, AnalyticsResponse, ChartsResponse } from "@/types";

export default function AnalyticsPage() {
  const [docs, setDocs] = useState<DocumentResponse[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<number | null>(null);
  const [analytics, setAnalytics] = useState<AnalyticsResponse | null>(null);
  const [charts, setCharts] = useState<ChartsResponse | null>(null);
  const [selectedCol, setSelectedCol] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [fetched, setFetched] = useState(false);

  async function loadDocs() {
    setLoading(true);
    try {
      const d = await listDocuments();
      setDocs(d);
    } finally {
      setLoading(false);
      setFetched(true);
    }
  }

  useEffect(() => {
    if (!fetched) loadDocs();
  }, []);

  async function runAnalytics(docId: number) {
    setSelectedDoc(docId);
    setAnalytics(null);
    setCharts(null);
    setSelectedCol("");
    const a = await getAnalytics(docId);
    setAnalytics(a);
    if (a.columns.length > 0) {
      setSelectedCol(a.columns[0].name);
    }
  }

  async function runCharts(col: string) {
    if (selectedDoc === null) return;
    setSelectedCol(col);
    const c = await getCharts(selectedDoc, col);
    setCharts(c);
  }

  const numericCols = analytics?.columns.filter((c) => c.dtype === "numeric") ?? [];
  const catCols = analytics?.columns.filter((c) => c.dtype === "categorical") ?? [];

  return (
    <div className="mx-auto max-w-6xl space-y-8 p-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">Analytics</h1>
        <p className="mt-1 text-sm text-zinc-400">Data insights and visualizations</p>
      </div>

      {!fetched && (
        <div className="text-sm text-zinc-500">Loading documents...</div>
      )}

      {docs.length === 0 && fetched && (
        <div className="rounded-xl border border-zinc-800 p-8 text-center text-sm text-zinc-500">
          No documents uploaded yet.
        </div>
      )}

      {docs.length > 0 && !selectedDoc && (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {docs.map((d) => (
            <button
              key={d.id}
              onClick={() => runAnalytics(d.id)}
              className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4 text-left hover:border-zinc-700"
            >
              <p className="text-sm font-medium">{d.title}</p>
              <p className="mt-1 text-xs text-zinc-500">
                {new Date(d.created_at).toLocaleDateString()}
              </p>
            </button>
          ))}
        </div>
      )}

      {analytics && (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4">
              <div className="flex items-center gap-2 text-blue-400">
                <Table className="h-4 w-4" />
                <span className="text-xs font-medium uppercase tracking-wider text-zinc-500">
                  Rows
                </span>
              </div>
              <p className="mt-2 text-2xl font-semibold">{analytics.row_count}</p>
            </div>
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4">
              <div className="flex items-center gap-2 text-emerald-400">
                <Hash className="h-4 w-4" />
                <span className="text-xs font-medium uppercase tracking-wider text-zinc-500">
                  Columns
                </span>
              </div>
              <p className="mt-2 text-2xl font-semibold">{analytics.column_count}</p>
            </div>
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4">
              <div className="flex items-center gap-2 text-amber-400">
                <AlertTriangle className="h-4 w-4" />
                <span className="text-xs font-medium uppercase tracking-wider text-zinc-500">
                  Missing
                </span>
              </div>
              <p className="mt-2 text-2xl font-semibold">
                {analytics.columns.reduce((s, c) => s + c.missing, 0)}
              </p>
            </div>
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4">
              <div className="flex items-center gap-2 text-purple-400">
                <Layers className="h-4 w-4" />
                <span className="text-xs font-medium uppercase tracking-wider text-zinc-500">
                  Numeric
                </span>
              </div>
              <p className="mt-2 text-2xl font-semibold">{numericCols.length}</p>
            </div>
          </div>

          <div>
            <h2 className="mb-3 text-lg font-medium">Columns</h2>
            <div className="overflow-x-auto rounded-xl border border-zinc-800">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-zinc-800 bg-zinc-900/70">
                    <th className="px-4 py-3 font-medium text-zinc-400">Name</th>
                    <th className="px-4 py-3 font-medium text-zinc-400">Type</th>
                    <th className="px-4 py-3 font-medium text-zinc-400">Total</th>
                    <th className="px-4 py-3 font-medium text-zinc-400">Missing</th>
                    <th className="px-4 py-3 font-medium text-zinc-400">Mean</th>
                    <th className="px-4 py-3 font-medium text-zinc-400">Unique</th>
                    <th className="px-4 py-3 font-medium text-zinc-400">Top</th>
                  </tr>
                </thead>
                <tbody>
                  {analytics.columns.map((col) => (
                    <tr
                      key={col.name}
                      className="border-b border-zinc-800/50 hover:bg-zinc-900/30"
                    >
                      <td className="px-4 py-3 font-medium">{col.name}</td>
                      <td className="px-4 py-3 text-zinc-400">{col.dtype}</td>
                      <td className="px-4 py-3">{col.total}</td>
                      <td className="px-4 py-3">
                        {col.missing > 0 ? (
                          <span className="text-amber-400">{col.missing}</span>
                        ) : (
                          col.missing
                        )}
                      </td>
                      <td className="px-4 py-3">
                        {col.numeric ? col.numeric.mean : "—"}
                      </td>
                      <td className="px-4 py-3">
                        {col.categorical
                          ? (col.categorical.unique as number)
                          : "—"}
                      </td>
                      <td className="px-4 py-3 text-zinc-400">
                        {col.categorical
                          ? (
                              col.categorical.top_values as {
                                value: string;
                                count: number;
                              }[]
                            ).slice(0, 2)
                            .map((t) => t.value)
                            .join(", ")
                          : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div>
            <h2 className="mb-3 text-lg font-medium">Charts</h2>
            <div className="flex flex-wrap gap-2">
              {analytics.columns.map((col) => (
                <button
                  key={col.name}
                  onClick={() => runCharts(col.name)}
                  className={`rounded-lg border px-3 py-1.5 text-xs font-medium transition-colors ${
                    selectedCol === col.name
                      ? "border-blue-600 bg-blue-600/20 text-blue-300"
                      : "border-zinc-800 text-zinc-400 hover:border-zinc-600"
                  }`}
                >
                  <BarChart3 className="mr-1 inline h-3 w-3" />
                  {col.name}
                </button>
              ))}
            </div>
          </div>

          {charts && (
            <div className="grid gap-6 lg:grid-cols-2">
              {(["bar", "pie", "line"] as const).map((type) => (
                <div
                  key={type}
                  className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4"
                >
                  <h3 className="mb-3 text-xs font-medium uppercase tracking-wider text-zinc-500">
                    {type.charAt(0).toUpperCase() + type.slice(1)}
                  </h3>
                  {charts[type] && <ChartFrame data={charts[type]} />}
                </div>
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}

function ChartFrame({ data }: { data: Record<string, unknown> | undefined }) {
  if (!data) return <div className="h-48 rounded-lg bg-zinc-900/70" />;
  const plotlyData = (data.data as Record<string, unknown>[]);
  if (!plotlyData?.length) return <div className="h-48 rounded-lg bg-zinc-900/70" />;
  const trace = plotlyData[0];
  const labels = (trace?.labels as string[]) ?? (trace?.x as string[]) ?? [];
  const values = (trace?.values as number[]) ?? (trace?.y as number[]) ?? [];

  if (!labels.length) {
    return <div className="h-48 rounded-lg bg-zinc-900/70" />;
  }

  const maxVal = Math.max(...values);
  const chartType = trace?.type as string;

  if (chartType === "pie") {
    return (
      <div className="flex flex-wrap items-center justify-center gap-4">
        {labels.map((label, i) => {
          const pct = ((values[i] / values.reduce((a, b) => a + b, 0)) * 100).toFixed(1);
          const colors = ["#636efa", "#ef553b", "#00cc96", "#ab63fa", "#ffa15a"];
          return (
            <div key={label} className="flex items-center gap-2 text-xs">
              <span
                className="h-3 w-3 rounded-full"
                style={{ backgroundColor: colors[i % colors.length] }}
              />
              <span className="text-zinc-300">{label}</span>
              <span className="text-zinc-500">{pct}%</span>
            </div>
          );
        })}
      </div>
    );
  }

  return (
    <div className="space-y-1">
      {labels.map((label, i) => (
        <div key={label} className="flex items-center gap-3 text-xs">
          <span className="w-20 truncate text-zinc-400">{label}</span>
          <div className="flex-1 overflow-hidden rounded-full bg-zinc-800">
            <div
              className="h-2 rounded-full bg-blue-500 transition-all"
              style={{ width: `${(values[i] / maxVal) * 100}%` }}
            />
          </div>
          <span className="w-8 text-right text-zinc-300">{values[i]}</span>
        </div>
      ))}
    </div>
  );
}
