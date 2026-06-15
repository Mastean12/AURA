"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  Users, Search, Loader2, Plus, X, Mail, UserPlus, Shield,
  Clock, CheckCircle, XCircle, AlertTriangle, ChevronRight,
} from "lucide-react";

interface UserRow {
  id: number; full_name: string; email: string; role: string;
  status: string; last_login: string | null;
  workspace_count: number; document_count: number;
}

export default function UsersPage() {
  const router = useRouter();
  const [users, setUsers] = useState<UserRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [roleFilter, setRoleFilter] = useState("");
  const [showInvite, setShowInvite] = useState(false);
  const [inviteForm, setInviteForm] = useState({ full_name: "", email: "", role: "analyst", workspace_id: "" });
  const [inviting, setInviting] = useState(false);
  const [inviteResult, setInviteResult] = useState("");

  const token = typeof window !== "undefined" ? localStorage.getItem("aura_token") : "";
  const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

  function authHeaders() { return { "Content-Type": "application/json", Authorization: `Bearer ${token}` } as Record<string, string>; }

  async function fetchUsers() {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (search) params.set("search", search);
      if (statusFilter) params.set("status", statusFilter);
      if (roleFilter) params.set("role", roleFilter);
      const res = await fetch(`${apiBase}/api/v1/users/?${params}`, { headers: authHeaders() });
      const data = await res.json();
      setUsers(data.users || []);
    } catch { setUsers([]); }
    finally { setLoading(false); }
  }

  useEffect(() => { fetchUsers(); }, [search, statusFilter, roleFilter]);

  async function handleInvite() {
    setInviting(true);
    setInviteResult("");
    try {
      const res = await fetch(`${apiBase}/api/v1/users/invite`, {
        method: "POST", headers: authHeaders(),
        body: JSON.stringify({
          full_name: inviteForm.full_name,
          email: inviteForm.email,
          role: inviteForm.role,
          workspace_id: inviteForm.workspace_id ? Number(inviteForm.workspace_id) : null,
        }),
      });
      const data = await res.json();
      if (res.ok) {
        setInviteResult(`Invited! Temp password: ${data.temp_password || "sent via email"}`);
        setShowInvite(false);
        setInviteForm({ full_name: "", email: "", role: "analyst", workspace_id: "" });
        fetchUsers();
      } else {
        setInviteResult(data.detail || "Invite failed");
      }
    } catch { setInviteResult("Connection failed"); }
    finally { setInviting(false); }
  }

  async function handleStatusChange(userId: number, action: "activate" | "disable") {
    try {
      await fetch(`${apiBase}/api/v1/users/${userId}/${action}`, { method: "POST", headers: authHeaders() });
      fetchUsers();
    } catch {}
  }

  const roleBadge = (role: string) => {
    const colors: Record<string, string> = { admin: "bg-purple-900/50 text-purple-300", manager: "bg-blue-900/50 text-blue-300", analyst: "bg-emerald-900/50 text-emerald-300", viewer: "bg-zinc-800 text-zinc-400" };
    return <span className={`rounded px-1.5 py-0.5 text-[10px] font-medium ${colors[role] || "bg-zinc-800 text-zinc-400"}`}>{role}</span>;
  };

  const statusDot = (status: string) => {
    const colors: Record<string, string> = { active: "bg-emerald-500", pending: "bg-amber-500", disabled: "bg-red-500", suspended: "bg-zinc-600" };
    return <span className={`h-1.5 w-1.5 rounded-full ${colors[status] || "bg-zinc-600"}`} />;
  };

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">User Management</h1>
          <p className="text-sm text-zinc-500">Manage users, roles, and workspace access</p>
        </div>
        <button onClick={() => setShowInvite(true)}
          className="flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-2 text-xs font-medium hover:bg-blue-500">
          <UserPlus className="h-3.5 w-3.5" />Invite User
        </button>
      </div>

      {/* Stats */}
      <div className="grid gap-3 sm:grid-cols-4">
        {[
          { label: "Total Users", value: users.length, icon: Users, color: "text-blue-400" },
          { label: "Active", value: users.filter(u => u.status === "active").length, icon: CheckCircle, color: "text-emerald-400" },
          { label: "Pending", value: users.filter(u => u.status === "pending").length, icon: Clock, color: "text-amber-400" },
          { label: "Disabled", value: users.filter(u => u.status === "disabled").length, icon: XCircle, color: "text-red-400" },
        ].map(s => (
          <div key={s.label} className="rounded-lg border border-zinc-800 bg-zinc-900/50 p-3 flex items-center gap-3">
            <s.icon className={`h-5 w-5 ${s.color}`} />
            <div>
              <p className="text-lg font-semibold text-zinc-200">{s.value}</p>
              <p className="text-[10px] text-zinc-500">{s.label}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-zinc-600" />
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Search by name or email..."
            className="w-full rounded-lg border border-zinc-800 bg-zinc-900/70 pl-9 pr-3 py-2 text-xs text-zinc-100 placeholder-zinc-600 outline-none focus:border-blue-600" />
        </div>
        <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)}
          className="rounded-lg border border-zinc-800 bg-zinc-900/70 px-3 py-2 text-xs text-zinc-300 outline-none focus:border-blue-600">
          <option value="">All Status</option>
          <option value="active">Active</option>
          <option value="pending">Pending</option>
          <option value="disabled">Disabled</option>
        </select>
        <select value={roleFilter} onChange={e => setRoleFilter(e.target.value)}
          className="rounded-lg border border-zinc-800 bg-zinc-900/70 px-3 py-2 text-xs text-zinc-300 outline-none focus:border-blue-600">
          <option value="">All Roles</option>
          <option value="admin">Admin</option>
          <option value="manager">Manager</option>
          <option value="analyst">Analyst</option>
          <option value="viewer">Viewer</option>
        </select>
      </div>

      {/* Table */}
      {loading ? (
        <div className="space-y-2">{[1,2,3,4,5].map(i => <div key={i} className="h-14 animate-pulse rounded-xl bg-zinc-800/50" />)}</div>
      ) : (
        <div className="overflow-x-auto rounded-xl border border-zinc-800">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-zinc-800 bg-zinc-900/70 text-zinc-500">
                <th className="px-4 py-3 font-medium">User</th>
                <th className="px-4 py-3 font-medium">Email</th>
                <th className="px-4 py-3 font-medium">Role</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Workspaces</th>
                <th className="px-4 py-3 font-medium">Last Login</th>
                <th className="px-4 py-3 font-medium">Actions</th>
              </tr>
            </thead>
            <tbody>
              {users.map(u => (
                <tr key={u.id} className="border-b border-zinc-800/50 hover:bg-zinc-900/30 cursor-pointer"
                  onClick={() => router.push(`/users/${u.id}`)}>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <div className="flex h-7 w-7 items-center justify-center rounded-full bg-blue-600/20 text-[9px] font-semibold text-blue-400">
                        {u.full_name?.split(" ").map(n => n[0]).join("").toUpperCase().slice(0, 2) || "?"}
                      </div>
                      <span className="text-sm font-medium text-zinc-200">{u.full_name}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-zinc-400">{u.email}</td>
                  <td className="px-4 py-3">{roleBadge(u.role)}</td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-1.5">
                      {statusDot(u.status)}
                      <span className="capitalize text-zinc-400">{u.status}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-zinc-400">{u.workspace_count}</td>
                  <td className="px-4 py-3 text-zinc-500">
                    {u.last_login ? new Date(u.last_login).toLocaleDateString() : "Never"}
                  </td>
                  <td className="px-4 py-3" onClick={e => e.stopPropagation()}>
                    <div className="flex gap-1">
                      {u.status === "active" ? (
                        <button onClick={() => handleStatusChange(u.id, "disable")}
                          className="rounded px-1.5 py-0.5 text-[10px] text-amber-400 hover:bg-amber-950/30">Disable</button>
                      ) : (
                        <button onClick={() => handleStatusChange(u.id, "activate")}
                          className="rounded px-1.5 py-0.5 text-[10px] text-emerald-400 hover:bg-emerald-950/30">Activate</button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
              {users.length === 0 && (
                <tr><td colSpan={7} className="px-4 py-8 text-center text-zinc-600">No users found</td></tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Invite Dialog */}
      {showInvite && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={() => setShowInvite(false)}>
          <div className="w-full max-w-md rounded-xl border border-zinc-800 bg-zinc-900 p-6 shadow-xl" onClick={e => e.stopPropagation()}>
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold">Invite User</h3>
              <button onClick={() => setShowInvite(false)} className="text-zinc-500 hover:text-zinc-300"><X className="h-4 w-4" /></button>
            </div>
            <div className="space-y-3">
              <div>
                <label className="text-xs text-zinc-500">Full Name</label>
                <input value={inviteForm.full_name} onChange={e => setInviteForm({...inviteForm, full_name: e.target.value})}
                  className="mt-1 w-full rounded-lg border border-zinc-800 bg-zinc-900/70 px-3 py-2 text-xs text-zinc-100 outline-none focus:border-blue-600" />
              </div>
              <div>
                <label className="text-xs text-zinc-500">Email</label>
                <input value={inviteForm.email} onChange={e => setInviteForm({...inviteForm, email: e.target.value})}
                  className="mt-1 w-full rounded-lg border border-zinc-800 bg-zinc-900/70 px-3 py-2 text-xs text-zinc-100 outline-none focus:border-blue-600" />
              </div>
              <div>
                <label className="text-xs text-zinc-500">Role</label>
                <select value={inviteForm.role} onChange={e => setInviteForm({...inviteForm, role: e.target.value})}
                  className="mt-1 w-full rounded-lg border border-zinc-800 bg-zinc-900/70 px-3 py-2 text-xs text-zinc-300 outline-none focus:border-blue-600">
                  <option value="admin">Admin</option>
                  <option value="manager">Manager</option>
                  <option value="analyst">Analyst</option>
                  <option value="viewer">Viewer</option>
                </select>
              </div>
              {inviteResult && <p className="text-xs text-zinc-400 bg-zinc-800/50 rounded px-3 py-2">{inviteResult}</p>}
              <button onClick={handleInvite} disabled={inviting || !inviteForm.email}
                className="flex w-full items-center justify-center gap-1.5 rounded-lg bg-blue-600 py-2 text-xs font-medium hover:bg-blue-500 disabled:opacity-50">
                {inviting ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Mail className="h-3.5 w-3.5" />}
                Send Invitation
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
