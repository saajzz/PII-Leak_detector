import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import { useState } from "react";

const matchTypes = ["All", "Aadhaar", "PAN", "Mobile", "UPI", "IFSC", "Email"];

const typeColors: Record<string, string> = {
  aadhaar: "bg-[hsl(0_84%_60%/0.1)] text-severity-critical",
  pan: "bg-[hsl(25_95%_53%/0.1)] text-severity-high",
  mobile: "bg-[hsl(48_96%_53%/0.15)] text-[#a16207]",
  upi: "bg-primary/10 text-primary",
  ifsc: "bg-[hsl(142_71%_45%/0.1)] text-severity-low",
  email: "bg-secondary text-muted-foreground",
};

export default function Findings() {
  const { data, isLoading, error } = useQuery({ queryKey: ["findings"], queryFn: api.getFindings });
  const [filter, setFilter] = useState("All");

  if (error) toast.error("Failed to load findings");

  const filtered = (data || []).filter((f: any) => filter === "All" || f.match_type?.toLowerCase() === filter.toLowerCase());

  return (
    <div className="space-y-5">
      <div className="flex gap-1 bg-card shadow-card rounded-lg p-1 w-fit">
        {matchTypes.map((t) => (
          <button key={t} onClick={() => setFilter(t)} className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${filter === t ? "bg-primary text-primary-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"}`}>
            {t}
          </button>
        ))}
      </div>

      <div className="bg-card rounded-xl shadow-card overflow-hidden">
        {isLoading ? (
          <div className="p-6 space-y-3">{[...Array(8)].map((_, i) => <Skeleton key={i} className="h-10 w-full" />)}</div>
        ) : filtered.length === 0 ? (
          <div className="p-12 text-center text-muted-foreground text-sm">No findings found.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-muted-foreground text-xs uppercase tracking-wider">
                  <th className="text-left px-6 py-3 font-medium">Match Type</th>
                  <th className="text-left px-6 py-3 font-medium">Masked Value</th>
                  <th className="text-left px-6 py-3 font-medium">Source Type</th>
                  <th className="text-left px-6 py-3 font-medium">Context</th>
                  <th className="text-left px-6 py-3 font-medium">Detected At</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((f: any, i: number) => (
                  <tr key={i} className={`border-t border-border transition-colors hover:bg-row-hover ${i % 2 === 1 ? "bg-row-alt" : ""}`}>
                    <td className="px-6 py-3">
                      <span className={`px-2.5 py-1 rounded-md text-xs font-semibold ${typeColors[f.match_type?.toLowerCase()] || "bg-secondary text-muted-foreground"}`}>
                        {f.match_type}
                      </span>
                    </td>
                    <td className="px-6 py-3 font-mono text-foreground text-xs">{f.masked_value || f.value}</td>
                    <td className="px-6 py-3 text-foreground text-xs">{f.source_type}</td>
                    <td className="px-6 py-3 text-muted-foreground max-w-[250px] truncate text-xs" title={f.context}>{f.context || "—"}</td>
                    <td className="px-6 py-3 text-muted-foreground text-xs">{f.detected_at ? new Date(f.detected_at).toLocaleString() : "—"}</td>
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
