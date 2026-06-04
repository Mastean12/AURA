"use client";

import { useState, useEffect } from "react";
import {
  FileText,
  MessageSquare,
  Database,
  Server,
  Sparkles,
  ArrowRight,
} from "lucide-react";
import Link from "next/link";
import { listDocuments, health, getAnalytics, getCharts } from "@/lib/api";
import type { DocumentResponse, ChartsResponse } from "@/types";

export default function Dashboard() {
  const [docs, setDocs] = useState<DocumentResponse[]>([]);
  const [serverStatus, setServerStatus] = useState<string>("");
  const [totalChats, setTotalChats] = useState(0);
  const [latestDocAnalytics, setLatestDocAnalytics] = useState<{
    row_count: number;
    column_count: number;
  } | null>(null);
  const [chartData, setChartData] = useState<ChartsResponse | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    async function load() {
      try {
        const [d, h] = await Promise.all([listDocuments(), health()]);
        setDocs(d);
        setServerStatus(h.status);
        setTotalChats(0);
        if (d.length > 0) {
          const latest = d[0];
          try {
            const a = await getAnalytics(latest.id);
            setLatestDocAnalytics({ row_count: a.row_count, column_count: a.column_count });
            if (a.columns.length > 0) {
              const c = await getCharts(latest.id, a.columns[0].name);
              setChartData(c);
            }
          } catch {
            // analytics not available
          }
        }
      } catch {
        setServerStatus("unreachable");
      } finally {
        setLoaded(true);
      }
    }
    load();
  }, []);

  const kpis = [
    {
      label: "Documents",
      value: docs.length,
      icon: FileText,
      color: "text-blue-400",
      bg: "bg-blue-600/10",
      border: "border-blue-800/30",
    },
    {
      label: "Chat Sessions",
      value: totalChats,
      icon: MessageSquare,
      color: "text-emerald-400",
      bg: "bg-emerald-600/10",
      border: "border-emerald-800/30",
    },
    {
      label: "Data Rows",
      value: latestDocAnalytics?.row_count ?? "—",
      icon: Database,
      color: "text-purple-400",
      bg: "bg-purple-600/10",
      border: "border-purple-800/30",
    },
    {
      label: "Server",
      value: serverStatus === "ok" ? "Online" : serverStatus || "Checking...",
      icon: Server,
      color: serverStatus === "ok" ? "text-emerald-400" : "text-red-400",
      bg: serverStatus === "ok" ? "bg-emerald-600/10" : "bg-red-600/10",
      border: serverStatus === "ok" ? "border-emerald-800/30" : "border-red-800/30",
    },
  ];

  return (
    <div className="mx-auto max-w-6xl space-y-8 p-8">
      {/* header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Dashboard</h1>
          <p className="mt-1 text-sm text-zinc-500">
            Overview of your AURA workspace
          </p>
        </div>
        <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600/20">
          <Sparkles className="h-5 w-5 text-blue-400" />
        </div>
      </div>

      {/* KPI cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {kpis.map((kpi) => (
          <div
            key={kpi.label}
            className={`rounded-xl border ${kpi.border} ${kpi.bg} p-5`}
          >
            <div className="flex items-center justify-between">
              <span className="text-xs font-medium uppercase tracking-wider text-zinc-500">
                {kpi.label}
              </span>
              <kpi.icon className={`h-4 w-4 ${kpi.color}`} />
            </div>
            <p className={`mt-3 text-3xl font-semibold ${kpi.color}`}>
              {loaded ? kpi.value : (
                <span className="inline-block h-7 w-16 animate-pulse rounded bg-zinc-800" />
              )}
            </p>
          </div>
        ))}
      </div>

      {/* charts + recent docs */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* chart section */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-5">
          <h2 className="mb-4 text-sm font-medium uppercase tracking-wider text-zinc-500">
            Data Overview
          </h2>
          {!loaded && (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-4 w-full animate-pulse rounded bg-zinc-800" />
              ))}
            </div>
          )}
          {loaded && !chartData && (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Database className="mb-3 h-8 w-8 text-zinc-700" />
              <p className="text-sm text-zinc-600">Upload a document to see its chart preview here</p>
              <Link
                href="/upload"
                className="mt-3 flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300"
              >
                Go to Upload <ArrowRight className="h-3 w-3" />
              </Link>
            </div>
          )}
          {chartData?.bar && (
            <BarChartRenderer data={chartData.bar as Record<string, unknown>} />
          )}
        </div>

        {/* recent documents */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-5">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">
              Recent Documents
            </h2>
            <Link
              href="/upload"
              className="text-xs text-zinc-600 hover:text-zinc-400"
            >
              View all
            </Link>
          </div>
          {!loaded && (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-12 w-full animate-pulse rounded-lg bg-zinc-800" />
              ))}
            </div>
          )}
          {loaded && docs.length === 0 && (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <FileText className="mb-3 h-8 w-8 text-zinc-700" />
              <p className="text-sm text-zinc-600">No documents uploaded yet</p>
              <Link
                href="/upload"
                className="mt-3 flex items-center gap-1 text-xs text-blue-400 hover:text-blue-300"
              >
                Upload your first document <ArrowRight className="h-3 w-3" />
              </Link>
            </div>
          )}
          {loaded && docs.length > 0 && (
            <div className="space-y-2">
              {docs.slice(0, 5).map((doc) => (
                <div
                  key={doc.id}
                  className="flex items-center gap-3 rounded-lg border border-zinc-800/50 px-4 py-3 transition-colors hover:border-zinc-700"
                >
                  <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-zinc-800">
                    <FileText className="h-4 w-4 text-zinc-400" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium">{doc.title}</p>
                    <p className="text-xs text-zinc-600">
                      {new Date(doc.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <span className="shrink-0 text-xs text-zinc-600">
                    {doc.content.length.toLocaleString()} chars
                  </span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* quick stats row */}
      {latestDocAnalytics && (
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-5">
          <h2 className="mb-4 text-sm font-medium uppercase tracking-wider text-zinc-500">
            Latest Document Stats
          </h2>
          <div className="grid gap-4 sm:grid-cols-3">
            <div className="rounded-lg bg-zinc-900/60 px-4 py-3">
              <p className="text-xs text-zinc-500">Rows</p>
              <p className="mt-1 text-xl font-semibold">{latestDocAnalytics.row_count}</p>
            </div>
            <div className="rounded-lg bg-zinc-900/60 px-4 py-3">
              <p className="text-xs text-zinc-500">Columns</p>
              <p className="mt-1 text-xl font-semibold">{latestDocAnalytics.column_count}</p>
            </div>
            <div className="rounded-lg bg-zinc-900/60 px-4 py-3">
              <p className="text-xs text-zinc-500">Total Chars</p>
              <p className="mt-1 text-xl font-semibold">
                {docs[0]?.content.length.toLocaleString() ?? "—"}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function BarChartRenderer({ data }: { data: Record<string, unknown> | undefined }) {
  if (!data) return <p className="text-sm text-zinc-600">No chart data</p>;
  const plotlyData = (data.data as Record<string, unknown>[]);
  if (!plotlyData?.length) return <p className="text-sm text-zinc-600">No chart data</p>;
  const trace = plotlyData[0];
  const labels = (trace?.x as string[]) ?? [];
  const values = (trace?.y as number[]) ?? [];
  const maxVal = Math.max(...values, 1);

  const colors = ["#636efa", "#ef553b", "#00cc96", "#ab63fa", "#ffa15a", "#19d3f3"];

  return (
    <div className="space-y-2">
      {labels.slice(0, 8).map((label, i) => (
        <div key={label} className="flex items-center gap-3 text-xs">
          <span className="w-24 truncate text-zinc-400">{label}</span>
          <div className="flex-1 overflow-hidden rounded-full bg-zinc-800">
            <div
              className="h-3 rounded-full transition-all"
              style={{
                width: `${(values[i] / maxVal) * 100}%`,
                backgroundColor: colors[i % colors.length],
              }}
            />
          </div>
          <span className="w-8 text-right text-zinc-300">{values[i]}</span>
        </div>
      ))}
    </div>
  );
}
