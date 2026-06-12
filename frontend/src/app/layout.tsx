"use client";

import { useState } from "react";
import "./globals.css";
import Sidebar from "@/components/Sidebar";
import AppHeader from "@/components/AppHeader";

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const [mobileSidebar, setMobileSidebar] = useState(false);

  return (
    <html lang="en">
      <body className="bg-zinc-950 text-zinc-100 antialiased">
        <div className="flex h-screen overflow-hidden">
          {/* Desktop sidebar */}
          <div className="hidden lg:block">
            <Sidebar />
          </div>

          {/* Mobile sidebar overlay */}
          {mobileSidebar && (
            <div className="fixed inset-0 z-50 lg:hidden">
              <div className="absolute inset-0 bg-black/60" onClick={() => setMobileSidebar(false)} />
              <div className="absolute left-0 top-0 h-full">
                <Sidebar />
              </div>
            </div>
          )}

          <div className="flex flex-1 flex-col overflow-hidden">
            <AppHeader onToggleSidebar={() => setMobileSidebar(!mobileSidebar)} />
            <main className="flex-1 overflow-y-auto">{children}</main>
          </div>
        </div>
      </body>
    </html>
  );
}
