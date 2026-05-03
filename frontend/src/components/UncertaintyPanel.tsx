import type { UncertaintyData } from "@/types/report";

const panelSection =
  "rounded-lg border border-zinc-200 bg-white p-4 dark:border-zinc-800 dark:bg-zinc-950/40";

const labelClass =
  "mb-2 block text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400";

function confidenceToPercent(confidence: number): number {
  if (!Number.isFinite(confidence)) return 0;
  const scaled = confidence <= 1 ? confidence * 100 : confidence;
  return Math.min(100, Math.max(0, scaled));
}

function formatMetric(value: number): string {
  if (!Number.isFinite(value)) return "—";
  return Number.isInteger(value) ? String(value) : value.toFixed(4);
}

export interface UncertaintyPanelProps {
  uncertainty: UncertaintyData;
  className?: string;
}

export function UncertaintyPanel({
  uncertainty,
  className = "",
}: UncertaintyPanelProps) {
  const {
    confidence,
    entropy,
    semantic_variance,
    needs_human_review,
    severity_votes,
  } = uncertainty;

  const confidencePct = confidenceToPercent(confidence);
  const voteEntries = Object.entries(severity_votes).sort(
    (a, b) => b[1] - a[1]
  );
  const maxVotes = Math.max(
    ...voteEntries.map(([, count]) => count),
    1
  );

  return (
    <div className={`flex flex-col gap-4 ${className}`.trim()}>
      {needs_human_review ? (
        <div
          role="status"
          className="flex gap-3 rounded-lg border border-amber-300 bg-amber-50 p-4 dark:border-amber-600/50 dark:bg-amber-950/40"
        >
          <span
            className="mt-0.5 inline-flex size-8 shrink-0 items-center justify-center rounded-full bg-amber-500 text-sm font-bold text-white dark:bg-amber-600"
            aria-hidden
          >
            !
          </span>
          <div>
            <p className="text-sm font-semibold text-amber-950 dark:text-amber-100">
              Human review recommended
            </p>
            <p className="mt-1 text-sm leading-snug text-amber-900/90 dark:text-amber-200/90">
              Model uncertainty indicates this case should be verified by a
              clinician before clinical use.
            </p>
          </div>
        </div>
      ) : null}

      <section className={panelSection}>
        <h3 className={labelClass}>Confidence</h3>
        <div className="flex items-center gap-3">
          <div className="h-3 min-w-0 flex-1 overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-800">
            <div
              className="h-full rounded-full bg-emerald-500 transition-[width] duration-300 dark:bg-emerald-600"
              style={{ width: `${confidencePct}%` }}
            />
          </div>
          <span className="shrink-0 tabular-nums text-sm font-medium text-zinc-900 dark:text-zinc-100">
            {confidencePct.toFixed(1)}%
          </span>
        </div>
      </section>

      <section className={panelSection}>
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <h3 className={labelClass}>Entropy</h3>
            <p className="font-mono text-lg tabular-nums text-zinc-900 dark:text-zinc-100">
              {formatMetric(entropy)}
            </p>
          </div>
          <div>
            <h3 className={labelClass}>Semantic variance</h3>
            <p className="font-mono text-lg tabular-nums text-zinc-900 dark:text-zinc-100">
              {formatMetric(semantic_variance)}
            </p>
          </div>
        </div>
      </section>

      <section className={panelSection}>
        <h3 className={labelClass}>Severity votes</h3>
        {voteEntries.length === 0 ? (
          <p className="text-sm text-zinc-500 dark:text-zinc-400">
            No vote data returned.
          </p>
        ) : (
          <ul className="flex flex-col gap-3">
            {voteEntries.map(([label, count]) => {
              const pct = (count / maxVotes) * 100;
              return (
                <li key={label}>
                  <div className="mb-1 flex items-baseline justify-between gap-2 text-xs">
                    <span className="font-medium uppercase tracking-wide text-zinc-700 dark:text-zinc-300">
                      {label}
                    </span>
                    <span className="tabular-nums text-zinc-500 dark:text-zinc-400">
                      {count}
                    </span>
                  </div>
                  <div className="h-2 w-full overflow-hidden rounded-full bg-zinc-200 dark:bg-zinc-800">
                    <div
                      className="h-full rounded-full bg-indigo-500 dark:bg-indigo-500"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </section>
    </div>
  );
}
