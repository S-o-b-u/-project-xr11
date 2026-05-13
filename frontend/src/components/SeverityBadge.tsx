import type { ReportSeverity } from "@/types/report";

const severityStyles: Record<ReportSeverity, { text: string; bg: string; border: string; dot: string }> = {
  NORMAL:   { text: "text-emerald-400", bg: "bg-emerald-400/8",  border: "border-emerald-400/20", dot: "bg-emerald-400" },
  MILD:     { text: "text-amber-400",   bg: "bg-amber-400/8",    border: "border-amber-400/20",   dot: "bg-amber-400" },
  MODERATE: { text: "text-orange-500",  bg: "bg-orange-500/8",   border: "border-orange-500/20",  dot: "bg-gradient-to-r from-[#FF3D00] to-[#FF6D00]" },
  CRITICAL: { text: "text-red-500",     bg: "bg-red-500/8",      border: "border-red-500/20",     dot: "bg-gradient-to-r from-[#FF3D00] to-[#EF4444]" },
};

export interface SeverityBadgeProps {
  severity: ReportSeverity;
  className?: string;
}

export function SeverityBadge({ severity, className = "" }: SeverityBadgeProps) {
  const s = severityStyles[severity] ?? severityStyles.NORMAL;

  return (
    <span
      className={`inline-flex items-center gap-2.5 px-4 py-1.5 rounded-full border text-[10px] font-mono tracking-widest uppercase ${s.text} ${s.border} ${s.bg} ${className}`.trim()}
    >
      <span className={`w-2 h-2 rounded-full ${s.dot}`} style={{ boxShadow: severity === "CRITICAL" || severity === "MODERATE" ? "0 0 8px rgba(255,61,0,0.4)" : "none" }} />
      {severity}
    </span>
  );
}
