"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  Settings, Users, Building2, Save, Trash2, Plus, X, Loader2,
  FileText, BarChart3, Brain, Shield, Check, AlertTriangle, RefreshCw,
  RotateCcw, Mail,
} from "lucide-react";
import {
  listWorkspaces, getWorkspace, updateWorkspace, deleteWorkspace,
  addWorkspaceMember, updateMemberRole, removeMember, getWorkspaceSettings,
  updateWorkspaceSettings, createWorkspace,
} from "@/lib/api";

interface Member {
  id: number; user_id: number; email: string; full_name: string;
  role: string; status: string; joined_at: string | null;
}

interface WorkspaceData {
  id: number; name: string; description: string; workspace_type: string;
  status: string; owner_id: number; created_at: string;
  member_count: number; doc_count: number;
  members: Member[];
  settings: Record<string, unknown>;
}

export default function WorkspaceSettingsPage() {
  const router = useRouter();
  const [workspaces, setWorkspaces] = useState<any[]>([]);
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [data, setData] = useState<WorkspaceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [editName, setEditName] = useState("");
  const [editDesc, setEditDesc] = useState("");
  const [editType, setEditType] = useState("department");
  const [activeTab, setActiveTab] = useState("overview");
  const [notification, setNotification] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [newType, setNewType] = useState("department");
  const [addRole, setAddRole] = useState("analyst");
  const [availableUsers, setAvailableUsers] = useState<{id: number; full_name: string; email: string}[]>([]);
  const [selectedUserId, setSelectedUserId] = useState<number | null>(null);
  const [showAddMember, setShowAddMember] = useState(false);

  useEffect(() => {
    listWorkspaces().then(wss => {
      setWorkspaces(wss);
      const active = wss.find((w: any) => w.status === "active");
      if (active) { setSelectedId(active.id); loadWorkspace(active.id); }
      else setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  async function loadWorkspace(id: number) {
    setLoading(true);
    setSelectedId(id);
    try {
      const ws = await getWorkspace(id);
      setData(ws);
      setEditName(ws.name);
      setEditDesc(ws.description || "");
      setEditType(ws.workspace_type);
    } catch { setData(null); }
    finally { setLoading(false); }
  }

  async function refreshList() {
    const wss = await listWorkspaces();
    setWorkspaces(wss);
  }

  async function handleSave() {
    if (!selectedId) return;
    setSaving(true);
    try {
      await updateWorkspace(selectedId, { name: editName, description: editDesc, workspace_type: editType });
      showNotification("Workspace updated");
      loadWorkspace(selectedId);
    } catch { showNotification("Save failed"); }
    finally { setSaving(false); }
  }

  async function handleDelete() {
    if (!selectedId) return;
    if (!confirm("Archive this workspace? It can be restored later.")) return;
    try {
      await deleteWorkspace(selectedId);
      showNotification("Workspace archived");
      await refreshList();
      setSelectedId(null); setData(null);
    } catch { showNotification("Archive failed"); }
  }

  async function handleRestore(wsId: number) {
    try {
      const token = localStorage.getItem("aura_token");
      await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/workspaces/${wsId}/restore`, {
        method: "POST", headers: { Authorization: `Bearer ${token}` },
      });
      showNotification("Workspace restored");
      await refreshList();
      loadWorkspace(wsId);
    } catch { showNotification("Restore failed"); }
  }

  async function handleCreate() {
    if (!newName.trim()) return;
    try {
      await createWorkspace({ name: newName, description: newDesc, workspace_type: newType });
      showNotification("Workspace created");
      setShowCreate(false); setNewName(""); setNewDesc("");
      await refreshList();
    } catch { showNotification("Create failed"); }
  }

  async function loadAvailableUsers() {
    if (!selectedId) return;
    const token = localStorage.getItem("aura_token");
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/workspaces/${selectedId}/available-users`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setAvailableUsers(await res.json());
    } catch {}
  }

  async function handleAddMember() {
    if (!selectedId || !selectedUserId) return;
    const token = localStorage.getItem("aura_token");
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/v1/workspaces/${selectedId}/members`,
        { method: "POST", headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
          body: JSON.stringify({ user_id: selectedUserId, role: addRole }) }
      );
      const data = await res.json();
      showNotification(data.detail || "Member added");
      setSelectedUserId(null);
      setShowAddMember(false);
      loadWorkspace(selectedId);
    } catch { showNotification("Failed to add member"); }
  }

  async function handleRoleChange(userId: number, role: string) {
    if (!selectedId) return;
    try { await updateMemberRole(selectedId, userId, role); showNotification("Role updated"); loadWorkspace(selectedId); }
    catch { showNotification("Role update failed"); }
  }

  async function handleRemoveMember(userId: number) {
    if (!selectedId) return;
    try { await removeMember(selectedId, userId); showNotification("Member removed"); loadWorkspace(selectedId); }
    catch { showNotification("Remove failed"); }
  }

  async function handleToggleSetting(key: string, current: boolean) {
    if (!selectedId) return;
    try { await updateWorkspaceSettings(selectedId, { [key]: current ? 0 : 1 }); showNotification("Setting updated"); loadWorkspace(selectedId); }
    catch { showNotification("Update failed"); }
  }

  function showNotification(msg: string) { setNotification(msg); setTimeout(() => setNotification(""), 3000); }

  const activeWs = workspaces.filter((w: any) => w.status === "active");
  const archivedWs = workspaces.filter((w: any) => w.status === "archived");

  const tabs = [
    { id: "overview", label: "Overview", icon: Building2 },
    { id: "members", label: "Members", icon: Users },
    { id: "settings", label: "AI Settings", icon: Brain },
    { id: "access", label: "Access Controls", icon: Shield },
  ];

  return (
    <div className="mx-auto max-w-5xl space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Workspace Settings</h1>
          <p className="text-sm text-zinc-500">Manage workspaces, members, and permissions</p>
        </div>
      </div>

      {/* Active workspaces */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">Active Workspaces</p>
          <button onClick={() => setShowCreate(!showCreate)}
            className="flex items-center gap-1 rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-medium hover:bg-blue-500">
            <Plus className="h-3.5 w-3.5" />New Workspace
          </button>
        </div>
        <div className="flex flex-wrap gap-2">
          {activeWs.map((ws: any) => (
            <button key={ws.id} onClick={() => loadWorkspace(ws.id)}
              className={`rounded-xl border px-3 py-1.5 text-xs transition-colors ${
                selectedId === ws.id ? "border-blue-600 bg-blue-600/20 text-blue-300" : "border-zinc-800 text-zinc-400 hover:border-zinc-700"
              }`}>
              {ws.name}
            </button>
          ))}
          {activeWs.length === 0 && <span className="text-xs text-zinc-600">No active workspaces</span>}
        </div>
      </div>

      {/* Archived workspaces */}
      {archivedWs.length > 0 && (
        <div>
          <p className="text-xs font-medium uppercase tracking-wider text-zinc-600 mb-2">Archived Workspaces</p>
          <div className="flex flex-wrap gap-2">
            {archivedWs.map((ws: any) => (
              <div key={ws.id} className="flex items-center gap-1 rounded-xl border border-zinc-800 bg-zinc-900/30 px-3 py-1.5 text-xs text-zinc-500">
                <span className="line-through">{ws.name}</span>
                <button onClick={() => handleRestore(ws.id)}
                  className="ml-1 rounded bg-zinc-800 px-1.5 py-0.5 text-[10px] text-emerald-400 hover:bg-zinc-700">
                  <RotateCcw className="h-3 w-3 inline mr-0.5" />Restore
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Create workspace dialog */}
      {showCreate && (
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/70 p-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium">Create Workspace</h3>
            <button onClick={() => setShowCreate(false)} className="text-zinc-500 hover:text-zinc-300"><X className="h-4 w-4" /></button>
          </div>
          <div className="grid gap-3 sm:grid-cols-3 mb-3">
            <input value={newName} onChange={e => setNewName(e.target.value)} placeholder="Workspace name"
              className="rounded-lg border border-zinc-800 bg-zinc-900/70 px-3 py-2 text-xs text-zinc-100 placeholder-zinc-600 outline-none focus:border-blue-600" />
            <input value={newDesc} onChange={e => setNewDesc(e.target.value)} placeholder="Description (optional)"
              className="rounded-lg border border-zinc-800 bg-zinc-900/70 px-3 py-2 text-xs text-zinc-100 placeholder-zinc-600 outline-none focus:border-blue-600" />
            <select value={newType} onChange={e => setNewType(e.target.value)}
              className="rounded-lg border border-zinc-800 bg-zinc-900/70 px-3 py-2 text-xs text-zinc-300 outline-none focus:border-blue-600">
              <option value="department">Department</option><option value="project">Project</option>
              <option value="team">Team</option><option value="custom">Custom</option>
            </select>
          </div>
          <button onClick={handleCreate} className="rounded-lg bg-blue-600 px-4 py-2 text-xs font-medium hover:bg-blue-500">Create</button>
        </div>
      )}

      {notification && (
        <div className="rounded-lg border border-emerald-800/30 bg-emerald-950/20 px-4 py-2 text-xs text-emerald-400">{notification}</div>
      )}

      {loading ? (
        <div className="space-y-4">{[1,2,3].map(i => <div key={i} className="h-24 animate-pulse rounded-xl bg-zinc-800/50" />)}</div>
      ) : data ? (
        <>
          <div className="flex gap-1 rounded-xl border border-zinc-800 bg-zinc-900/30 p-1">
            {tabs.map(tab => (
              <button key={tab.id} onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-1.5 rounded-lg px-4 py-2 text-xs font-medium transition-colors flex-1 justify-center ${
                  activeTab === tab.id ? "bg-blue-600/20 text-blue-300" : "text-zinc-500 hover:text-zinc-300"
                }`}>
                <tab.icon className="h-3.5 w-3.5" />{tab.label}
              </button>
            ))}
          </div>

          {activeTab === "overview" && (
            <div className="space-y-4">
              <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
                <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500 mb-4">Workspace Overview</h2>
                <div className="grid gap-4 sm:grid-cols-2">
                  {[
                    { label: "Name", value: data.name },
                    { label: "Description", value: data.description || "—" },
                    { label: "Type", value: data.workspace_type },
                    { label: "Status", value: data.status },
                    { label: "Members", value: data.member_count },
                    { label: "Documents", value: data.doc_count },
                    { label: "Created", value: data.created_at ? new Date(data.created_at).toLocaleDateString() : "—" },
                  ].map(m => (
                    <div key={m.label} className="rounded-lg bg-zinc-800/30 p-3">
                      <p className="text-[10px] uppercase tracking-wider text-zinc-500">{m.label}</p>
                      <p className="mt-1 text-sm font-medium text-zinc-200">{m.value}</p>
                    </div>
                  ))}
                </div>
              </div>

              <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
                <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500 mb-4">Edit Workspace</h2>
                <div className="space-y-4">
                  <div>
                    <label className="text-xs text-zinc-400">Name</label>
                    <input value={editName} onChange={e => setEditName(e.target.value)}
                      className="mt-1 w-full rounded-lg border border-zinc-800 bg-zinc-900/70 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-blue-600" />
                  </div>
                  <div>
                    <label className="text-xs text-zinc-400">Description</label>
                    <textarea value={editDesc} onChange={e => setEditDesc(e.target.value)} rows={3}
                      className="mt-1 w-full rounded-lg border border-zinc-800 bg-zinc-900/70 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-blue-600" />
                  </div>
                  <div>
                    <label className="text-xs text-zinc-400">Type</label>
                    <select value={editType} onChange={e => setEditType(e.target.value)}
                      className="mt-1 w-full rounded-lg border border-zinc-800 bg-zinc-900/70 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-blue-600">
                      <option value="department">Department</option><option value="project">Project</option>
                      <option value="team">Team</option><option value="custom">Custom</option>
                    </select>
                  </div>
                  <div className="flex gap-2">
                    <button onClick={handleSave} disabled={saving}
                      className="flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-2 text-xs font-medium hover:bg-blue-500 disabled:opacity-50">
                      {saving ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Save className="h-3.5 w-3.5" />}Save
                    </button>
                    <button onClick={handleDelete}
                      className="flex items-center gap-1.5 rounded-lg border border-amber-800/30 bg-amber-950/20 px-4 py-2 text-xs text-amber-400 hover:bg-amber-950/40">
                      <Trash2 className="h-3.5 w-3.5" />Archive
                    </button>
                  </div>
                </div>
              </div>

              <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
                <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500 mb-4">Workspace Resources</h2>
                <div className="grid gap-3 sm:grid-cols-4">
                  {[
                    { label: "Documents", value: data.doc_count, icon: FileText, color: "text-blue-400" },
                    { label: "Reports", value: "—", icon: BarChart3, color: "text-emerald-400" },
                    { label: "Analytics", value: "—", icon: Brain, color: "text-purple-400" },
                    { label: "Briefings", value: "—", icon: FileText, color: "text-amber-400" },
                  ].map(r => (
                    <div key={r.label} className="rounded-lg border border-zinc-800 bg-zinc-900/70 p-3 text-center">
                      <r.icon className={`mx-auto h-5 w-5 ${r.color} mb-1`} />
                      <p className="text-lg font-semibold text-zinc-200">{r.value}</p>
                      <p className="text-[10px] text-zinc-500">{r.label}</p>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === "members" && (
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500">Members ({data.members.length})</h2>
              </div>

              <div className="mb-4">
                {showAddMember ? (
                  <div className="flex gap-2">
                    <select value={selectedUserId ?? ""} onChange={e => setSelectedUserId(Number(e.target.value) || null)}
                      className="flex-1 rounded-lg border border-zinc-800 bg-zinc-900/70 px-3 py-2 text-xs text-zinc-300 outline-none focus:border-blue-600"
                      onFocus={loadAvailableUsers}>
                      <option value="">Select a user to add...</option>
                      {availableUsers.map(u => (
                        <option key={u.id} value={u.id}>{u.full_name} ({u.email})</option>
                      ))}
                    </select>
                    <select value={addRole} onChange={e => setAddRole(e.target.value)}
                      className="rounded-lg border border-zinc-800 bg-zinc-900/70 px-3 py-2 text-xs text-zinc-300 outline-none focus:border-blue-600">
                      <option value="workspace_admin">Admin</option><option value="manager">Manager</option>
                      <option value="analyst">Analyst</option><option value="viewer">Viewer</option>
                    </select>
                    <button onClick={handleAddMember} disabled={!selectedUserId}
                      className="flex items-center gap-1 rounded-lg bg-blue-600 px-3 py-2 text-xs font-medium hover:bg-blue-500 disabled:opacity-50">
                      <Plus className="h-3.5 w-3.5" />Add
                    </button>
                    <button onClick={() => setShowAddMember(false)}
                      className="rounded-lg border border-zinc-800 px-3 py-2 text-xs text-zinc-500 hover:text-zinc-300">Cancel</button>
                  </div>
                ) : (
                  <button onClick={() => { setShowAddMember(true); loadAvailableUsers(); }}
                    className="flex items-center gap-1 rounded-lg bg-blue-600 px-3 py-2 text-xs font-medium hover:bg-blue-500">
                    <Plus className="h-3.5 w-3.5" />Add Existing User
                  </button>
                )}
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead>
                    <tr className="border-b border-zinc-800 text-zinc-500">
                      <th className="px-3 py-2 font-medium">User</th>
                      <th className="px-3 py-2 font-medium">Email</th>
                      <th className="px-3 py-2 font-medium">Role</th>
                      <th className="px-3 py-2 font-medium">Status</th>
                      <th className="px-3 py-2 font-medium">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.members.map(m => (
                      <tr key={m.id} className="border-b border-zinc-800/50">
                        <td className="px-3 py-2">
                          <div className="flex items-center gap-2">
                            <div className="flex h-6 w-6 items-center justify-center rounded-full bg-blue-600/20 text-[9px] font-semibold text-blue-400">
                              {m.full_name?.split(" ").map((n: string) => n[0]).join("").toUpperCase().slice(0, 2) || "?"}
                            </div>
                            <span className="text-zinc-300">{m.full_name || `User #${m.user_id}`}</span>
                          </div>
                        </td>
                        <td className="px-3 py-2 text-zinc-400">{m.email || "—"}</td>
                        <td className="px-3 py-2">
                          <select value={m.role} onChange={e => handleRoleChange(m.user_id, e.target.value)}
                            className="rounded border border-zinc-800 bg-zinc-900 px-2 py-0.5 text-xs text-zinc-300 outline-none">
                            <option value="workspace_admin">Admin</option><option value="manager">Manager</option>
                            <option value="analyst">Analyst</option><option value="viewer">Viewer</option>
                          </select>
                        </td>
                        <td className="px-3 py-2">
                          <span className={`flex items-center gap-1 ${m.status === "active" ? "text-emerald-400" : "text-zinc-500"}`}>
                            <span className={`h-1.5 w-1.5 rounded-full ${m.status === "active" ? "bg-emerald-500" : "bg-zinc-600"}`} />
                            {m.status}
                          </span>
                        </td>
                        <td className="px-3 py-2">
                          <button onClick={() => handleRemoveMember(m.user_id)}
                            className="text-zinc-600 hover:text-red-400"><Trash2 className="h-3.5 w-3.5" /></button>
                        </td>
                      </tr>
                    ))}
                    {data.members.length === 0 && (
                      <tr><td colSpan={5} className="px-3 py-4 text-center text-zinc-600">No members</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {activeTab === "settings" && (
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
              <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500 mb-4">AI Settings</h2>
              <div className="space-y-4">
                <div>
                  <label className="text-xs text-zinc-400">Default AI Provider</label>
                  <select value={(data.settings?.ai_provider as string) || "gemini"}
                    onChange={e => handleToggleSetting("ai_provider", false)}
                    className="mt-1 w-full rounded-lg border border-zinc-800 bg-zinc-900/70 px-3 py-2 text-sm text-zinc-100 outline-none focus:border-blue-600">
                    <option value="gemini">Gemini</option><option value="openai">OpenAI</option>
                    <option value="claude">Claude (Future)</option>
                  </select>
                </div>
                <div className="space-y-2">
                  <p className="text-xs text-zinc-500 mb-2">AI Features</p>
                  {[
                    { key: "executive_insights", label: "Executive Insights" },
                    { key: "forecasting", label: "Forecasting" },
                    { key: "risk_analysis", label: "Risk Analysis" },
                    { key: "recommendations", label: "Recommendations" },
                  ].map(f => (
                    <label key={f.key} className="flex items-center justify-between rounded-lg bg-zinc-800/30 px-4 py-3">
                      <span className="text-xs text-zinc-300">{f.label}</span>
                      <button onClick={() => handleToggleSetting(f.key, !!(data.settings as any)[f.key])}
                        className={`relative h-5 w-9 rounded-full transition-colors ${(data.settings as any)[f.key] ? "bg-blue-600" : "bg-zinc-700"}`}>
                        <span className={`absolute left-0.5 top-0.5 h-4 w-4 rounded-full bg-white transition-transform ${(data.settings as any)[f.key] ? "translate-x-4" : ""}`} />
                      </button>
                    </label>
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === "access" && (
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
              <h2 className="text-sm font-medium uppercase tracking-wider text-zinc-500 mb-4">Data Access Controls</h2>
              <div className="space-y-2">
                {[
                  { key: "allow_uploads", label: "Allow Uploads" },
                  { key: "allow_ai_chat", label: "Allow AI Chat" },
                  { key: "allow_analytics", label: "Allow Analytics" },
                  { key: "allow_pdf_export", label: "Allow PDF Export" },
                  { key: "allow_executive_reports", label: "Allow Executive Reports" },
                ].map(f => (
                  <label key={f.key} className="flex items-center justify-between rounded-lg bg-zinc-800/30 px-4 py-3">
                    <div>
                      <span className="text-xs text-zinc-300">{f.label}</span>
                      <p className="text-[10px] text-zinc-600">Workspace admin controls this setting</p>
                    </div>
                    <button onClick={() => handleToggleSetting(f.key, !!(data.settings as any)[f.key])}
                      className={`relative h-5 w-9 rounded-full transition-colors ${(data.settings as any)[f.key] ? "bg-blue-600" : "bg-zinc-700"}`}>
                      <span className={`absolute left-0.5 top-0.5 h-4 w-4 rounded-full bg-white transition-transform ${(data.settings as any)[f.key] ? "translate-x-4" : ""}`} />
                    </button>
                  </label>
                ))}
              </div>
            </div>
          )}
        </>
      ) : (
        <p className="text-sm text-zinc-600 text-center py-12">Select a workspace to manage or create a new one.</p>
      )}
    </div>
  );
}
