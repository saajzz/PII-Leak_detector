import { Shield, AlertTriangle, Search, BarChart3, Bug } from "lucide-react";
import { NavLink } from "react-router-dom";
import { cn } from "@/lib/utils";

const navItems = [
  { label: "Overview", icon: Shield, path: "/" },
  { label: "Incidents", icon: AlertTriangle, path: "/incidents" },
  { label: "Findings", icon: Search, path: "/findings" },
  { label: "Analytics", icon: BarChart3, path: "/analytics" },
  { label: "Canaries", icon: Bug, path: "/canaries" },
];

export function DashboardSidebar() {
  return (
    <aside className="fixed left-0 top-0 h-screen w-60 bg-sidebar flex flex-col z-50">
      <div className="px-5 py-6">
        <div className="flex items-center gap-2.5">
          <div className="h-8 w-8 rounded-lg bg-sidebar-primary flex items-center justify-center">
            <Shield className="h-4 w-4 text-sidebar-primary-foreground" />
          </div>
          <div>
            <h1 className="text-sm font-semibold text-sidebar-foreground tracking-tight">ShieldWatch</h1>
            <p className="text-[11px] text-sidebar-muted">PII Leak Detection</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 px-3 space-y-0.5">
        <p className="text-[11px] font-medium text-sidebar-muted uppercase tracking-wider px-3 mb-2">Menu</p>
        {navItems.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === "/"}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-2.5 px-3 py-2 rounded-lg text-[13px] font-medium transition-all duration-150",
                isActive
                  ? "bg-sidebar-primary text-sidebar-primary-foreground shadow-sm"
                  : "text-sidebar-muted hover:text-sidebar-foreground hover:bg-sidebar-accent"
              )
            }
          >
            <item.icon className="h-4 w-4" />
            {item.label}
          </NavLink>
        ))}
      </nav>

      <div className="px-5 py-4 border-t border-sidebar-border">
        <p className="text-[11px] text-sidebar-muted">ShieldWatch v1.0</p>
        <p className="text-[11px] text-sidebar-muted">SRM Valliammai</p>
      </div>
    </aside>
  );
}
