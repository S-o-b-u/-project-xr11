import type { ReportSeverity } from "@/types/report";

const severityStyles: Record<
  ReportSeverity,
  string
> = {
  NORMAL:
    "bg-emerald-100 text-emerald-900 ring-1 ring-inset ring-emerald-600/20 dark:bg-emerald-950/50 dark:text-emerald-200 dark:ring-emerald-500/30",
  MILD:
    "bg-amber-100 text-amber-950 ring-1 ring-inset ring-amber-500/25 dark:bg-amber-950/40 dark:text-amber-200 dark:ring-amber-400/30",
  MODERATE:
    "bg-orange-100 text-orange-950 ring-1 ring-inset ring-orange-500/25 dark:bg-orange-950/45 dark:text-orange-200 dark:ring-orange-400/30",
  CRITICAL:
    "bg-red-100 text-red-950 ring-1 ring-inset ring-red-600/30 dark:bg-red-950/50 dark:text-red-200 dark:ring-red-500/35",
};

export interface SeverityBadgeProps {
  severity: ReportSeverity;
  className?: string;
}

export function SeverityBadge({ severity, className = "" }: SeverityBadgeProps) {
  const styles = severityStyles[severity];

  return (
    <span
      className={`inline-flex max-w-full items-center rounded-full px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wide ${styles} ${className}`.trim()}
    >
      {severity}
    </span>
  );
}
