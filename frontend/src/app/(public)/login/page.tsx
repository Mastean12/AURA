"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Sparkles, Loader2, Eye, EyeOff } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showPw, setShowPw] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/auth/login`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (!res.ok) { setError(data.detail || "Login failed"); return; }
      localStorage.setItem("aura_token", data.access_token);
      localStorage.setItem("aura_user", JSON.stringify(data.user));
      document.cookie = `aura_token=${data.access_token}; path=/; max-age=86400; SameSite=Lax`;
      router.push("/dashboard");
    } catch { setError("Connection failed"); }
    finally { setLoading(false); }
  }

  return (
    <div className="min-h-screen bg-zinc-950 flex">
      {/* Left - Brand */}
      <div className="hidden lg:flex w-1/2 bg-gradient-to-br from-blue-600/10 via-zinc-950 to-zinc-900 items-center justify-center p-12">
        <div className="max-w-md">
          <div className="flex items-center gap-2 mb-8">
            <Sparkles className="h-7 w-7 text-blue-400" />
            <span className="text-xl font-semibold">AURA</span>
          </div>
          <h2 className="text-3xl font-bold leading-tight mb-4">AI-Powered Executive Intelligence</h2>
          <p className="text-zinc-400 leading-relaxed">
            Transform your documents, reports, and data into executive-ready insights, forecasts, and board reports.
          </p>
          <div className="mt-8 space-y-4">
            {[
              "Document Intelligence & RAG Chat",
              "Executive Summaries & Risk Analysis",
              "Predictive Forecasting & Anomaly Detection",
              "Board-Ready PDF Reports",
              "Workspace Collaboration & RBAC",
            ].map((item, i) => (
              <div key={i} className="flex items-center gap-3 text-sm text-zinc-300">
                <div className="h-1.5 w-1.5 rounded-full bg-blue-400" />
                {item}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Right - Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8">
        <div className="w-full max-w-sm">
          <div className="text-center mb-8 lg:hidden">
            <div className="flex items-center justify-center gap-2 mb-4">
              <Sparkles className="h-6 w-6 text-blue-400" />
              <span className="text-lg font-semibold">AURA</span>
            </div>
          </div>
          <h1 className="text-2xl font-semibold">Welcome back</h1>
          <p className="mt-1 text-sm text-zinc-500">Sign in to your account</p>

          <form onSubmit={handleSubmit} className="mt-8 space-y-5">
            <div>
              <label className="text-xs font-medium text-zinc-400">Email address</label>
              <input type="email" value={email} onChange={e => setEmail(e.target.value)} required placeholder="you@company.com"
                className="mt-1.5 w-full rounded-xl border border-zinc-800 bg-zinc-900/70 px-4 py-2.5 text-sm text-zinc-100 placeholder-zinc-600 outline-none focus:border-blue-600 transition-colors" />
            </div>
            <div>
              <div className="flex items-center justify-between">
                <label className="text-xs font-medium text-zinc-400">Password</label>
                <button type="button" className="text-xs text-zinc-600 hover:text-zinc-400">Forgot?</button>
              </div>
              <div className="relative mt-1.5">
                <input type={showPw ? "text" : "password"} value={password} onChange={e => setPassword(e.target.value)} required placeholder="Enter your password"
                  className="w-full rounded-xl border border-zinc-800 bg-zinc-900/70 px-4 py-2.5 text-sm text-zinc-100 placeholder-zinc-600 outline-none focus:border-blue-600 transition-colors pr-10" />
                <button type="button" onClick={() => setShowPw(!showPw)} className="absolute right-3 top-2.5 text-zinc-500 hover:text-zinc-300">
                  {showPw ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            {error && <p className="text-xs text-red-400 bg-red-950/30 rounded-lg px-3 py-2">{error}</p>}

            <button type="submit" disabled={loading}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-blue-600 py-2.5 text-sm font-medium hover:bg-blue-500 disabled:opacity-50 transition-colors shadow-lg shadow-blue-600/20">
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
              {loading ? "Signing in..." : "Sign in"}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-zinc-600">
            Don&apos;t have an account?{" "}
            <a href="/register" className="text-blue-400 hover:underline font-medium">Create account</a>
          </p>
        </div>
      </div>
    </div>
  );
}
