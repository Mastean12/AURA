"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { User, Shield, Mail, LogOut, Loader2 } from "lucide-react";

export default function ProfilePage() {
  const router = useRouter();
  const [user, setUser] = useState<Record<string, unknown> | null>(null);

  useEffect(() => {
    if (!localStorage.getItem("aura_token")) router.push("/login");
  }, []);

  useEffect(() => {
    const stored = localStorage.getItem("aura_user");
    if (stored) setUser(JSON.parse(stored));
  }, []);

  function handleLogout() {
    localStorage.removeItem("aura_token");
    localStorage.removeItem("aura_user");
    document.cookie = "aura_token=; path=/; max-age=0";
    router.push("/login");
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6 p-6">
      <h1 className="text-2xl font-semibold tracking-tight">Profile</h1>
      {user ? (
        <div className="space-y-4">
          <div className="flex items-center gap-4 rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
            <div className="flex h-14 w-14 items-center justify-center rounded-full bg-blue-600/20">
              <User className="h-6 w-6 text-blue-400" />
            </div>
            <div>
              <p className="text-lg font-medium text-zinc-200">{user.full_name as string}</p>
              <p className="text-sm text-zinc-500">{user.email as string}</p>
            </div>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4">
              <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-zinc-500 mb-1">
                <Shield className="h-3.5 w-3.5" />Role
              </div>
              <p className="text-sm font-semibold text-zinc-200 capitalize">{user.role as string}</p>
            </div>
            <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-4">
              <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-wider text-zinc-500 mb-1">
                <Mail className="h-3.5 w-3.5" />Email
              </div>
              <p className="text-sm font-semibold text-zinc-200">{user.email as string}</p>
            </div>
          </div>
          <button onClick={handleLogout}
            className="flex items-center gap-2 rounded-xl border border-red-800/30 bg-red-950/20 px-4 py-2.5 text-sm text-red-400 hover:bg-red-950/40">
            <LogOut className="h-4 w-4" />Sign Out
          </button>
        </div>
      ) : (
        <p className="text-sm text-zinc-600">Not logged in. <a href="/login" className="text-blue-400 hover:underline">Sign in</a></p>
      )}
    </div>
  );
}
