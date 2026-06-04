"use client";

import { useEffect, useState } from "react";
import { health } from "@/lib/api";

export default function HealthCheck() {
  const [status, setStatus] = useState<"loading" | "online" | "offline">("loading");

  useEffect(() => {
    let cancelled = false;
    async function check() {
      try {
        const res = await health();
        if (!cancelled) setStatus(res.status === "ok" ? "online" : "offline");
      } catch {
        if (!cancelled) setStatus("offline");
      }
    }
    check();
    const interval = setInterval(check, 30000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  return (
    <div className="flex items-center gap-2 rounded-lg border border-zinc-800 px-3 py-2 text-xs">
      <span
        className={`h-2 w-2 rounded-full ${
          status === "loading"
            ? "animate-pulse bg-zinc-500"
            : status === "online"
            ? "bg-emerald-500"
            : "bg-red-500"
        }`}
      />
      <span className="text-zinc-500">
        {status === "loading"
          ? "Checking..."
          : status === "online"
          ? "Backend Connected"
          : "Backend Offline"}
      </span>
    </div>
  );
}
