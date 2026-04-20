import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Skeleton } from "@/components/ui/skeleton";
import { Bug, ShieldCheck, ShieldAlert } from "lucide-react";
import { toast } from "sonner";

export default function Canaries() {
  const { data, isLoading, error } = useQuery({ queryKey: ["canaries"], queryFn: api.getCanaries });

  if (error) toast.error("Failed to load canaries");

  const canaries = data || [];
  const planted = canaries.length;
  const triggered = canaries.filter((c: any) => c.status === "triggered").length;

  return (
    <div className="space-y-6">
      <p className="text-sm text-muted-foreground max-w-2xl">
        Canary records are fake PII values planted in monitored sources — if they appear in a leak, the source is compromised.
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
        <div className="bg-card rounded-xl shadow-card p-5 flex items-center gap-4 transition-shadow hover:shadow-card-hover">
          <div className="h-11 w-11 rounded-xl bg-primary/10 flex items-center justify-center">
            <ShieldCheck className="h-5 w-5 text-primary" />
          </div>
          <div>
            <p className="text-2xl font-bold text-foreground">{planted}</p>
            <p className="text-xs text-muted-foreground">Canaries Planted</p>
          </div>
        </div>
        <div className="bg-card rounded-xl shadow-card p-5 flex items-center gap-4 transition-shadow hover:shadow-card-hover">
          <div className="h-11 w-11 rounded-xl bg-severity-critical/10 flex items-center justify-center">
            <ShieldAlert className="h-5 w-5 text-severity-critical" />
          </div>
          <div>
            <p className="text-2xl font-bold text-foreground">{triggered}</p>
            <p className="text-xs text-muted-foreground">Triggered</p>
          </div>
        </div>
      </div>

      <div className="bg-card rounded-xl shadow-card overflow-hidden">
        {isLoading ? (
          <div className="p-6 space-y-3">{[...Array(5)].map((_, i) => <Skeleton key={i} className="h-10 w-full" />)}</div>
        ) : canaries.length === 0 ? (
          <div className="p-12 text-center text-muted-foreground text-sm">No canary records planted yet.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-muted-foreground text-xs uppercase tracking-wider">
                  <th className="text-left px-6 py-3 font-medium">Label</th>
                  <th className="text-left px-6 py-3 font-medium">Fake Aadhaar</th>
                  <th className="text-left px-6 py-3 font-medium">Fake PAN</th>
                  <th className="text-left px-6 py-3 font-medium">Fake Phone</th>
                  <th className="text-left px-6 py-3 font-medium">Planted At</th>
                  <th className="text-left px-6 py-3 font-medium">Status</th>
                </tr>
              </thead>
              <tbody>
                {canaries.map((c: any, i: number) => (
                  <tr key={i} className={`border-t border-border transition-colors hover:bg-row-hover ${i % 2 === 1 ? "bg-row-alt" : ""} ${c.status === "triggered" ? "border-l-4 border-l-severity-critical" : ""}`}>
                    <td className="px-6 py-3 text-foreground font-medium text-xs">{c.label}</td>
                    <td className="px-6 py-3 font-mono text-foreground text-xs">{c.fake_aadhaar ? `XXXX-XXXX-${c.fake_aadhaar.slice(-4)}` : "—"}</td>
                    <td className="px-6 py-3 font-mono text-foreground text-xs">{c.fake_pan || "—"}</td>
                    <td className="px-6 py-3 font-mono text-foreground text-xs">{c.fake_phone ? `XXXXX-${c.fake_phone.slice(-5)}` : "—"}</td>
                    <td className="px-6 py-3 text-muted-foreground text-xs">{c.planted_at ? new Date(c.planted_at).toLocaleString() : "—"}</td>
                    <td className="px-6 py-3">
                      {c.status === "triggered" ? (
                        <span className="inline-flex items-center gap-1 bg-[hsl(0_84%_60%/0.1)] text-severity-critical px-2.5 py-1 rounded-md text-xs font-semibold">🔴 Triggered</span>
                      ) : (
                        <span className="inline-flex items-center gap-1 bg-[hsl(142_71%_45%/0.1)] text-severity-low px-2.5 py-1 rounded-md text-xs font-semibold">🟢 Safe</span>
                      )}
                    </td>
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
