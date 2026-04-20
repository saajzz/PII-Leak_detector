import { ReactNode } from "react";
import { DashboardSidebar } from "./DashboardSidebar";
import { useLocation } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

const pageTitles: Record<string, string> = {
  "/": "Overview",
  "/incidents": "Incidents",
  "/findings": "Findings",
  "/analytics": "Analytics",
  "/canaries": "Canaries",
};

export function DashboardLayout({ children }: { children: ReactNode }) {
  const location = useLocation();
  const title = pageTitles[location.pathname] || "Dashboard";
  const stats = useQuery({ queryKey: ["stats"], queryFn: api.getStats, refetchInterval: 30000 });

  return (
    <div className="flex min-h-screen w-full bg-background">
      <DashboardSidebar />
      <div className="flex-1 ml-60 flex flex-col">
        <header className="sticky top-0 z-40 bg-card shadow-card px-8 py-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-foreground">{title}</h2>
          <p className="text-xs text-muted-foreground">
            Last updated: {stats.dataUpdatedAt ? new Date(stats.dataUpdatedAt).toLocaleTimeString() : "—"}
          </p>
        </header>
        <main className="flex-1 p-8">
          {children}
        </main>
      </div>
    </div>
  );
}
