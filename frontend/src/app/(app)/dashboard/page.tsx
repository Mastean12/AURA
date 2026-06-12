"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  Sparkles, Brain, Shield, TrendingUp, AlertTriangle, Target,
  FileText, Loader2, LineChart, DollarSign, Clock, Database,
  ArrowRight, ChevronRight, Bot, BarChart3, MessageSquare, Building2,
} from "lucide-react";
import Link from "next/link";

export default function Dashboard() {
  const router = useRouter();
  const [user, setUser] = useState<Record<string, unknown> | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("aura_token");
    if (!token) { router.replace("/login"); return; }
    const stored = localStorage.getItem("aura_user");
    if (stored) setUser(JSON.parse(stored));
    setLoaded(true);
  }, []);

  const healthMetrics = [
    { label: "Business Health", value: "84", unit: "/100", icon: Shield, color: "text-emerald-400", bg: "bg-emerald-600/10", barColor: "bg-emerald-500", barWidth: "84%" },
    { label: "Risk Exposure", value: "32", unit: "/100", icon: AlertTriangle, color: "text-amber-400", bg: "bg-amber-600/10", barColor: "bg-amber-500", barWidth: "32%" },
    { label: "Growth Potential", value: "78", unit: "/100", icon: TrendingUp, color: "text-blue-400", bg: "bg-blue-600/10", barColor: "bg-blue-500", barWidth: "78%" },
    { label: "Data Quality", value: "91", unit: "/100", icon: Database, color: "text-purple-400", bg: "bg-purple-600/10", barColor: "bg-purple-500", barWidth: "91%" },
  ];

  const insights = [
    { icon: TrendingUp, label: "Revenue increased 12% QoQ", desc: "Driven by expanded services in East Africa", type: "trend", time: "Updated today" },
    { icon: AlertTriangle, label: "Supplier concentration risk", desc: "Top supplier accounts for 40% of procurement", type: "risk", time: "Identified 2h ago", color: "text-red-400" },
    { icon: Target, label: "Cost optimization opportunity", desc: "Process automation could reduce OPEX by 15%", type: "opportunity", time: "Identified today", color: "text-emerald-400" },
    { icon: LineChart, label: "Forecast: 8.5% growth next quarter", desc: "Confidence: 85% — Based on current trends", type: "forecast", time: "Updated today", color: "text-blue-400" },
  ];

  if (!loaded) return null;

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      {/* Welcome */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">
            Welcome back, {user?.full_name as string || "Leader"}
          </h1>
          <p className="text-sm text-zinc-500 mt-0.5">Your organization intelligence overview</p>
        </div>
        <div className="hidden sm:flex items-center gap-2 rounded-full border border-zinc-800 bg-zinc-900/50 px-3 py-1.5">
          <Bot className="h-4 w-4 text-blue-400" />
          <span className="text-xs text-zinc-400">AURA Advisor</span>
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
          <span className="text-xs text-zinc-600">Active</span>
        </div>
      </div>

      {/* Business Health Score Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {healthMetrics.map((m) => (
          <div key={m.label} className={`rounded-xl border border-zinc-800 ${m.bg} p-4`}>
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium uppercase tracking-wider text-zinc-500">{m.label}</span>
              <m.icon className={`h-4 w-4 ${m.color}`} />
            </div>
            <div className="flex items-baseline gap-0.5">
              <span className={`text-2xl font-bold ${m.color}`}>{m.value}</span>
              <span className="text-sm text-zinc-600">{m.unit}</span>
            </div>
            <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-zinc-800">
              <div className={`h-full rounded-full ${m.barColor}`} style={{ width: m.barWidth }} />
            </div>
          </div>
        ))}
      </div>

      {/* Main Grid */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Insights Feed */}
        <div className="lg:col-span-2 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Live Intelligence Feed</h2>
            <Link href="/executive" className="flex items-center gap-1 text-xs text-blue-400 hover:underline">
              View all <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
          <div className="space-y-2">
            {insights.map((ins, i) => (
              <div key={i} className="flex items-start gap-3 rounded-xl border border-zinc-800 bg-zinc-900/50 p-4 hover:border-zinc-700 transition-colors">
                <div className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg ${ins.color || "text-blue-400"} bg-zinc-800/70`}>
                  <ins.icon className="h-4 w-4" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-zinc-200">{ins.label}</p>
                  <p className="text-xs text-zinc-500 mt-0.5">{ins.desc}</p>
                  <p className="text-[10px] text-zinc-700 mt-1">{ins.time}</p>
                </div>
                <ChevronRight className="h-4 w-4 text-zinc-700 mt-1.5" />
              </div>
            ))}
          </div>
        </div>

        {/* Quick Actions */}
        <div className="space-y-4">
          <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Quick Actions</h2>
          <div className="space-y-2">
            {[
              { icon: Brain, label: "Generate Executive Summary", href: "/executive", color: "text-emerald-400" },
              { icon: FileText, label: "Generate Board Report", href: "/reports", color: "text-blue-400" },
              { icon: TrendingUp, label: "Run Forecast", href: "/predictive", color: "text-purple-400" },
              { icon: Building2, label: "Analyze Workspace", href: "/enterprise", color: "text-amber-400" },
            ].map((action, i) => (
              <Link key={i} href={action.href}
                className={`flex items-center gap-3 rounded-xl border border-zinc-800 bg-zinc-900/50 p-3 hover:border-zinc-700 transition-colors`}>
                <action.icon className={`h-4 w-4 ${action.color}`} />
                <span className="text-xs font-medium text-zinc-300">{action.label}</span>
                <ArrowRight className="h-3.5 w-3.5 ml-auto text-zinc-600" />
              </Link>
            ))}
          </div>

          {/* Recent Activity */}
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4">
            <h3 className="text-[10px] font-medium uppercase tracking-wider text-zinc-500 mb-2">Recent Reports</h3>
            <div className="space-y-2">
              {["Executive Briefing — Q2 Analysis", "Board Report — April 2026", "Risk Assessment — Updated"].map((r, i) => (
                <div key={i} className="flex items-center gap-2 text-xs text-zinc-400">
                  <FileText className="h-3 w-3 text-zinc-600" />
                  {r}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Forecast & Recommendations */}
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Forecast Snapshot</h2>
            <Link href="/predictive" className="text-xs text-blue-400 hover:underline">Full forecast →</Link>
          </div>
          <div className="grid grid-cols-3 gap-3 text-center">
            {[
              { label: "30 Day", value: "+3.2%", color: "text-emerald-400" },
              { label: "90 Day", value: "+8.5%", color: "text-blue-400" },
              { label: "12 Month", value: "+14.1%", color: "text-purple-400" },
            ].map((f) => (
              <div key={f.label} className="rounded-lg bg-zinc-800/50 p-3">
                <p className="text-[10px] text-zinc-500">{f.label}</p>
                <p className={`text-lg font-bold ${f.color}`}>{f.value}</p>
              </div>
            ))}
          </div>
          <div className="mt-3 h-12 rounded-lg bg-zinc-800/30 flex items-center justify-center">
            <span className="text-[10px] text-zinc-600">Trend chart: Positive momentum across all metrics</span>
          </div>
        </div>

        <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Recommended Actions</h2>
            <Link href="/executive" className="text-xs text-blue-400 hover:underline">All actions →</Link>
          </div>
          <div className="space-y-2">
            {[
              { priority: "High", text: "Diversify supplier base to reduce concentration risk", color: "text-red-400", dot: "bg-red-500" },
              { priority: "High", text: "Expand services in high-growth regions", color: "text-red-400", dot: "bg-red-500" },
              { priority: "Medium", text: "Optimize operational costs through automation", color: "text-amber-400", dot: "bg-amber-500" },
              { priority: "Medium", text: "Increase marketing investment in underperforming regions", color: "text-amber-400", dot: "bg-amber-500" },
            ].map((rec, i) => (
              <div key={i} className="flex items-start gap-2">
                <span className={`mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full ${rec.dot}`} />
                <div className="min-w-0">
                  <p className="text-xs text-zinc-300">{rec.text}</p>
                  <span className={`text-[10px] font-medium ${rec.color}`}>{rec.priority}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Navigation cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { href: "/analytics", label: "Analytics Dashboard", desc: "Explore detailed analytics", icon: BarChart3 },
          { href: "/chat", label: "Knowledge Base", desc: "Ask questions about documents", icon: MessageSquare },
          { href: "/enterprise", label: "Enterprise Intelligence", desc: "Multi-document analysis", icon: Building2 },
          { href: "/reports", label: "Intelligence Reports", desc: "Generate board-ready PDFs", icon: FileText },
        ].map((card) => (
          <Link key={card.href} href={card.href}
            className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4 hover:border-zinc-700 transition-colors">
            <card.icon className="h-5 w-5 text-blue-400 mb-2" />
            <p className="text-sm font-medium text-zinc-200">{card.label}</p>
            <p className="text-xs text-zinc-500 mt-0.5">{card.desc}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}


