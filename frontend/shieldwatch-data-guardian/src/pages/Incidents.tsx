import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { SeverityBadge } from "@/components/SeverityBadge";
import { Skeleton } from "@/components/ui/skeleton";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";
import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";

const severityOptions = ["All", "Critical", "High", "Medium", "Low"];

function parsePiiTypes(pii_types: any): string[] {
  if (!pii_types) return [];
  if (typeof pii_types === "string") return pii_types.split(",").map((s) => s.trim()).filter(Boolean);
  if (Array.isArray(pii_types)) return pii_types;
  return [];
}

export default function Incidents() {
  const { data, isLoading, error } = useQuery({ queryKey: ["incidents"], queryFn: api.getIncidents });
  const [search, setSearch] = useState("");
  const [severityFilter, setSeverityFilter] = useState("All");
  const [sourceFilter, setSourceFilter] = useState("All");
  const [expandedRow, setExpandedRow] = useState<number | null>(null);

  if (error) toast.error("Failed to load incidents");

  const sourceTypes = ["All", ...new Set((data || []).map((d: any) => d.source_type).filter(Boolean))];

  const filtered = (data || []).filter((inc: any) => {
    if (severityFilter !== "All" && inc.severity?.toLowerCase() !== severityFilter.toLowerCase()) return false;
    if (sourceFilter !== "All" && inc.source_type !== sourceFilter) return false;
    if (search && !(inc.source_url || "").toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center gap-3">
        <Input placeholder="Search by URL..." value={search} onChange={(e) => setSearch(e.target.value)} className="max-w-xs bg-card shadow-card rounded-lg border-border" />
        <div className="flex gap-1 bg-card shadow-card rounded-lg p-1">
          {severityOptions.map((s) => (
            <button key={s} onClick={() => setSeverityFilter(s)} className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${severityFilter === s ? "bg-primary text-primary-foreground shadow-sm" : "text-muted-foreground hover:text-foreground"}`}>
              {s}
            </button>
          ))}
        </div>
        <select value={sourceFilter} onChange={(e) => setSourceFilter(e.target.value)} className="bg-card shadow-card border-0 rounded-lg px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-ring">
          {sourceTypes.map((s) => <option key={s as string} value={s as string}>{s as string}</option>)}
        </select>
      </div>

      <div className="bg-card rounded-xl shadow-card overflow-hidden">
        {isLoading ? (
          <div className="p-6 space-y-3">{[...Array(8)].map((_, i) => <Skeleton key={i} className="h-10 w-full" />)}</div>
        ) : filtered.length === 0 ? (
          <div className="p-12 text-center text-muted-foreground text-sm">No incidents found.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-muted-foreground text-xs uppercase tracking-wider">
                  <th className="p-1 w-8"></th>
                  <th className="text-left px-4 py-3 font-medium">#</th>
                  <th className="text-left px-4 py-3 font-medium">Source URL</th>
                  <th className="text-left px-4 py-3 font-medium">Type</th>
                  <th className="text-left px-4 py-3 font-medium">Severity</th>
                  <th className="text-left px-4 py-3 font-medium">Score</th>
                  <th className="text-left px-4 py-3 font-medium">PII Types</th>
                  <th className="text-left px-4 py-3 font-medium">Records</th>
                  <th className="text-left px-4 py-3 font-medium">Date</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((inc: any, i: number) => {
                  const piiTypes = parsePiiTypes(inc.pii_types);
                  return (
                    <>
                      <tr key={i} onClick={() => setExpandedRow(expandedRow === i ? null : i)} className={`border-t border-border cursor-pointer transition-colors hover:bg-row-hover ${i % 2 === 1 ? "bg-row-alt" : ""}`}>
                        <td className="pl-3">{expandedRow === i ? <ChevronDown className="h-3.5 w-3.5 text-muted-foreground" /> : <ChevronRight className="h-3.5 w-3.5 text-muted-foreground" />}</td>
                        <td className="px-4 py-3 text-muted-foreground text-xs">{i + 1}</td>
                        <td className="px-4 py-3 text-foreground max-w-[180px] truncate font-medium text-xs" title={inc.source_url}>{inc.source_url}</td>
                        <td className="px-4 py-3"><span className="bg-secondary px-2 py-0.5 rounded-md text-xs font-medium text-muted-foreground">{inc.source_type}</span></td>
                        <td className="px-4 py-3"><SeverityBadge severity={inc.severity} /></td>
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-2">
                            <div className="w-14 h-1.5 bg-secondary rounded-full overflow-hidden">
                              <div className="h-full bg-primary rounded-full transition-all" style={{ width: `${(inc.score / 10) * 100}%` }} />
                            </div>
                            <span className="text-xs font-mono text-muted-foreground">{inc.score}</span>
                          </div>
                        </td>
                        <td className="px-4 py-3">
                          <div className="flex flex-wrap gap-1">
                            {piiTypes.slice(0, 3).map((t: string) => (
                              <span key={t} className="bg-primary/10 text-primary px-1.5 py-0.5 rounded text-[10px] font-medium">{t}</span>
                            ))}
                            {piiTypes.length > 3 && <span className="text-[10px] text-muted-foreground">+{piiTypes.length - 3}</span>}
                          </div>
                        </td>
                        <td className="px-4 py-3 text-foreground text-xs">{inc.record_count ?? "—"}</td>
                        <td className="px-4 py-3 text-muted-foreground text-xs">{new Date(inc.created_at).toLocaleDateString()}</td>
                      </tr>
                      {expandedRow === i && (
                        <tr key={`exp-${i}`} className="bg-secondary/50">
                          <td colSpan={9} className="px-6 py-4">
                            <p className="text-sm text-foreground mb-1"><span className="font-medium">Full URL:</span> {inc.source_url}</p>
                            <p className="text-sm text-foreground"><span className="font-medium">All PII Types:</span> {piiTypes.join(", ") || "N/A"}</p>
                          </td>
                        </tr>
                      )}
                    </>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}