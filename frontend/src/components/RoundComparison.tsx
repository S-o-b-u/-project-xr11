import type { GenerateReportData } from "@/types/report";

const panelClass =
  "flex min-h-0 flex-1 flex-col rounded-lg border border-zinc-200 bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-950/50";

const headerClass =
  "shrink-0 border-b border-zinc-200 px-3 py-2 text-xs font-semibold uppercase tracking-wide text-zinc-600 dark:border-zinc-700 dark:text-zinc-300";

const preClass =
  "min-h-0 flex-1 overflow-auto whitespace-pre-wrap p-3 font-mono text-xs leading-relaxed text-zinc-800 dark:text-zinc-200";

export interface RoundComparisonProps {
  round1Raw: GenerateReportData["round1_raw"];
  round2Raw: GenerateReportData["round2_raw"];
  className?: string;
}

export function RoundComparison({
  round1Raw,
  round2Raw,
  className = "",
}: RoundComparisonProps) {
  return (
    <div className={className}>
      <p className="mb-2 text-[10px] font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
        Round 1 vs round 2 (raw)
      </p>
      <div className="flex min-h-48 max-h-128 flex-col gap-3 md:max-h-160 md:flex-row">
        <div className={panelClass}>
          <div className={headerClass}>Round 1</div>
          <pre className={preClass}>{round1Raw || "—"}</pre>
        </div>
        <div className={panelClass}>
          <div className={headerClass}>Round 2</div>
          <pre className={preClass}>{round2Raw || "—"}</pre>
        </div>
      </div>
    </div>
  );
}
