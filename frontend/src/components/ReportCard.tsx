import { SeverityBadge } from "@/components/SeverityBadge";
import type { FinalReport } from "@/types/report";

const sectionClass =
  "rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-950/40";

const labelClass =
  "mb-2 block text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400";

const bodyClass =
  "whitespace-pre-wrap text-sm leading-relaxed text-zinc-900 dark:text-zinc-100";

export interface ReportCardProps {
  finalReport: FinalReport;
  className?: string;
}

export function ReportCard({ finalReport, className = "" }: ReportCardProps) {
  const { findings, impression, severity, follow_up, deviations } =
    finalReport;

  return (
    <div className={`flex flex-col gap-4 ${className}`.trim()}>
      <section className={sectionClass}>
        <h3 className={labelClass}>Findings</h3>
        <p className={bodyClass}>{findings}</p>
      </section>

      <section className={sectionClass}>
        <h3 className={labelClass}>Impression</h3>
        <p className={bodyClass}>{impression}</p>
      </section>

      <section className={sectionClass}>
        <h3 className={labelClass}>Severity</h3>
        <SeverityBadge severity={severity} />
      </section>

      <section className={sectionClass}>
        <h3 className={labelClass}>Follow-up</h3>
        <p className={bodyClass}>{follow_up}</p>
      </section>

      <section className={sectionClass}>
        <h3 className={labelClass}>Deviations</h3>
        <p className={bodyClass}>{deviations}</p>
      </section>
    </div>
  );
}
