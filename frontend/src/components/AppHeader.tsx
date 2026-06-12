"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  Sparkles, User, ChevronDown, Settings, LogOut, Bell, Brain,
  Building2, Users, CreditCard, Shield, Menu, X,
} from "lucide-react";

interface UserData {
  id: number;
  email: string;
  full_name: string;
  role: string;
  organization_id?: number;
}

interface Workspace {
  id: number;
  name: string;
  description: string;
}

export default function AppHeader({ onToggleSidebar }: { onToggleSidebar?: () => void }) {
  const router = useRouter();
  const [user, setUser] = useState<UserData | null>(null);
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [activeWs, setActiveWs] = useState<Workspace | null>(null);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showWsMenu, setShowWsMenu] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  const userRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<HTMLDivElement>(null);
  const notifRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const stored = localStorage.getItem("aura_user");
    const token = localStorage.getItem("aura_token");
    if (stored) setUser(JSON.parse(stored));

    if (token) {
      fetch("http://localhost:8000/api/v1/workspaces/", {
        headers: { Authorization: `Bearer ${token}` },
      })
        .then(r => r.json())
        .then(data => {
          setWorkspaces(data);
          if (data.length > 0) setActiveWs(data[0]);
        })
        .catch(() => {});
    }
  }, []);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (userRef.current && !userRef.current.contains(e.target as Node)) setShowUserMenu(false);
      if (wsRef.current && !wsRef.current.contains(e.target as Node)) setShowWsMenu(false);
      if (notifRef.current && !notifRef.current.contains(e.target as Node)) setShowNotifications(false);
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  function handleLogout() {
    localStorage.removeItem("aura_token");
    localStorage.removeItem("aura_user");
    document.cookie = "aura_token=; path=/; max-age=0";
    router.push("/login");
  }

  const initials = user?.full_name?.split(" ").map(n => n[0]).join("").toUpperCase().slice(0, 2) || "AU";

  const notifications = [
    { text: "New risk identified in financial data", time: "2m ago", color: "bg-red-500" },
    { text: "Forecast updated for Q3", time: "15m ago", color: "bg-amber-500" },
    { text: "Executive briefing generated", time: "1h ago", color: "bg-blue-500" },
    { text: "Document processed: Q2 Report.pdf", time: "2h ago", color: "bg-emerald-500" },
  ];

  return (
    <header className="sticky top-0 z-40 border-b border-zinc-800 bg-zinc-950/90 backdrop-blur-lg">
      <div className="flex h-14 items-center justify-between px-4">
        {/* Left */}
        <div className="flex items-center gap-3">
          {onToggleSidebar && (
            <button onClick={onToggleSidebar} className="lg:hidden p-1.5 text-zinc-500 hover:text-zinc-200">
              <Menu className="h-5 w-5" />
            </button>
          )}
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-blue-400" />
            <span className="text-sm font-semibold hidden sm:inline">AURA</span>
          </div>
          <div className="h-4 w-px bg-zinc-800 hidden sm:block" />
          <span className="text-xs text-zinc-500 hidden sm:inline">Executive Intelligence</span>
        </div>

        {/* Center - AI Presence */}
        <div className="hidden md:flex items-center gap-2 rounded-full border border-zinc-800 bg-zinc-900/70 px-3 py-1">
          <Brain className="h-3.5 w-3.5 text-blue-400" />
          <span className="text-[10px] text-zinc-400">AURA Advisor</span>
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />
          <span className="text-[10px] text-zinc-600">Ready</span>
        </div>

        {/* Right */}
        <div className="flex items-center gap-2">
          {/* Workspace */}
          {workspaces.length > 0 && (
            <div ref={wsRef} className="relative hidden md:block">
              <button onClick={() => setShowWsMenu(!showWsMenu)}
                className="flex items-center gap-1.5 rounded-lg border border-zinc-800 px-2.5 py-1.5 text-xs text-zinc-300 hover:bg-zinc-800/50">
                <Building2 className="h-3.5 w-3.5 text-zinc-500" />
                <span className="max-w-24 truncate">{activeWs?.name || "Workspace"}</span>
                <ChevronDown className="h-3 w-3 text-zinc-600" />
              </button>
              {showWsMenu && (
                <div className="absolute right-0 top-full mt-1 w-48 rounded-xl border border-zinc-800 bg-zinc-900 py-1 shadow-xl">
                  {workspaces.map(ws => (
                    <button key={ws.id} onClick={() => { setActiveWs(ws); setShowWsMenu(false); }}
                      className={`w-full px-3 py-2 text-left text-xs hover:bg-zinc-800 ${activeWs?.id === ws.id ? "text-blue-400" : "text-zinc-400"}`}>
                      {ws.name}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Notifications */}
          <div ref={notifRef} className="relative">
            <button onClick={() => setShowNotifications(!showNotifications)}
              className="relative rounded-lg p-1.5 text-zinc-500 hover:bg-zinc-800 hover:text-zinc-200">
              <Bell className="h-4 w-4" />
              <span className="absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full bg-red-500" />
            </button>
            {showNotifications && (
              <div className="absolute right-0 top-full mt-1 w-72 rounded-xl border border-zinc-800 bg-zinc-900 py-2 shadow-xl">
                <p className="px-3 pb-1 text-[10px] font-medium uppercase tracking-wider text-zinc-500">Notifications</p>
                <div className="space-y-0.5">
                  {notifications.map((n, i) => (
                    <div key={i} className="flex items-start gap-2 px-3 py-2 hover:bg-zinc-800/50">
                      <span className={`mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full ${n.color}`} />
                      <div className="min-w-0">
                        <p className="text-xs text-zinc-300">{n.text}</p>
                        <p className="text-[10px] text-zinc-600">{n.time}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* User Menu */}
          <div ref={userRef} className="relative">
            <button onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex items-center gap-2 rounded-lg px-2 py-1.5 hover:bg-zinc-800/50">
              <div className="flex h-7 w-7 items-center justify-center rounded-full bg-blue-600/20 text-[10px] font-semibold text-blue-400">
                {initials}
              </div>
              <div className="hidden md:block text-left">
                <p className="text-xs font-medium text-zinc-200">{user?.full_name || "User"}</p>
                <p className="text-[10px] text-zinc-500">
                  {user?.role ? user.role.charAt(0).toUpperCase() + user.role.slice(1) : "Viewer"}
                </p>
              </div>
              <ChevronDown className="h-3 w-3 text-zinc-600 hidden md:block" />
            </button>

            {showUserMenu && (
              <div className="absolute right-0 top-full mt-1 w-52 rounded-xl border border-zinc-800 bg-zinc-900 py-1 shadow-xl">
                <div className="border-b border-zinc-800 px-3 py-2">
                  <p className="text-xs font-medium text-zinc-200">{user?.full_name}</p>
                  <p className="text-[10px] text-zinc-500">{user?.email}</p>
                </div>
                <div className="py-1">
                  <button onClick={() => { router.push("/profile"); setShowUserMenu(false); }}
                    className="flex w-full items-center gap-2 px-3 py-1.5 text-xs text-zinc-400 hover:bg-zinc-800">
                    <User className="h-3.5 w-3.5" />My Profile
                  </button>
                  <button onClick={() => setShowUserMenu(false)}
                    className="flex w-full items-center gap-2 px-3 py-1.5 text-xs text-zinc-400 hover:bg-zinc-800">
                    <Building2 className="h-3.5 w-3.5" />Workspace Settings
                  </button>
                  <button onClick={() => setShowUserMenu(false)}
                    className="flex w-full items-center gap-2 px-3 py-1.5 text-xs text-zinc-400 hover:bg-zinc-800">
                    <Settings className="h-3.5 w-3.5" />Organization Settings
                  </button>
                  <button onClick={() => setShowUserMenu(false)}
                    className="flex w-full items-center gap-2 px-3 py-1.5 text-xs text-zinc-400 hover:bg-zinc-800">
                    <Shield className="h-3.5 w-3.5" />User Management
                  </button>
                  <button onClick={() => setShowUserMenu(false)}
                    className="flex w-full items-center gap-2 px-3 py-1.5 text-xs text-zinc-400 hover:bg-zinc-800">
                    <CreditCard className="h-3.5 w-3.5" />Billing
                  </button>
                </div>
                <div className="border-t border-zinc-800 pt-1">
                  <button onClick={handleLogout}
                    className="flex w-full items-center gap-2 px-3 py-1.5 text-xs text-red-400 hover:bg-zinc-800">
                    <LogOut className="h-3.5 w-3.5" />Sign Out
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
