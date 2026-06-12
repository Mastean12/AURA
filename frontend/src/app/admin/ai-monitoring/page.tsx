"use client";

import { useState, useEffect } from "react";
import {
  Activity, AlertTriangle, BarChart3, Database, RefreshCw,
  CheckCircle, XCircle, Clock, TrendingUp, DollarSign, Server,
  Cpu, Zap, Shield,
} from "lucide-react";

interface MonitoringData {
  ai_usage: {
    requests_today: number;
    requests_month: number;
    total_requests: number;
    tokens_consumed: number;
    estimated_cost: number;
    average_response_time_ms: number;
    total_retries: number;
    failed_requests: number;
  };
  ai_health: {
    provider: string;
    active_model: string;
    key_configured: boolean;
  };
  cache_metrics: {
    cache_hit_rate: number;
    cache_miss_rate: number;
    tokens_saved: number;
    estimated_cost_savings: number;
    cache_entries: number;
  };
  error_monitoring: {
    failed_requests: number;
    timeout_count: number;
    retry_count: number;
    recent_errors: { type: string; error: string; time: string }[];
  };
}

export default function AIMonitoringPage() {
  const [data, setData] = useState<MonitoringData | null>(null);
  const [loading, setLoading] = useState(true);

  async function fetchData() {
    setLoading(true);
    try {
      const res = await fetch("http://localhost:8000/api/v1/admin/ai-monitoring");
      const json = await res.json();
      setData(json);
    } catch {
      // keep existing data
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { fetchData(); }, []);

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">AI Monitoring</h1>
          <p className="text-sm text-zinc-500">Internal operational metrics — not visible to clients</p>
        </div>
        <button onClick={fetchData} disabled={loading}
          className="flex items-center gap-1.5 rounded-xl border border-zinc-800 bg-zinc-900/50 px-4 py-2 text-sm text-zinc-400 hover:text-zinc-200">
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {loading && !data ? (
        <div className="space-y-4">{[1,2,3,4].map(i => <div key={i} className="h-24 animate-pulse rounded-xl bg-zinc-800/50" />)}</div>
      ) : data ? (
        <div className="space-y-6">
          {/* AI Usage */}
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
            <div className="flex items-center gap-2 mb-4">
              <Activity className="h-5 w-5 text-blue-400" />
              <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">AI Usage</h2>
            </div>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <MetricCard label="Requests Today" value={data.ai_usage.requests_today} icon={BarChart3} color="text-blue-400" />
              <MetricCard label="Requests This Month" value={data.ai_usage.requests_month} icon={BarChart3} color="text-emerald-400" />
              <MetricCard label="Tokens Consumed" value={data.ai_usage.tokens_consumed.toLocaleString()} icon={Cpu} color="text-purple-400" />
              <MetricCard label="Est. Cost" value={`$${data.ai_usage.estimated_cost.toFixed(4)}`} icon={DollarSign} color="text-amber-400" />
              <MetricCard label="Avg Response Time" value={`${data.ai_usage.average_response_time_ms}ms`} icon={Clock} color="text-cyan-400" />
              <MetricCard label="Total Requests" value={data.ai_usage.total_requests} icon={Activity} color="text-zinc-300" />
              <MetricCard label="Failed Requests" value={data.ai_usage.failed_requests} icon={XCircle} color="text-red-400" />
              <MetricCard label="Total Retries" value={data.ai_usage.total_retries} icon={RefreshCw} color="text-amber-400" />
            </div>
          </div>

          {/* AI Health */}
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
            <div className="flex items-center gap-2 mb-4">
              <Server className="h-5 w-5 text-emerald-400" />
              <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">AI Health</h2>
            </div>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <div className="rounded-lg border border-zinc-800 bg-zinc-900/70 p-3">
                <p className="text-[10px] uppercase tracking-wider text-zinc-500">Provider</p>
                <p className="mt-1 text-sm font-semibold text-zinc-200">{data.ai_health.provider}</p>
              </div>
              <div className="rounded-lg border border-zinc-800 bg-zinc-900/70 p-3">
                <p className="text-[10px] uppercase tracking-wider text-zinc-500">Active Model</p>
                <p className="mt-1 text-sm font-semibold text-zinc-200">{data.ai_health.active_model}</p>
              </div>
              <div className="rounded-lg border border-zinc-800 bg-zinc-900/70 p-3">
                <p className="text-[10px] uppercase tracking-wider text-zinc-500">API Key</p>
                <div className="flex items-center gap-1.5 mt-1">
                  {data.ai_health.key_configured ? (
                    <><CheckCircle className="h-4 w-4 text-emerald-400" /><span className="text-sm font-semibold text-emerald-400">Configured</span></>
                  ) : (
                    <><XCircle className="h-4 w-4 text-red-400" /><span className="text-sm font-semibold text-red-400">Missing</span></>
                  )}
                </div>
              </div>
              <div className="rounded-lg border border-zinc-800 bg-zinc-900/70 p-3">
                <p className="text-[10px] uppercase tracking-wider text-zinc-500">Status</p>
                <div className="flex items-center gap-1.5 mt-1">
                  {data.ai_health.key_configured ? (
                    <><div className="h-2 w-2 rounded-full bg-emerald-500" /><span className="text-sm font-semibold text-emerald-400">Healthy</span></>
                  ) : (
                    <><div className="h-2 w-2 rounded-full bg-red-500" /><span className="text-sm font-semibold text-red-400">Unhealthy</span></>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Cache Metrics */}
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
            <div className="flex items-center gap-2 mb-4">
              <Database className="h-5 w-5 text-violet-400" />
              <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Cache Metrics</h2>
            </div>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <MetricCard label="Cache Hit Rate" value={`${data.cache_metrics.cache_hit_rate}%`} icon={Zap} color="text-emerald-400" />
              <MetricCard label="Cache Miss Rate" value={`${data.cache_metrics.cache_miss_rate}%`} icon={Activity} color="text-amber-400" />
              <MetricCard label="Tokens Saved" value={data.cache_metrics.tokens_saved.toLocaleString()} icon={Cpu} color="text-blue-400" />
              <MetricCard label="Est. Cost Savings" value={`$${data.cache_metrics.estimated_cost_savings.toFixed(4)}`} icon={DollarSign} color="text-emerald-400" />
              <MetricCard label="Cache Entries" value={data.cache_metrics.cache_entries} icon={Database} color="text-violet-400" />
            </div>
          </div>

          {/* Error Monitoring */}
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
            <div className="flex items-center gap-2 mb-4">
              <AlertTriangle className="h-5 w-5 text-red-400" />
              <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Error Monitoring</h2>
            </div>
            <div className="grid gap-4 sm:grid-cols-3 mb-4">
              <MetricCard label="Failed Requests" value={data.error_monitoring.failed_requests} icon={XCircle} color="text-red-400" />
              <MetricCard label="Timeouts" value={data.error_monitoring.timeout_count} icon={Clock} color="text-amber-400" />
              <MetricCard label="Retries" value={data.error_monitoring.retry_count} icon={RefreshCw} color="text-amber-400" />
            </div>
            {data.error_monitoring.recent_errors.length > 0 && (
              <div>
                <p className="text-xs font-medium uppercase tracking-wider text-zinc-500 mb-2">Recent Errors</p>
                <div className="space-y-1 max-h-40 overflow-y-auto">
                  {data.error_monitoring.recent_errors.map((err, i) => (
                    <div key={i} className="flex items-start gap-2 rounded-lg border border-red-800/30 bg-red-950/20 p-2">
                      <AlertTriangle className="h-3.5 w-3.5 shrink-0 text-red-400 mt-0.5" />
                      <div className="min-w-0">
                        <p className="text-xs text-zinc-300">{err.type}</p>
                        <p className="text-[10px] text-zinc-500 truncate">{err.error}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      ) : (
        <p className="text-sm text-zinc-600 text-center py-12">Could not load monitoring data. Ensure backend is running.</p>
      )}
    </div>
  );
}

function MetricCard({ label, value, icon: Icon, color }: { label: string; value: string | number; icon: React.ElementType; color: string }) {
  return (
    <div className="rounded-lg border border-zinc-800 bg-zinc-900/70 p-3">
      <div className="flex items-center justify-between mb-1">
        <p className="text-[10px] uppercase tracking-wider text-zinc-500">{label}</p>
        <Icon className={`h-3.5 w-3.5 ${color}`} />
      </div>
      <p className={`text-lg font-semibold ${color}`}>{value}</p>
    </div>
  );
}
