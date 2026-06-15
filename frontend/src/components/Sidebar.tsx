"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, Sparkles, Upload, MessageSquare, BarChart3,
  TrendingUp, Building2, Brain, FileText, ScrollText, Shield,
  Users, Settings, AlertTriangle, Target,
} from "lucide-react";

const navGroups = [
  {
    label: "Overview",
    items: [
      { href: "/dashboard", label: "Executive Command Center", icon: LayoutDashboard },
    ],
  },
  {
    label: "Intelligence",
    items: [
      { href: "/upload", label: "Document Upload", icon: Upload },
      { href: "/chat", label: "Knowledge Base", icon: MessageSquare },
      { href: "/analytics", label: "Analytics", icon: BarChart3 },
      { href: "/predictive", label: "Predictive", icon: TrendingUp },
    ],
  },
  {
    label: "Insights",
    items: [
      { href: "/executive", label: "Executive Insights", icon: Brain },
      { href: "/enterprise", label: "Enterprise", icon: Building2 },
    ],
  },
  {
    label: "Reports",
    items: [
      { href: "/reports", label: "Executive Briefings", icon: ScrollText },
    ],
  },
  {
    label: "Administration",
    items: [
      { href: "/workspace/settings", label: "Workspace Settings", icon: Settings },
      { href: "/admin/ai-monitoring", label: "AI Monitoring", icon: Shield },
    ],
  },
];

export default function Sidebar() {
  const pathname = usePathname();

  const isActive = (href: string) => {
    if (href === "/dashboard") return pathname === "/dashboard" || pathname === "/";
    return pathname.startsWith(href);
  };

  return (
    <aside className="flex h-screen w-56 flex-col border-r border-zinc-800 bg-zinc-900/30">
      <div className="flex items-center gap-2 border-b border-zinc-800 px-5 py-4">
        <Sparkles className="h-5 w-5 text-blue-400" />
        <span className="text-sm font-semibold tracking-tight">AURA</span>
      </div>

      <nav className="flex-1 overflow-y-auto px-2 py-3">
        {navGroups.map((group) => (
          <div key={group.label} className="mb-4">
            <p className="mb-1 px-3 text-[10px] font-medium uppercase tracking-wider text-zinc-600">
              {group.label}
            </p>
            {group.items.map(({ href, label, icon: Icon }) => (
              <Link key={`${href}-${label}`} href={href}
                className={`flex items-center gap-2.5 rounded-lg px-3 py-2 text-xs font-medium transition-colors ${
                  isActive(href)
                    ? "bg-blue-600/15 text-blue-300"
                    : "text-zinc-400 hover:bg-zinc-800/50 hover:text-zinc-200"
                }`}>
                <Icon className="h-3.5 w-3.5 shrink-0" />
                {label}
              </Link>
            ))}
          </div>
        ))}
      </nav>

      <div className="border-t border-zinc-800 px-4 py-3">
        <p className="text-[10px] text-zinc-700 text-center">v1.0 · Enterprise</p>
      </div>
    </aside>
  );
}
