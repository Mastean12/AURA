"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Sparkles, Loader2 } from "lucide-react";

export default function RegisterPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [orgName, setOrgName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPw, setConfirmPw] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (password !== confirmPw) { setError("Passwords do not match"); return; }
    setLoading(true);
    setError("");
    try {
      const res = await fetch("http://localhost:8000/api/v1/auth/register", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, full_name: fullName, organization_name: orgName }),
      });
      const data = await res.json();
      if (!res.ok) { setError(data.detail || "Registration failed"); return; }
      localStorage.setItem("aura_token", data.access_token);
      localStorage.setItem("aura_user", JSON.stringify(data.user));
      document.cookie = `aura_token=${data.access_token}; path=/; max-age=86400; SameSite=Lax`;
      router.push("/dashboard");
    } catch { setError("Connection failed"); }
    finally { setLoading(false); }
  }

  return (
    <div className="min-h-screen bg-zinc-950 flex">
      <div className="hidden lg:flex w-1/2 bg-gradient-to-br from-blue-600/10 via-zinc-950 to-zinc-900 items-center justify-center p-12">
        <div className="max-w-md">
          <div className="flex items-center gap-2 mb-8">
            <Sparkles className="h-7 w-7 text-blue-400" />
            <span className="text-xl font-semibold">AURA</span>
          </div>
          <h2 className="text-3xl font-bold leading-tight mb-4">Start your free trial</h2>
          <p className="text-zinc-400 leading-relaxed">
            No credit card required. Full access to all features during your trial period.
          </p>
          <div className="mt-8 space-y-4">
            {[
              "Unlimited document uploads",
              "AI-powered executive intelligence",
              "Board-ready PDF reports",
              "Team collaboration & workspaces",
              "Enterprise-grade security",
            ].map((item, i) => (
              <div key={i} className="flex items-center gap-3 text-sm text-zinc-300">
                <div className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                {item}
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="w-full lg:w-1/2 flex items-center justify-center p-8">
        <div className="w-full max-w-sm">
          <div className="text-center mb-8 lg:hidden">
            <div className="flex items-center justify-center gap-2 mb-4">
              <Sparkles className="h-6 w-6 text-blue-400" />
              <span className="text-lg font-semibold">AURA</span>
            </div>
          </div>
          <h1 className="text-2xl font-semibold">Create your account</h1>
          <p className="mt-1 text-sm text-zinc-500">Get started with AURA Enterprise Intelligence</p>

          <form onSubmit={handleSubmit} className="mt-8 space-y-4">
            <div>
              <label className="text-xs font-medium text-zinc-400">Full name</label>
              <input type="text" value={fullName} onChange={e => setFullName(e.target.value)} required placeholder="John Smith"
                className="mt-1.5 w-full rounded-xl border border-zinc-800 bg-zinc-900/70 px-4 py-2.5 text-sm text-zinc-100 placeholder-zinc-600 outline-none focus:border-blue-600" />
            </div>
            <div>
              <label className="text-xs font-medium text-zinc-400">Organization name</label>
              <input type="text" value={orgName} onChange={e => setOrgName(e.target.value)} required placeholder="Acme Corporation"
                className="mt-1.5 w-full rounded-xl border border-zinc-800 bg-zinc-900/70 px-4 py-2.5 text-sm text-zinc-100 placeholder-zinc-600 outline-none focus:border-blue-600" />
            </div>
            <div>
              <label className="text-xs font-medium text-zinc-400">Email address</label>
              <input type="email" value={email} onChange={e => setEmail(e.target.value)} required placeholder="you@company.com"
                className="mt-1.5 w-full rounded-xl border border-zinc-800 bg-zinc-900/70 px-4 py-2.5 text-sm text-zinc-100 placeholder-zinc-600 outline-none focus:border-blue-600" />
            </div>
            <div>
              <label className="text-xs font-medium text-zinc-400">Password</label>
              <input type="password" value={password} onChange={e => setPassword(e.target.value)} required minLength={8} placeholder="Min. 8 characters"
                className="mt-1.5 w-full rounded-xl border border-zinc-800 bg-zinc-900/70 px-4 py-2.5 text-sm text-zinc-100 placeholder-zinc-600 outline-none focus:border-blue-600" />
            </div>
            <div>
              <label className="text-xs font-medium text-zinc-400">Confirm password</label>
              <input type="password" value={confirmPw} onChange={e => setConfirmPw(e.target.value)} required minLength={8} placeholder="Re-enter your password"
                className="mt-1.5 w-full rounded-xl border border-zinc-800 bg-zinc-900/70 px-4 py-2.5 text-sm text-zinc-100 placeholder-zinc-600 outline-none focus:border-blue-600" />
            </div>

            {error && <p className="text-xs text-red-400 bg-red-950/30 rounded-lg px-3 py-2">{error}</p>}

            <button type="submit" disabled={loading}
              className="flex w-full items-center justify-center gap-2 rounded-xl bg-blue-600 py-2.5 text-sm font-medium hover:bg-blue-500 disabled:opacity-50 shadow-lg shadow-blue-600/20">
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
              {loading ? "Creating account..." : "Create account"}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-zinc-600">
            Already have an account?{" "}
            <a href="/login" className="text-blue-400 hover:underline font-medium">Sign in</a>
          </p>
        </div>
      </div>
    </div>
  );
}
