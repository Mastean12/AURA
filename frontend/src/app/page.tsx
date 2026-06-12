"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import {
  Sparkles, FileText, BarChart3, TrendingUp, Building2, Users, Shield,
  Brain, Bot, AlertTriangle, Target, LineChart, ScrollText, Globe,
  CheckCircle, ArrowRight, Menu, X, ChevronRight,
} from "lucide-react";

export default function LandingPage() {
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem("aura_token");
    if (token) window.location.href = "/dashboard";
  }, []);

  const features = [
    { icon: Brain, title: "Document Intelligence", desc: "Upload PDFs, DOCX, XLSX, and CSV. AURA extracts, chunks, and indexes everything for instant semantic search and Q&A." },
    { icon: Bot, title: "AI Chat", desc: "Ask questions in natural language. AURA retrieves relevant context and delivers grounded answers with source citations." },
    { icon: BarChart3, title: "Executive Intelligence", desc: "Get AI-generated executive summaries, key findings, business impact analysis, and strategic implications from your data." },
    { icon: TrendingUp, title: "Predictive Analytics", desc: "Automatic forecasting with 30/90/365-day projections, anomaly detection, risk scoring, and trend analysis." },
    { icon: ScrollText, title: "Board Reporting", desc: "Generate professional board-ready PDFs with branded covers, risk matrices, KPI dashboards, and executive briefings." },
    { icon: Building2, title: "Workspace Collaboration", desc: "Organize documents, reports, and analytics into workspaces. Invite team members with role-based access control." },
  ];

  const steps = [
    { num: "01", title: "Upload Documents", desc: "Drag-and-drop PDF, DOCX, CSV, XLSX, or TXT files." },
    { num: "02", title: "AI Processing", desc: "Text extraction, chunking, and Gemini-powered embedding." },
    { num: "03", title: "Executive Intelligence", desc: "Summaries, risks, opportunities, and health scoring." },
    { num: "04", title: "Forecasting", desc: "Automated projections with confidence intervals." },
    { num: "05", title: "Board Reports", desc: "Professional PDF reports ready for leadership." },
  ];

  const industries = [
    "Finance", "Healthcare", "NGOs", "Government", "Education",
    "Research", "Consulting", "Manufacturing", "Logistics", "Technology",
  ];

  const benefits = [
    { stat: "90%", label: "Faster Reporting", desc: "Reduce reporting time from days to minutes" },
    { stat: "100%", label: "Centralized Knowledge", desc: "All documents in one searchable platform" },
    { stat: "10x", label: "Better Decisions", desc: "AI-powered insights for leadership" },
    { stat: "24/7", label: "Always Available", desc: "Instant analysis on demand" },
  ];

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      {/* Nav */}
      <nav className="sticky top-0 z-50 border-b border-zinc-800/50 bg-zinc-950/80 backdrop-blur-lg">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-2">
            <Sparkles className="h-6 w-6 text-blue-400" />
            <span className="text-lg font-semibold">AURA</span>
          </div>
          <div className="hidden items-center gap-6 md:flex">
            <Link href="/login" className="text-sm text-zinc-400 hover:text-zinc-200">Sign In</Link>
            <Link href="/register" className="rounded-xl bg-blue-600 px-5 py-2 text-sm font-medium hover:bg-blue-500">Get Started Free</Link>
          </div>
          <button onClick={() => setMenuOpen(!menuOpen)} className="md:hidden">
            {menuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
        {menuOpen && (
          <div className="border-t border-zinc-800 px-6 py-4 md:hidden">
            <div className="flex flex-col gap-3">
              <Link href="/login" className="text-sm text-zinc-400 hover:text-zinc-200">Sign In</Link>
              <Link href="/register" className="rounded-xl bg-blue-600 px-5 py-2 text-sm font-medium text-center hover:bg-blue-500">Get Started Free</Link>
            </div>
          </div>
        )}
      </nav>

      {/* Hero */}
      <section className="relative overflow-hidden border-b border-zinc-800/50">
        <div className="absolute inset-0 bg-gradient-to-b from-blue-600/5 via-transparent to-transparent" />
        <div className="mx-auto max-w-7xl px-6 py-24 text-center">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-blue-800/30 bg-blue-950/30 px-4 py-1.5 text-xs text-blue-300">
            <Sparkles className="h-3.5 w-3.5" />
            Enterprise Intelligence Platform — Now Available
          </div>
          <h1 className="bg-gradient-to-r from-white via-zinc-200 to-zinc-400 bg-clip-text text-5xl font-bold leading-tight text-transparent sm:text-6xl">
            AI-Powered Executive<br />Intelligence Platform
          </h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-zinc-400">
            Transform documents, reports, spreadsheets, and operational data into
            executive-ready insights, forecasts, recommendations, and board-level reports.
          </p>
          <div className="mt-10 flex items-center justify-center gap-4">
            <Link href="/register" className="rounded-xl bg-blue-600 px-8 py-3 text-sm font-medium hover:bg-blue-500 shadow-lg shadow-blue-600/25">
              Get Started Free
            </Link>
            <Link href="/login" className="rounded-xl border border-zinc-700 px-8 py-3 text-sm font-medium text-zinc-300 hover:bg-zinc-800/50">
              Sign In
            </Link>
          </div>
          {/* Dashboard preview */}
          <div className="mt-16 mx-auto max-w-5xl rounded-2xl border border-zinc-800 bg-zinc-900/70 p-1 shadow-2xl shadow-blue-600/5">
            <div className="rounded-xl bg-zinc-900 p-4">
              <div className="grid gap-3 sm:grid-cols-5 mb-4">
                {[
                  { label: "Business Health", value: "84/100", color: "text-emerald-400" },
                  { label: "Active Reports", value: "12", color: "text-blue-400" },
                  { label: "Documents", value: "47", color: "text-purple-400" },
                  { label: "Forecasts", value: "8", color: "text-amber-400" },
                  { label: "Confidence", value: "92%", color: "text-emerald-400" },
                ].map((s, i) => (
                  <div key={i} className="rounded-lg bg-zinc-800/50 p-3 text-center">
                    <p className="text-xs text-zinc-500">{s.label}</p>
                    <p className={`text-xl font-bold ${s.color}`}>{s.value}</p>
                  </div>
                ))}
              </div>
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="rounded-lg bg-zinc-800/30 p-3">
                  <p className="text-xs font-medium uppercase tracking-wider text-zinc-500 mb-2">Executive Summary</p>
                  <p className="text-xs text-zinc-300 leading-relaxed">Revenue increased 12% quarter-over-quarter. Operational performance remains stable. Primary risk is supplier concentration.</p>
                </div>
                <div className="rounded-lg bg-zinc-800/30 p-3">
                  <p className="text-xs font-medium uppercase tracking-wider text-zinc-500 mb-2">Top Recommendations</p>
                  <div className="space-y-1">
                    {["Diversify supplier base", "Expand in high-growth regions", "Optimize operational costs"].map((r, i) => (
                      <div key={i} className="flex items-center gap-1.5 text-xs text-zinc-400"><ChevronRight className="h-3 w-3 text-blue-400" />{r}</div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* What AURA Does */}
      <section className="mx-auto max-w-7xl px-6 py-24">
        <div className="text-center mb-16">
          <h2 className="text-3xl font-bold">What AURA Does</h2>
          <p className="mt-3 text-zinc-400">From document upload to executive decision support in one platform</p>
        </div>
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((f, i) => (
            <div key={i} className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-6 hover:border-zinc-700 transition-colors">
              <f.icon className="h-8 w-8 text-blue-400 mb-3" />
              <h3 className="text-sm font-semibold mb-2">{f.title}</h3>
              <p className="text-xs text-zinc-400 leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* How It Works */}
      <section className="border-t border-zinc-800/50 bg-zinc-900/20">
        <div className="mx-auto max-w-7xl px-6 py-24">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold">How AURA Works</h2>
            <p className="mt-3 text-zinc-400">From upload to decision in minutes, not days</p>
          </div>
          <div className="relative">
            <div className="absolute left-8 top-0 h-full w-px bg-gradient-to-b from-blue-500 via-zinc-700 to-transparent hidden md:block" />
            <div className="space-y-12">
              {steps.map((s, i) => (
                <div key={i} className="relative flex items-start gap-8">
                  <div className="hidden md:flex h-16 w-16 shrink-0 items-center justify-center rounded-full border border-zinc-700 bg-zinc-900 text-sm font-bold text-blue-400">
                    {s.num}
                  </div>
                  <div className="min-w-0">
                    <h3 className="text-lg font-semibold">{s.title}</h3>
                    <p className="mt-1 text-sm text-zinc-400">{s.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Benefits */}
      <section className="mx-auto max-w-7xl px-6 py-24">
        <div className="text-center mb-16">
          <h2 className="text-3xl font-bold">Measurable Outcomes</h2>
        </div>
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {benefits.map((b, i) => (
            <div key={i} className="text-center rounded-xl border border-zinc-800 bg-zinc-900/50 p-8">
              <p className="text-4xl font-bold text-blue-400">{b.stat}</p>
              <p className="mt-2 text-sm font-semibold">{b.label}</p>
              <p className="mt-1 text-xs text-zinc-500">{b.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Industries */}
      <section className="border-t border-zinc-800/50 bg-zinc-900/20">
        <div className="mx-auto max-w-7xl px-6 py-24">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold">Built for Every Industry</h2>
            <p className="mt-3 text-zinc-400">Trusted by organizations across sectors</p>
          </div>
          <div className="flex flex-wrap justify-center gap-3">
            {industries.map((ind, i) => (
              <div key={i} className="rounded-xl border border-zinc-800 bg-zinc-900/50 px-5 py-3 text-sm text-zinc-300">
                {ind}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="mx-auto max-w-4xl px-6 py-24 text-center">
        <div className="rounded-2xl border border-zinc-800 bg-gradient-to-b from-zinc-900 to-zinc-950 p-12">
          <h2 className="text-3xl font-bold">Ready to transform your organization&apos;s intelligence?</h2>
          <p className="mt-3 text-zinc-400">Join organizations using AURA to make better decisions faster.</p>
          <div className="mt-8 flex items-center justify-center gap-4">
            <Link href="/register" className="rounded-xl bg-blue-600 px-8 py-3 text-sm font-medium hover:bg-blue-500">Create Account</Link>
            <Link href="/login" className="rounded-xl border border-zinc-700 px-8 py-3 text-sm font-medium text-zinc-300 hover:bg-zinc-800/50">Sign In</Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-zinc-800/50 px-6 py-8">
        <div className="mx-auto flex max-w-7xl items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-blue-400" />
            <span className="text-sm font-semibold">AURA</span>
          </div>
          <p className="text-xs text-zinc-600">Enterprise Intelligence Platform</p>
        </div>
      </footer>
    </div>
  );
}
