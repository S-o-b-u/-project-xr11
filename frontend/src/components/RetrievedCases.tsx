import type { RetrievedCase } from "@/types/report";

const cardClass =
  "rounded-lg border border-zinc-200 bg-white p-3 dark:border-zinc-800 dark:bg-zinc-950/40";

const labelClass =
  "text-[10px] font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400";

export interface RetrievedCasesProps {
  /** RAG neighbors from the API; only the first three are shown. */
  retrievedCases: RetrievedCase[];
  className?: string;
}

export function RetrievedCases({
  retrievedCases,
  className = "",
}: RetrievedCasesProps) {
  const topThree = retrievedCases.slice(0, 3);

  return (
    <div className={`flex flex-col gap-3 ${className}`.trim()}>
      <h3 className={labelClass}>Top RAG cases (similarity)</h3>
      {topThree.length === 0 ? (
        <p className="text-sm text-zinc-500 dark:text-zinc-400">
          No similar cases returned.
        </p>
      ) : (
        <ol className="flex flex-col gap-3">
          {topThree.map((item, index) => (
            <li key={item.id || `case-${index}`} className={cardClass}>
              <div className="mb-2 flex flex-wrap items-baseline justify-between gap-2">
                <span className="text-xs font-medium text-zinc-700 dark:text-zinc-200">
                  Case {index + 1}
                  {item.id ? (
                    <span className="ml-1 font-mono text-[10px] text-zinc-400">
                      {item.id}
                    </span>
                  ) : null}
                </span>
                <span className="shrink-0 font-mono text-xs tabular-nums text-zinc-600 dark:text-zinc-300">
                  {(item.similarity_score * 100).toFixed(1)}% similar
                </span>
              </div>
              <p className={labelClass}>Findings (snippet)</p>
              <p className="mt-1 max-h-28 overflow-y-auto text-sm leading-snug text-zinc-900 dark:text-zinc-100">
                {item.gold_findings || "—"}
              </p>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}
