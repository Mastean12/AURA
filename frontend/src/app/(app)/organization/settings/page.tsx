"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  Building2, Shield, Brain, Database, BarChart3, CreditCard,
  Save, Loader2, CheckCircle, XCircle, Globe, Mail, Phone,
  MapPin, Clock, Palette, Upload, Lock, Key, Users,
  HardDrive, FileText, AlertTriangle,
} from "lucide-react";

type TabId = "profile" | "security" | "ai" | "governance" | "analytics" | "subscription";

const TABS: { id: TabId; label: string; icon: React.ElementType }[] = [
  { id: "profile", label: "Company Profile", icon: Building2 },
  { id: "security", label: "Security & Access", icon: Shield },
  { id: "ai", label: "AI Configuration", icon: Brain },
  { id: "governance", label: "Data Governance", icon: Database },
  { id: "analytics", label: "Analytics", icon: BarChart3 },
  { id: "subscription", label: "Subscription", icon: CreditCard },
];

export default function OrgSettingsPage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<TabId>("profile");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [notification, setNotification] = useState("");

  const [profile, setProfile] = useState<Record<string, any>>({});
  const [security, setSecurity] = useState<Record<string, any>>({});
  const [aiConfig, setAiConfig] = useState<Record<string, any>>({});
  const [governance, setGovernance] = useState<Record<string, any>>({});
  const [analytics, setAnalytics] = useState<Record<string, any>>({});
  const [subscription, setSubscription] = useState<Record<string, any>>({});

  const token = typeof window !== "undefined" ? localStorage.getItem("aura_token") : null;
  const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  function authFetch(url: string, options: RequestInit = {}) {
    return fetch(url, {
      ...options,
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}`, ...(options.headers || {}) },
    });
  }

  useEffect(() => {
    if (!token) { router.push("/login"); return; }
    Promise.all([
      authFetch(`${apiBase}/api/v1/organization/profile`).then(r => r.json()).then(setProfile),
      authFetch(`${apiBase}/api/v1/organization/security`).then(r => r.json()).then(setSecurity),
      authFetch(`${apiBase}/api/v1/organization/ai-config`).then(r => r.json()).then(setAiConfig),
      authFetch(`${apiBase}/api/v1/organization/governance`).then(r => r.json()).then(setGovernance),
      authFetch(`${apiBase}/api/v1/organization/analytics`).then(r => r.json()).then(setAnalytics),
      authFetch(`${apiBase}/api/v1/organization/subscription`).then(r => r.json()).then(setSubscription),
    ]).catch(() => {}).finally(() => setLoading(false));
  }, []);

  async function saveEndpoint(path: string, data: any) {
    setSaving(true);
    try {
      const res = await authFetch(`${apiBase}/api/v1/organization/${path}`, {
        method: "PUT", body: JSON.stringify(data),
      });
      if (res.ok) { showNotification("Saved"); } else { showNotification("Save failed"); }
    } catch { showNotification("Save failed"); }
    finally { setSaving(false); }
  }

  function showNotification(msg: string) { setNotification(msg); setTimeout(() => setNotification(""), 3000); }

  function Toggle({ value, onChange }: { value: boolean; onChange: (v: boolean) => void }) {
    return (
      <button onClick={() => onChange(!value)}
        className={`relative h-5 w-9 rounded-full transition-colors ${value ? "bg-blue-600" : "bg-zinc-700"}`}>
        <span className={`absolute left-0.5 top-0.5 h-4 w-4 rounded-full bg-white transition-transform ${value ? "translate-x-4" : ""}`} />
      </button>
    );
  }

  if (loading) return <div className="mx-auto max-w-6xl p-6 space-y-4">{[1,2,3].map(i => <div key={i} className="h-24 animate-pulse rounded-xl bg-zinc-800/50" />)}</div>;

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Organization Settings</h1>
          <p className="text-sm text-zinc-500">Manage your organization's profile, security, AI, and governance</p>
        </div>
      </div>

      {notification && (
        <div className="rounded-lg border border-emerald-800/30 bg-emerald-950/20 px-4 py-2 text-xs text-emerald-400">{notification}</div>
      )}

      {/* Tabs */}
      <div className="flex gap-1 overflow-x-auto rounded-xl border border-zinc-800 bg-zinc-900/30 p-1">
        {TABS.map(tab => (
          <button key={tab.id} onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-1.5 rounded-lg px-4 py-2 text-xs font-medium whitespace-nowrap transition-colors ${
              activeTab === tab.id ? "bg-blue-600/20 text-blue-300" : "text-zinc-500 hover:text-zinc-300"
            }`}>
            <tab.icon className="h-3.5 w-3.5" />{tab.label}
          </button>
        ))}
      </div>

      {/* Tab: Profile */}
      {activeTab === "profile" && (
        <div className="space-y-4">
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
            <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500 mb-4">Organization Information</h2>
            <div className="grid gap-4 sm:grid-cols-2">
              {[
                { label: "Company Name", key: "name", type: "text" },
                { label: "Industry", key: "industry", type: "text" },
                { label: "Website", key: "website", type: "text" },
                { label: "Email", key: "email", type: "email" },
                { label: "Phone", key: "phone", type: "text" },
                { label: "Country", key: "country", type: "text" },
                { label: "Address", key: "address", type: "text" },
                { label: "Time Zone", key: "timezone", type: "text" },
              ].map(f => (
                <div key={f.key}>
                  <label className="text-xs text-zinc-500">{f.label}</label>
                  <input type={f.type} value={(profile as any)[f.key] || ""} onChange={e => setProfile({...profile, [f.key]: e.target.value})}
                    className="mt-1 w-full rounded-lg border border-zinc-800 bg-zinc-900/70 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-blue-600" />
                </div>
              ))}
            </div>
            <button onClick={() => saveEndpoint("profile", profile)} disabled={saving}
              className="mt-4 flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-2 text-xs font-medium hover:bg-blue-500 disabled:opacity-50">
              {saving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5" />} Save Changes
            </button>
          </div>
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
            <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500 mb-4">Branding</h2>
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="text-xs text-zinc-500">Theme Color</label>
                <div className="flex gap-2 mt-1">
                  <input type="color" value={(profile as any).theme_color || "#2563eb"} onChange={e => setProfile({...profile, theme_color: e.target.value})}
                    className="h-9 w-9 rounded border border-zinc-800 bg-transparent cursor-pointer" />
                  <input value={(profile as any).theme_color || ""} onChange={e => setProfile({...profile, theme_color: e.target.value})}
                    className="flex-1 rounded-lg border border-zinc-800 bg-zinc-900/70 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-blue-600" />
                </div>
              </div>
              <div>
                <label className="text-xs text-zinc-500">Description</label>
                <textarea value={(profile as any).description || ""} onChange={e => setProfile({...profile, description: e.target.value})} rows={2}
                  className="mt-1 w-full rounded-lg border border-zinc-800 bg-zinc-900/70 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-blue-600" />
              </div>
            </div>
            <button onClick={() => saveEndpoint("profile", profile)} disabled={saving}
              className="mt-4 flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-2 text-xs font-medium hover:bg-blue-500 disabled:opacity-50">
              <Save className="h-3.5 w-3.5" /> Save Branding
            </button>
          </div>
        </div>
      )}

      {/* Tab: Security */}
      {activeTab === "security" && (
        <div className="space-y-4">
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
            <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500 mb-4">Authentication Policies</h2>
            <div className="space-y-3">
              {[
                { label: "Min Password Length", key: "password_min_length", type: "number" },
                { label: "Password Expiry (days)", key: "password_expiry_days", type: "number" },
                { label: "Session Timeout (min)", key: "session_timeout_minutes", type: "number" },
                { label: "Lock Inactive Accounts (days)", key: "lock_inactive_days", type: "number" },
              ].map(f => (
                <div key={f.key} className="flex items-center justify-between rounded-lg bg-zinc-800/30 px-4 py-3">
                  <span className="text-xs text-zinc-300">{f.label}</span>
                  <input type={f.type} value={(security as any)[f.key] ?? ""} onChange={e => setSecurity({...security, [f.key]: Number(e.target.value)})}
                    className="w-20 rounded border border-zinc-800 bg-zinc-900 px-2 py-1 text-xs text-zinc-100 text-center outline-none focus:border-blue-600" />
                </div>
              ))}
            </div>
          </div>
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
            <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500 mb-4">Access Controls</h2>
            <div className="space-y-2">
              {[
                { label: "Require Special Characters", key: "password_require_special" },
                { label: "Require MFA", key: "require_mfa" },
                { label: "Require Email Verification", key: "require_email_verification" },
                { label: "Allow Public Invitations", key: "allow_public_invitations" },
                { label: "Force Password Reset", key: "force_password_reset" },
              ].map(f => (
                <label key={f.key} className="flex items-center justify-between rounded-lg bg-zinc-800/30 px-4 py-3">
                  <span className="text-xs text-zinc-300">{f.label}</span>
                  <Toggle value={!!(security as any)[f.key]} onChange={v => setSecurity({...security, [f.key]: v})} />
                </label>
              ))}
            </div>
          </div>
          <button onClick={() => saveEndpoint("security", security)} disabled={saving}
            className="flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-2 text-xs font-medium hover:bg-blue-500 disabled:opacity-50">
            {saving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5" />} Save Security Settings
          </button>
        </div>
      )}

      {/* Tab: AI Configuration */}
      {activeTab === "ai" && (
        <div className="space-y-4">
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
            <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500 mb-4">AI Provider</h2>
            <select value={(aiConfig as any).ai_provider || "gemini"} onChange={e => setAiConfig({...aiConfig, ai_provider: e.target.value})}
              className="w-full rounded-lg border border-zinc-800 bg-zinc-900/70 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-blue-600">
              <option value="gemini">Gemini 2.5 Flash</option>
              <option value="openai">OpenAI GPT-4o</option>
              <option value="claude">Claude (Future)</option>
            </select>
          </div>
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
            <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500 mb-4">AI Features</h2>
            <div className="space-y-2">
              {[
                { label: "Executive Intelligence", key: "executive_intelligence" },
                { label: "Risk Analysis", key: "risk_analysis" },
                { label: "Forecasting", key: "forecasting" },
                { label: "Recommendations", key: "recommendations" },
                { label: "Board Reports", key: "board_reports" },
                { label: "Document Chat", key: "document_chat" },
                { label: "Knowledge Base Search", key: "knowledge_search" },
              ].map(f => (
                <label key={f.key} className="flex items-center justify-between rounded-lg bg-zinc-800/30 px-4 py-3">
                  <span className="text-xs text-zinc-300">{f.label}</span>
                  <Toggle value={!!(aiConfig as any)[f.key]} onChange={v => setAiConfig({...aiConfig, [f.key]: v})} />
                </label>
              ))}
            </div>
          </div>
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
            <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500 mb-4">AI Cost Controls</h2>
            <div className="space-y-3">
              {[
                { label: "Monthly Budget (cents)", key: "monthly_budget_cents", note: "$50 = 5000 cents" },
                { label: "Max Daily Requests", key: "max_daily_requests" },
                { label: "Max Monthly Requests", key: "max_monthly_requests" },
                { label: "Auto Shutdown Threshold (%)", key: "auto_shutdown_threshold", note: "Pause AI when usage reaches this % of budget" },
              ].map(f => (
                <div key={f.key} className="flex items-center justify-between rounded-lg bg-zinc-800/30 px-4 py-3">
                  <div>
                    <span className="text-xs text-zinc-300">{f.label}</span>
                    {f.note && <p className="text-[10px] text-zinc-600">{f.note}</p>}
                  </div>
                  <input type="number" value={(aiConfig as any)[f.key] ?? ""} onChange={e => setAiConfig({...aiConfig, [f.key]: Number(e.target.value)})}
                    className="w-24 rounded border border-zinc-800 bg-zinc-900 px-2 py-1 text-xs text-zinc-100 text-center outline-none focus:border-blue-600" />
                </div>
              ))}
            </div>
          </div>
          <button onClick={() => saveEndpoint("ai-config", aiConfig)} disabled={saving}
            className="flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-2 text-xs font-medium hover:bg-blue-500 disabled:opacity-50">
            {saving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5" />} Save AI Configuration
          </button>
        </div>
      )}

      {/* Tab: Data Governance */}
      {activeTab === "governance" && (
        <div className="space-y-4">
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
            <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500 mb-4">Data Retention</h2>
            <select value={(governance as any).data_retention_days || 365} onChange={e => setGovernance({...governance, data_retention_days: Number(e.target.value)})}
              className="w-full rounded-lg border border-zinc-800 bg-zinc-900/70 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-blue-600">
              <option value={30}>30 Days</option>
              <option value={90}>90 Days</option>
              <option value={365}>1 Year</option>
              <option value={3650}>Forever</option>
            </select>
          </div>
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
            <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500 mb-4">File Policies</h2>
            <div className="space-y-3">
              {[
                { label: "Max Upload Size (MB)", key: "max_upload_size_mb" },
                { label: "Document Retention (days)", key: "document_retention_days" },
              ].map(f => (
                <div key={f.key} className="flex items-center justify-between rounded-lg bg-zinc-800/30 px-4 py-3">
                  <span className="text-xs text-zinc-300">{f.label}</span>
                  <input type="number" value={(governance as any)[f.key] ?? ""} onChange={e => setGovernance({...governance, [f.key]: Number(e.target.value)})}
                    className="w-20 rounded border border-zinc-800 bg-zinc-900 px-2 py-1 text-xs text-zinc-100 text-center outline-none focus:border-blue-600" />
                </div>
              ))}
              <div>
                <label className="text-xs text-zinc-500">Allowed File Types</label>
                <input value={(governance as any).allowed_file_types || ""} onChange={e => setGovernance({...governance, allowed_file_types: e.target.value})}
                  className="mt-1 w-full rounded-lg border border-zinc-800 bg-zinc-900/70 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-blue-600" />
              </div>
            </div>
          </div>
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
            <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500 mb-4">Compliance</h2>
            <div className="space-y-2">
              {[
                { key: "gdpr_compliant", label: "GDPR Ready" },
                { key: "soc2_compliant", label: "SOC 2 Ready" },
                { key: "iso27001_compliant", label: "ISO 27001 Ready" },
              ].map(f => (
                <label key={f.key} className="flex items-center justify-between rounded-lg bg-zinc-800/30 px-4 py-3">
                  <div className="flex items-center gap-2">
                    {(governance as any)[f.key] ? <CheckCircle className="h-4 w-4 text-emerald-400" /> : <XCircle className="h-4 w-4 text-zinc-600" />}
                    <span className="text-xs text-zinc-300">{f.label}</span>
                  </div>
                  <Toggle value={!!(governance as any)[f.key]} onChange={v => setGovernance({...governance, [f.key]: v})} />
                </label>
              ))}
            </div>
          </div>
          <button onClick={() => saveEndpoint("governance", governance)} disabled={saving}
            className="flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-2 text-xs font-medium hover:bg-blue-500 disabled:opacity-50">
            {saving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5" />} Save Governance Settings
          </button>
        </div>
      )}

      {/* Tab: Analytics */}
      {activeTab === "analytics" && (
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
          <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500 mb-4">Organization Analytics</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[
              { label: "Total Users", value: (analytics as any).total_users, icon: Users, color: "text-blue-400" },
              { label: "Active Users", value: (analytics as any).active_users, icon: Users, color: "text-emerald-400" },
              { label: "Workspaces", value: (analytics as any).active_workspaces, icon: Building2, color: "text-purple-400" },
              { label: "Documents", value: (analytics as any).total_documents, icon: FileText, color: "text-amber-400" },
              { label: "Documents Processed", value: (analytics as any).documents_processed, icon: CheckCircle, color: "text-emerald-400" },
              { label: "AI Requests", value: (analytics as any).ai_requests, icon: Brain, color: "text-blue-400" },
              { label: "Tokens Consumed", value: ((analytics as any).tokens_consumed || 0).toLocaleString(), icon: Database, color: "text-purple-400" },
              { label: "Cache Hits", value: (analytics as any).cache_hits, icon: HardDrive, color: "text-cyan-400" },
            ].map(m => (
              <div key={m.label} className="rounded-lg border border-zinc-800 bg-zinc-900/70 p-3 text-center">
                <m.icon className={`mx-auto h-5 w-5 ${m.color} mb-1`} />
                <p className="text-lg font-semibold text-zinc-200">{m.value}</p>
                <p className="text-[10px] text-zinc-500">{m.label}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab: Subscription */}
      {activeTab === "subscription" && (
        <div className="space-y-4">
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Current Plan</h2>
              <span className="rounded-full bg-blue-950 px-3 py-1 text-xs font-medium text-blue-400 capitalize">
                {(subscription as any).plan || "Free"}
              </span>
            </div>
            <div className="grid gap-4 sm:grid-cols-3">
              {[
                { label: "Users", value: `${(subscription as any).users_count || 0} / ${(subscription as any).users_allowed || 10}` },
                { label: "Storage", value: `${(subscription as any).storage_used_mb || 0}MB / ${(subscription as any).storage_limit_mb || 500}MB` },
                { label: "Renewal", value: (subscription as any).renewal_date ? new Date((subscription as any).renewal_date).toLocaleDateString() : "—" },
              ].map(m => (
                <div key={m.label} className="rounded-lg bg-zinc-800/30 p-3">
                  <p className="text-[10px] uppercase tracking-wider text-zinc-500">{m.label}</p>
                  <p className="mt-1 text-sm font-medium text-zinc-200">{m.value}</p>
                </div>
              ))}
            </div>
            <div className="mt-4 h-2 rounded-full bg-zinc-800 overflow-hidden">
              <div className="h-full rounded-full bg-blue-500" style={{ width: `${Math.min(((subscription as any).users_count || 0) / ((subscription as any).users_allowed || 1) * 100, 100)}%` }} />
            </div>
          </div>
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5 text-center">
            <p className="text-sm text-zinc-400 mb-4">Need more capacity?</p>
            <div className="flex justify-center gap-3">
              <button className="rounded-lg bg-blue-600 px-5 py-2 text-xs font-medium hover:bg-blue-500">Upgrade Plan</button>
              <button className="rounded-lg border border-zinc-700 px-5 py-2 text-xs font-medium text-zinc-300 hover:bg-zinc-800/50">Contact Sales</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
