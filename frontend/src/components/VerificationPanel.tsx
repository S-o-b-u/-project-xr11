import type {
  HallucinationResult,
  KnowledgeGraphResult,
  NliCheckResult,
} from "@/types/report";

const sectionTitle =
  "border-b border-zinc-200 pb-1 text-[11px] font-semibold uppercase tracking-wide text-zinc-500 dark:border-zinc-700 dark:text-zinc-400";

const rowLabel = "text-zinc-500 dark:text-zinc-400";
const rowValue = "font-mono text-xs text-zinc-900 dark:text-zinc-100";

export interface VerificationPanelProps {
  nli_check: NliCheckResult;
  knowledge_graph: KnowledgeGraphResult;
  hallucination: HallucinationResult;
  className?: string;
}

export function VerificationPanel({
  nli_check,
  knowledge_graph,
  hallucination,
  className = "",
}: VerificationPanelProps) {
  const icd10Codes = knowledge_graph.icd10_codes ?? [];
  const icd10Preview = icd10Codes.slice(0, 8);

  return (
    <div
      className={`rounded-lg border border-zinc-300 bg-zinc-50 p-3 text-xs dark:border-zinc-700 dark:bg-zinc-950 ${className}`.trim()}
    >
      <p className="mb-3 font-mono text-[10px] uppercase tracking-wider text-zinc-400">
        Verification (debug)
      </p>
      <div className="grid gap-4 md:grid-cols-3">
        <section>
          <h3 className={sectionTitle}>NLI consistency</h3>
          <dl className="mt-2 space-y-1.5">
            <div className="flex justify-between gap-2">
              <dt className={rowLabel}>nli_result</dt>
              <dd className={rowValue}>{String(nli_check.nli_result ?? "—")}</dd>
            </div>
            <div className="flex justify-between gap-2">
              <dt className={rowLabel}>severity_check</dt>
              <dd className={rowValue}>
                {String(nli_check.severity_check ?? "—")}
              </dd>
            </div>
            <div className="flex justify-between gap-2">
              <dt className={rowLabel}>consistency_score</dt>
              <dd className={rowValue}>
                {nli_check.consistency_score != null
                  ? nli_check.consistency_score.toFixed(3)
                  : "—"}
              </dd>
            </div>
          </dl>
          <p className={`mt-2 ${rowLabel}`}>contradictions</p>
          <pre className="mt-1 max-h-24 overflow-auto whitespace-pre-wrap wrap-break-word rounded bg-white/80 p-2 font-mono text-[11px] leading-snug text-zinc-800 dark:bg-zinc-900 dark:text-zinc-200">
            {nli_check.contradictions ?? "—"}
          </pre>
        </section>

        <section>
          <h3 className={sectionTitle}>RadLex + ICD-10</h3>
          <dl className="mt-2 space-y-1.5">
            <div className="flex justify-between gap-2">
              <dt className={rowLabel}>standardization_rate</dt>
              <dd className={rowValue}>
                {knowledge_graph.standardization_rate != null
                  ? knowledge_graph.standardization_rate.toFixed(3)
                  : "—"}
              </dd>
            </div>
            <div className="flex justify-between gap-2">
              <dt className={rowLabel}>terms_found</dt>
              <dd className={rowValue}>
                {(knowledge_graph.terms_found?.length ?? 0)} terms
              </dd>
            </div>
            <div className="flex justify-between gap-2">
              <dt className={rowLabel}>unmatched</dt>
              <dd className={rowValue}>
                {(knowledge_graph.unmatched_terms?.length ?? 0)}
              </dd>
            </div>
          </dl>
          <p className={`mt-2 ${rowLabel}`}>icd10_codes</p>
          <ul className="mt-1 max-h-28 space-y-1 overflow-auto font-mono text-[11px] text-zinc-800 dark:text-zinc-200">
            {icd10Preview.map((row) => (
              <li key={`${row.icd10_code}-${row.finding}`}>
                <span className="text-zinc-500">{row.icd10_code}</span>{" "}
                {row.finding}
              </li>
            ))}
            {icd10Codes.length > 8 ? (
              <li className="text-zinc-400">
                +{icd10Codes.length - 8} more
              </li>
            ) : null}
          </ul>
        </section>

        <section>
          <h3 className={sectionTitle}>Hallucination</h3>
          <dl className="mt-2 space-y-1.5">
            <div className="flex justify-between gap-2">
              <dt className={rowLabel}>hallucination_score</dt>
              <dd className={rowValue}>
                {hallucination.hallucination_score != null
                  ? hallucination.hallucination_score.toFixed(3)
                  : "—"}
              </dd>
            </div>
            <div className="flex justify-between gap-2">
              <dt className={rowLabel}>uncertainty_score</dt>
              <dd className={rowValue}>
                {hallucination.uncertainty_score != null
                  ? hallucination.uncertainty_score.toFixed(3)
                  : "—"}
              </dd>
            </div>
            <div className="flex justify-between gap-2">
              <dt className={rowLabel}>overall_risk</dt>
              <dd className={rowValue}>
                {String(hallucination.overall_risk ?? "—")}
              </dd>
            </div>
            <div className="flex justify-between gap-2">
              <dt className={rowLabel}>safe_to_use</dt>
              <dd className={rowValue}>
                {hallucination.safe_to_use === true
                  ? "true"
                  : hallucination.safe_to_use === false
                    ? "false"
                    : "—"}
              </dd>
            </div>
            <div className="flex justify-between gap-2">
              <dt className={rowLabel}>claims</dt>
              <dd className={rowValue}>
                {hallucination.claim_verifications?.length ?? 0}
              </dd>
            </div>
          </dl>
        </section>
      </div>
    </div>
  );
}
