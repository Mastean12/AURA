"use client";

import { useState, useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  User, Mail, Shield, Clock, FileText, Brain, Building2,
  Loader2, ArrowLeft, CheckCircle, XCircle, AlertTriangle,
  ChevronRight,
} from "lucide-react";

export default function UserDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [data, setData] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(true);

  const token = typeof window !== "undefined" ? localStorage.getItem("aura_token") : "";
  const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const authH = { "Content-Type": "application/json", Authorization: `Bearer ${token}` } as Record<string, string>;

  useEffect(() => {
    if (!id) return;
    fetch(`${apiBase}/api/v1/users/${id}`, { headers: authH })
      .then(r => r.json()).then(setData).catch(() => {}).finally(() => setLoading(false));
  }, [id]);

  async function handleAction(action: string) {
    await fetch(`${apiBase}/api/v1/users/${id}/${action}`, { method: "POST", headers: authH });
    const res = await fetch(`${apiBase}/api/v1/users/${id}`, { headers: authH });
    setData(await res.json());
  }

  if (loading) return <div className="mx-auto max-w-4xl p-6 space-y-4">{[1,2,3].map(i => <div key={i} className="h-24 animate-pulse rounded-xl bg-zinc-800/50" />)}</div>;

  const perms = [
    { perm: "Upload Documents", admin: "✔", manager: "✔", analyst: "✔", viewer: "—" },
    { perm: "AI Chat", admin: "✔", manager: "✔", analyst: "✔", viewer: "—" },
    { perm: "Run Analysis", admin: "✔", manager: "✔", analyst: "✔", viewer: "—" },
    { perm: "View Reports", admin: "✔", manager: "✔", analyst: "✔", viewer: "✔" },
    { perm: "Create Reports", admin: "✔", manager: "✔", analyst: "✔", viewer: "—" },
    { perm: "Manage Users", admin: "✔", manager: "—", analyst: "—", viewer: "—" },
    { perm: "Manage Workspaces", admin: "✔", manager: "✔", analyst: "—", viewer: "—" },
    { perm: "Billing", admin: "✔", manager: "—", analyst: "—", viewer: "—" },
  ];

  return (
    <div className="mx-auto max-w-4xl space-y-6 p-6">
      <button onClick={() => router.push("/users")} className="flex items-center gap-1 text-xs text-zinc-500 hover:text-zinc-300">
        <ArrowLeft className="h-3.5 w-3.5" />Back to Users
      </button>

      {/* Profile header */}
      <div className="flex items-center gap-4 rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-blue-600/20 text-lg font-semibold text-blue-400">
          {data.full_name?.split(" ").map((n: string) => n[0]).join("").toUpperCase().slice(0, 2) || "?"}
        </div>
        <div className="flex-1">
          <p className="text-lg font-semibold text-zinc-200">{data.full_name}</p>
          <p className="text-sm text-zinc-500">{data.email}</p>
          <div className="flex items-center gap-2 mt-1">
            <span className="rounded bg-purple-900/50 px-1.5 py-0.5 text-[10px] font-medium text-purple-300 capitalize">{data.role}</span>
            <div className="flex items-center gap-1">
              {data.status === "active" ? <CheckCircle className="h-3 w-3 text-emerald-400" /> : <XCircle className="h-3 w-3 text-red-400" />}
              <span className="text-[10px] text-zinc-500 capitalize">{data.status}</span>
            </div>
          </div>
        </div>
        <div className="flex gap-2">
          {data.status !== "disabled" ? (
            <button onClick={() => handleAction("disable")}
              className="rounded-lg border border-amber-800/30 bg-amber-950/20 px-3 py-1.5 text-[10px] text-amber-400 hover:bg-amber-950/40">
              Disable
            </button>
          ) : (
            <button onClick={() => handleAction("activate")}
              className="rounded-lg border border-emerald-800/30 bg-emerald-950/20 px-3 py-1.5 text-[10px] text-emerald-400 hover:bg-emerald-950/40">
              Activate
            </button>
          )}
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Details */}
        <div className="space-y-4">
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
            <h2 className="text-xs font-medium uppercase tracking-wider text-zinc-500 mb-3">Account Details</h2>
            <div className="space-y-2">
              {[
                { label: "User ID", value: `#${data.id}`, icon: User },
                { label: "Email", value: data.email, icon: Mail },
                { label: "Role", value: data.role, icon: Shield },
                { label: "Status", value: data.status, icon: data.status === "active" ? CheckCircle : XCircle },
                { label: "Created", value: data.created_at ? new Date(data.created_at).toLocaleDateString() : "—", icon: Clock },
                { label: "Last Login", value: data.last_login ? new Date(data.last_login).toLocaleDateString() : "Never", icon: Clock },
              ].map(f => (
                <div key={f.label} className="flex items-center gap-2 text-xs">
                  <f.icon className="h-3.5 w-3.5 text-zinc-600" />
                  <span className="text-zinc-500 w-20">{f.label}</span>
                  <span className="text-zinc-300">{f.value}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Activity */}
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
            <h2 className="text-xs font-medium uppercase tracking-wider text-zinc-500 mb-3">Activity</h2>
            <div className="grid grid-cols-2 gap-3">
              {[
                { label: "Documents", value: data.document_count || 0, icon: FileText, color: "text-blue-400" },
                { label: "AI Requests", value: data.ai_requests || 0, icon: Brain, color: "text-purple-400" },
                { label: "Workspaces", value: data.workspaces?.length || 0, icon: Building2, color: "text-emerald-400" },
              ].map(m => (
                <div key={m.label} className="rounded-lg bg-zinc-800/30 p-3 text-center">
                  <m.icon className={`mx-auto h-4 w-4 ${m.color} mb-1`} />
                  <p className="text-lg font-semibold text-zinc-200">{m.value}</p>
                  <p className="text-[10px] text-zinc-500">{m.label}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="space-y-4">
          {/* Workspaces */}
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
            <h2 className="text-xs font-medium uppercase tracking-wider text-zinc-500 mb-3">Workspaces ({data.workspaces?.length || 0})</h2>
            {data.workspaces?.length > 0 ? (
              <div className="space-y-1">
                {data.workspaces.map((ws: any) => (
                  <div key={ws.workspace_id} className="flex items-center justify-between rounded-lg bg-zinc-800/30 px-3 py-2">
                    <div className="flex items-center gap-2">
                      <Building2 className="h-3.5 w-3.5 text-zinc-500" />
                      <span className="text-xs text-zinc-300">{ws.name}</span>
                    </div>
                    <span className="rounded bg-zinc-800 px-1.5 py-0.5 text-[10px] text-zinc-400 capitalize">{ws.role}</span>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-zinc-600">No workspace assignments</p>
            )}
          </div>

          {/* Permissions matrix */}
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
            <h2 className="text-xs font-medium uppercase tracking-wider text-zinc-500 mb-3">Permissions</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-[10px]">
                <thead>
                  <tr className="text-zinc-600">
                    <th className="text-left px-2 py-1 font-medium">Permission</th>
                    <th className="px-2 py-1 font-medium">Admin</th>
                    <th className="px-2 py-1 font-medium">Mgr</th>
                    <th className="px-2 py-1 font-medium">Analyst</th>
                    <th className="px-2 py-1 font-medium">Viewer</th>
                  </tr>
                </thead>
                <tbody>
                  {perms.map(p => (
                    <tr key={p.perm} className="border-t border-zinc-800/50">
                      <td className="px-2 py-1.5 text-zinc-400">{p.perm}</td>
                      <td className={`px-2 py-1.5 text-center font-medium ${p.admin === "✔" ? "text-emerald-400" : "text-zinc-700"}`}>{p.admin}</td>
                      <td className={`px-2 py-1.5 text-center font-medium ${p.manager === "✔" ? "text-emerald-400" : "text-zinc-700"}`}>{p.manager}</td>
                      <td className={`px-2 py-1.5 text-center font-medium ${p.analyst === "✔" ? "text-emerald-400" : "text-zinc-700"}`}>{p.analyst}</td>
                      <td className={`px-2 py-1.5 text-center font-medium ${p.viewer === "✔" ? "text-emerald-400" : "text-zinc-700"}`}>{p.viewer}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
