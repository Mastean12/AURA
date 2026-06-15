"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  CreditCard, Building2, Users, FileText, Brain, HardDrive,
  Check, X, ArrowUp, ArrowDown, Download, Loader2, Zap,
  RefreshCw, AlertTriangle, DollarSign, BarChart3, Save,
} from "lucide-react";

const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function authHeaders() {
  const token = localStorage.getItem("aura_token");
  return { "Content-Type": "application/json", Authorization: `Bearer ${token}` } as Record<string, string>;
}

export default function BillingPage() {
  const router = useRouter();
  const [tab, setTab] = useState("overview");
  const [billing, setBilling] = useState<Record<string, any>>({});
  const [plans, setPlans] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [changing, setChanging] = useState(false);
  const [notification, setNotification] = useState("");
  const [edit, setEdit] = useState<Record<string, any>>({});

  useEffect(() => {
    const token = localStorage.getItem("aura_token");
    if (!token) { router.push("/login"); return; }
    Promise.all([
      fetch(`${apiBase}/api/v1/billing/`, { headers: authHeaders() }).then(r => r.json()).then(d => { setBilling(d); setEdit(d); }),
      fetch(`${apiBase}/api/v1/billing/plans`, { headers: authHeaders() }).then(r => r.json()).then(setPlans),
    ]).catch(() => {}).finally(() => setLoading(false));
  }, []);

  async function handleChangePlan(planId: string) {
    setChanging(true);
    try {
      const res = await fetch(`${apiBase}/api/v1/billing/plan`, {
        method: "POST", headers: authHeaders(),
        body: JSON.stringify({ plan: planId }),
      });
      const data = await res.json();
      showNotification(data.detail || data.error || "Plan changed");
      const b = await fetch(`${apiBase}/api/v1/billing/`, { headers: authHeaders() }).then(r => r.json());
      setBilling(b);
    } catch { showNotification("Plan change failed"); }
    finally { setChanging(false); }
  }

  async function handleSaveSettings() {
    try {
      const res = await fetch(`${apiBase}/api/v1/billing/`, {
        method: "PUT", headers: authHeaders(),
        body: JSON.stringify(edit),
      });
      showNotification("Billing settings saved");
    } catch { showNotification("Save failed"); }
  }

  function showNotification(msg: string) { setNotification(msg); setTimeout(() => setNotification(""), 3000); }

  const usage = billing.usage || {};
  const uom = (used: number, limit: number) => `${used} / ${limit}`;
  const pct = (used: number, limit: number) => Math.min((used / (limit || 1)) * 100, 100);

  if (loading) return <div className="mx-auto max-w-6xl p-6 space-y-4">{[1,2,3].map(i => <div key={i} className="h-24 animate-pulse rounded-xl bg-zinc-800/50" />)}</div>;

  const currentPlan = plans.find(p => p.id === billing.plan) || { name: billing.plan_name || billing.plan, price_cents: billing.price_cents };
  const price = ((currentPlan.price_cents || 0) / 100).toFixed(2);

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Billing</h1>
          <p className="text-sm text-zinc-500">Manage subscription, usage, and invoices</p>
        </div>
      </div>

      {notification && <div className="rounded-lg border border-emerald-800/30 bg-emerald-950/20 px-4 py-2 text-xs text-emerald-400">{notification}</div>}

      {/* Current Plan Card */}
      <div className="rounded-xl border border-zinc-800 bg-gradient-to-br from-zinc-900 to-zinc-950 p-6">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-xs uppercase tracking-wider text-zinc-500 mb-1">Current Plan</p>
            <h2 className="text-2xl font-bold text-zinc-100">{currentPlan.name || "Free"}</h2>
            <p className="text-sm text-zinc-400 mt-1">${price}/month &bull; {billing.subscription_status}</p>
            {billing.period_end && <p className="text-xs text-zinc-600 mt-1">Renewal: {new Date(billing.period_end).toLocaleDateString()}</p>}
          </div>
          <div className="text-right">
            <p className="text-xs text-zinc-500">Status</p>
            <div className="flex items-center gap-1.5 mt-1">
              <span className="h-2 w-2 rounded-full bg-emerald-500" />
              <span className="text-sm font-medium text-emerald-400 capitalize">{billing.subscription_status}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 rounded-xl border border-zinc-800 bg-zinc-900/30 p-1">
        {[
          { id: "overview", label: "Overview", icon: CreditCard },
          { id: "usage", label: "Usage", icon: BarChart3 },
          { id: "plans", label: "Plans", icon: Zap },
          { id: "invoices", label: "Invoices", icon: FileText },
          { id: "settings", label: "Settings", icon: Building2 },
        ].map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`flex items-center gap-1.5 rounded-lg px-4 py-2 text-xs font-medium flex-1 justify-center transition-colors ${
              tab === t.id ? "bg-blue-600/20 text-blue-300" : "text-zinc-500 hover:text-zinc-300"
            }`}>
            <t.icon className="h-3.5 w-3.5" />{t.label}
          </button>
        ))}
      </div>

      {/* Overview Tab */}
      {tab === "overview" && (
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
          <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500 mb-4">Billing Overview</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            {[
              { label: "Plan", value: currentPlan.name, icon: Zap },
              { label: "Monthly Cost", value: `$${price}`, icon: DollarSign },
              { label: "Status", value: billing.subscription_status, icon: RefreshCw },
              { label: "Billing Contact", value: billing.billing_email || "Not set", icon: Building2 },
              { label: "Country", value: billing.country || "Not set", icon: Building2 },
              { label: "Currency", value: billing.currency || "USD", icon: DollarSign },
            ].map(m => (
              <div key={m.label} className="flex items-center gap-3 rounded-lg bg-zinc-800/30 p-3">
                <m.icon className="h-5 w-5 text-zinc-500" />
                <div>
                  <p className="text-[10px] uppercase text-zinc-500">{m.label}</p>
                  <p className="text-sm font-medium text-zinc-200">{m.value}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Usage Tab */}
      {tab === "usage" && (
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
          <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500 mb-4">Usage & Limits</h2>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {[
              { label: "Users", used: usage.users, limit: usage.users_limit, icon: Users, color: "text-blue-400" },
              { label: "Workspaces", used: usage.workspaces, limit: usage.workspaces_limit, icon: Building2, color: "text-emerald-400" },
              { label: "Documents", used: usage.documents, limit: usage.documents_limit, icon: FileText, color: "text-purple-400" },
              { label: "AI Requests", used: usage.ai_requests, limit: usage.ai_requests_limit, icon: Brain, color: "text-amber-400" },
              { label: "Storage (MB)", used: usage.storage_mb, limit: usage.storage_limit_mb, icon: HardDrive, color: "text-cyan-400" },
            ].map(m => {
              const barPct = Math.min((m.used / (m.limit || 1)) * 100, 100);
              const isOver = m.used >= m.limit;
              return (
                <div key={m.label} className="rounded-lg border border-zinc-800 bg-zinc-900/70 p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <m.icon className={`h-4 w-4 ${m.color}`} />
                      <span className="text-xs text-zinc-400">{m.label}</span>
                    </div>
                    {isOver && <AlertTriangle className="h-4 w-4 text-red-400" />}
                  </div>
                  <p className={`text-lg font-semibold ${isOver ? "text-red-400" : "text-zinc-200"}`}>
                    {m.used} <span className="text-sm text-zinc-600">/ {m.limit}</span>
                  </p>
                  <div className="mt-2 h-1.5 rounded-full bg-zinc-800 overflow-hidden">
                    <div className={`h-full rounded-full ${barPct >= 100 ? "bg-red-500" : barPct >= 80 ? "bg-amber-500" : "bg-blue-500"}`}
                      style={{ width: `${barPct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Plans Tab */}
      {tab === "plans" && (
        <div className="grid gap-4 lg:grid-cols-2">
          {plans.filter(p => p.id !== "free").map(plan => {
            const isCurrent = billing.plan === plan.id;
            return (
              <div key={plan.id} className={`rounded-xl border p-5 ${isCurrent ? "border-blue-600/50 bg-blue-600/5" : "border-zinc-800 bg-zinc-900/50"}`}>
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h3 className="text-lg font-semibold">{plan.name}</h3>
                    <p className="text-2xl font-bold mt-1">${(plan.price_cents / 100).toFixed(2)}<span className="text-sm font-normal text-zinc-500">/month</span></p>
                  </div>
                  {isCurrent && <span className="rounded-full bg-blue-600/20 px-2.5 py-0.5 text-xs text-blue-400">Current</span>}
                </div>
                <div className="space-y-1.5 text-xs text-zinc-400">
                  {[
                    { label: "Users", value: plan.users },
                    { label: "Workspaces", value: plan.workspaces === 999 ? "Unlimited" : plan.workspaces },
                    { label: "Documents/mo", value: plan.documents === 999999 ? "Unlimited" : plan.documents.toLocaleString() },
                    { label: "AI Requests/mo", value: plan.ai_requests === 999999 ? "Unlimited" : plan.ai_requests.toLocaleString() },
                    { label: "Storage", value: `${plan.storage_mb / 1024} GB` },
                  ].map(f => (
                    <div key={f.label} className="flex items-center gap-2">
                      <Check className="h-3 w-3 text-emerald-500" />
                      <span className="text-zinc-500 w-28">{f.label}</span>
                      <span className="text-zinc-300">{f.value}</span>
                    </div>
                  ))}
                </div>
                {!isCurrent && (
                  <button onClick={() => handleChangePlan(plan.id)} disabled={changing}
                    className="mt-4 w-full rounded-lg bg-blue-600 py-2 text-xs font-medium hover:bg-blue-500 disabled:opacity-50">
                    {changing ? <Loader2 className="h-3.5 w-3.5 inline animate-spin mr-1" /> : null}
                    {plan.price_cents === 0 ? "Contact Sales" : `Switch to ${plan.name}`}
                  </button>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Invoices Tab */}
      {tab === "invoices" && (
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
          <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500 mb-4">Invoices</h2>
          {(billing.invoices || []).length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead><tr className="border-b border-zinc-800 text-zinc-500">
                  <th className="px-3 py-2 font-medium">Invoice</th>
                  <th className="px-3 py-2 font-medium">Date</th>
                  <th className="px-3 py-2 font-medium">Amount</th>
                  <th className="px-3 py-2 font-medium">Status</th>
                </tr></thead>
                <tbody>
                  {billing.invoices.map((inv: any) => (
                    <tr key={inv.id} className="border-b border-zinc-800/50">
                      <td className="px-3 py-2 text-zinc-300">{inv.invoice_number}</td>
                      <td className="px-3 py-2 text-zinc-500">{inv.created_at ? new Date(inv.created_at).toLocaleDateString() : "—"}</td>
                      <td className="px-3 py-2 text-zinc-300">${(inv.amount_cents / 100).toFixed(2)}</td>
                      <td className="px-3 py-2">
                        <span className={`rounded px-1.5 py-0.5 text-[10px] font-medium capitalize ${
                          inv.status === "paid" ? "bg-emerald-900/50 text-emerald-300" :
                          inv.status === "pending" ? "bg-amber-900/50 text-amber-300" : "bg-red-900/50 text-red-300"
                        }`}>{inv.status}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-xs text-zinc-600 text-center py-8">No invoices yet. Invoices will appear after the first billing cycle.</p>
          )}
        </div>
      )}

      {/* Settings Tab */}
      {tab === "settings" && (
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
          <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500 mb-4">Billing Settings</h2>
          <div className="grid gap-4 sm:grid-cols-2">
            {[
              { label: "Billing Email", key: "billing_email", type: "email" },
              { label: "Company Name", key: "billing_company", type: "text" },
              { label: "Tax/VAT Number", key: "tax_vat", type: "text" },
              { label: "Country", key: "country", type: "text" },
              { label: "Currency", key: "currency", type: "text" },
              { label: "PO Number", key: "po_number", type: "text" },
            ].map(f => (
              <div key={f.key}>
                <label className="text-xs text-zinc-500">{f.label}</label>
                <input type={f.type} value={edit[f.key] || ""} onChange={e => setEdit({...edit, [f.key]: e.target.value})}
                  className="mt-1 w-full rounded-lg border border-zinc-800 bg-zinc-900/70 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-blue-600" />
              </div>
            ))}
            <div className="sm:col-span-2">
              <label className="text-xs text-zinc-500">Billing Address</label>
              <textarea value={edit.billing_address || ""} onChange={e => setEdit({...edit, billing_address: e.target.value})} rows={2}
                className="mt-1 w-full rounded-lg border border-zinc-800 bg-zinc-900/70 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-blue-600" />
            </div>
          </div>
          <button onClick={handleSaveSettings}
            className="mt-4 flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-2 text-xs font-medium hover:bg-blue-500">
            <Save className="h-3.5 w-3.5" /> Save Settings
          </button>
        </div>
      )}
    </div>
  );
}


