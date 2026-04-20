import { cn } from "@/lib/utils";

const severityStyles: Record<string, string> = {
  critical: "bg-[hsl(0_84%_60%/0.1)] text-severity-critical",
  high: "bg-[hsl(25_95%_53%/0.1)] text-severity-high",
  medium: "bg-[hsl(48_96%_53%/0.15)] text-[#a16207]",
  low: "bg-[hsl(142_71%_45%/0.1)] text-severity-low",
};

export function SeverityBadge({ severity }: { severity: string }) {
  const s = severity?.toLowerCase() || "low";
  return (
    <span className={cn("px-2.5 py-1 rounded-md text-xs font-semibold", severityStyles[s] || severityStyles.low)}>
      {severity}
    </span>
  );
}
