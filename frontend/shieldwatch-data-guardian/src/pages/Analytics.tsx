import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, AreaChart, Area, CartesianGrid } from "recharts";
import { useMemo } from "react";

const SEVERITY_COLORS: Record<string, string> = {
  critical: "#EF4444",
  high: "#F97316",
  medium: "#EAB308",
  low: "#22C55E",
};

const tooltipStyle = { background: "#fff", border: "1px solid #E2E8F0", borderRadius: 10, color: "#0F172A", boxShadow: "0 4px 12px rgba(0,0,0,0.08)" };

export default function Analytics() {
  const severity = useQuery({ queryKey: ["severity-breakdown"], queryFn: api.getSeverityBreakdown });
  const sources = useQuery({ queryKey: ["sources"], queryFn: api.getSources });
  const incidents = useQuery({ queryKey: ["incidents"], queryFn: api.getIncidents });

  if (severity.error) toast.error("Failed to load severity data");
  if (sources.error) toast.error("Failed to load source data");

const pieData = (Array.isArray(severity.data) ? severity.data : []).map((d: any) => ({ name: d.severity, value: d.count }));
const barData = (Array.isArray(sources.data) ? sources.data : []).map((d: any) => ({ name: d.source_type, value: d.count }));

  const timelineData = useMemo(() => {
    if (!incidents.data) return [];
    const grouped: Record<string, number> = {};
    incidents.data.forEach((inc: any) => {
      const day = new Date(inc.created_at).toLocaleDateString();
      grouped[day] = (grouped[day] || 0) + 1;
    });
    return Object.entries(grouped).map(([date, count]) => ({ date, count })).sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
  }, [incidents.data]);

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-card rounded-xl shadow-card p-6">
          <h3 className="text-sm font-semibold text-foreground mb-4">Severity Breakdown</h3>
          {severity.isLoading ? <Skeleton className="h-64" /> : pieData.length === 0 ? (
            <div className="h-64 flex items-center justify-center text-muted-foreground text-sm">No data</div>
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie data={pieData} cx="50%" cy="50%" innerRadius={65} outerRadius={105} paddingAngle={3} dataKey="value" strokeWidth={0} label={({ name, value }) => `${name}: ${value}`}>
                  {pieData.map((entry) => (
                    <Cell key={entry.name} fill={SEVERITY_COLORS[entry.name.toLowerCase()] || "#94A3B8"} />
                  ))}
                </Pie>
                <Tooltip contentStyle={tooltipStyle} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="bg-card rounded-xl shadow-card p-6">
          <h3 className="text-sm font-semibold text-foreground mb-4">Incidents by Source</h3>
          {sources.isLoading ? <Skeleton className="h-64" /> : barData.length === 0 ? (
            <div className="h-64 flex items-center justify-center text-muted-foreground text-sm">No data</div>
          ) : (
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={barData} layout="vertical" margin={{ left: 20 }}>
                <XAxis type="number" stroke="#94A3B8" fontSize={12} />
                <YAxis type="category" dataKey="name" stroke="#94A3B8" width={80} fontSize={12} />
                <Tooltip contentStyle={tooltipStyle} />
                <Bar dataKey="value" fill="#6366F1" radius={[0, 6, 6, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      <div className="bg-card rounded-xl shadow-card p-6">
        <h3 className="text-sm font-semibold text-foreground mb-4">Incidents Over Time</h3>
        {incidents.isLoading ? <Skeleton className="h-64" /> : timelineData.length === 0 ? (
          <div className="h-64 flex items-center justify-center text-muted-foreground text-sm">No data</div>
        ) : (
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={timelineData}>
              <defs>
                <linearGradient id="colorCount" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#6366F1" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#6366F1" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
              <XAxis dataKey="date" stroke="#94A3B8" fontSize={12} />
              <YAxis stroke="#94A3B8" fontSize={12} />
              <Tooltip contentStyle={tooltipStyle} />
              <Area type="monotone" dataKey="count" stroke="#6366F1" fill="url(#colorCount)" strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
