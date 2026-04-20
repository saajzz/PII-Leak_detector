import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Shield, AlertOctagon, AlertTriangle, FileSearch, Play, Loader2 } from "lucide-react";
import { SeverityBadge } from "@/components/SeverityBadge";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { useState } from "react";

const kpis = [
  { label: "Total Incidents", key: "total_incidents", icon: Shield, iconBg: "bg-primary/10", iconColor: "text-primary" },
  { label: "Critical", key: "critical_incidents", icon: AlertOctagon, iconBg: "bg-severity-critical/10", iconColor: "text-severity-critical" },
  { label: "High", key: "high_incidents", icon: AlertTriangle, iconBg: "bg-severity-high/10", iconColor: "text-severity-high" },
  { label: "Total Findings", key: "total_findings", icon: FileSearch, iconBg: "bg-severity-low/10", iconColor: "text-severity-low" },
];

export default function Overview() {
  const queryClient = useQueryClient();
  const [running, setRunning] = useState(false);

  const stats = useQuery({ queryKey: ["stats"], queryFn: api.getStats, refetchInterval: 30000 });
  const incidents = useQuery({ queryKey: ["incidents"], queryFn: api.getIncidents, refetchInterval: 30000 });

  const handleRunPipeline = async () => {
    setRunning(true);
    try {
      await api.runPipeline();
      toast.success("Pipeline completed successfully");
      queryClient.invalidateQueries();
    } catch (e: any) {
      toast.error(e.message || "Pipeline failed");
    } finally {
      setRunning(false);
    }
  };

  if (stats.error) toast.error("Failed to load stats");
  if (incidents.error) toast.error("Failed to load incidents");

  const recentIncidents = (incidents.data || []).slice(0, 5);

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-end">
        <Button onClick={handleRunPipeline} disabled={running} className="gap-2 rounded-lg shadow-card">
          {running ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
          Run Pipeline
        </Button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        {kpis.map((kpi) => (
          <div key={kpi.key} className="bg-card rounded-xl shadow-card p-5 flex items-center gap-4 transition-shadow hover:shadow-card-hover">
            {stats.isLoading ? (
              <Skeleton className="h-16 w-full" />
            ) : (
              <>
                <div className={`h-11 w-11 rounded-xl ${kpi.iconBg} flex items-center justify-center shrink-0`}>
                  <kpi.icon className={`h-5 w-5 ${kpi.iconColor}`} />
                </div>
                <div>
                  <p className="text-2xl font-bold text-foreground">{stats.data?.[kpi.key] ?? 0}</p>
                  <p className="text-xs text-muted-foreground mt-0.5">{kpi.label}</p>
                </div>
              </>
            )}
          </div>
        ))}
      </div>

      <div className="bg-card rounded-xl shadow-card">
        <div className="px-6 py-4 border-b border-border">
          <h3 className="text-sm font-semibold text-foreground">Recent Incidents</h3>
        </div>
        {incidents.isLoading ? (
          <div className="p-6 space-y-3">
            {[...Array(5)].map((_, i) => <Skeleton key={i} className="h-10 w-full" />)}
          </div>
        ) : recentIncidents.length === 0 ? (
          <div className="p-12 text-center text-muted-foreground text-sm">No incidents detected yet.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-muted-foreground text-xs uppercase tracking-wider">
                  <th className="text-left px-6 py-3 font-medium">Source</th>
                  <th className="text-left px-6 py-3 font-medium">Type</th>
                  <th className="text-left px-6 py-3 font-medium">Severity</th>
                  <th className="text-left px-6 py-3 font-medium">Score</th>
                  <th className="text-left px-6 py-3 font-medium">Date</th>
                </tr>
              </thead>
              <tbody>
                {recentIncidents.map((inc: any, i: number) => (
                  <tr key={i} className={`border-t border-border transition-colors hover:bg-row-hover ${i % 2 === 1 ? "bg-row-alt" : ""}`}>
                    <td className="px-6 py-3 text-foreground max-w-[220px] truncate font-medium">{inc.source_url || inc.source}</td>
                    <td className="px-6 py-3"><span className="bg-secondary px-2.5 py-1 rounded-md text-xs font-medium text-muted-foreground">{inc.source_type}</span></td>
                    <td className="px-6 py-3"><SeverityBadge severity={inc.severity} /></td>
                    <td className="px-6 py-3 font-mono text-foreground text-xs">{inc.score}/10</td>
                    <td className="px-6 py-3 text-muted-foreground text-xs">{new Date(inc.created_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
