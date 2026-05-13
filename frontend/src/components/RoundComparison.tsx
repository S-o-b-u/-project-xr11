import type { GenerateReportData } from "@/types/report";

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
    <div className={`${className}`.trim()}>
      <div className="flex items-center gap-3 mb-6">
        <span className="accent-dot" />
        <h2
          style={{ fontFamily: "var(--font-display)" }}
          className="text-xl md:text-2xl font-bold text-white uppercase tracking-wide"
        >
          Inference Delta
        </h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="card-dark p-6">
          <span className="accent-pill text-[8px] mb-4 inline-flex">Round 1 · Raw</span>
          <pre className="text-xs font-mono text-white/40 leading-relaxed whitespace-pre-wrap mt-2">
            {round1Raw || "—"}
          </pre>
        </div>
        <div className="card-dark p-6">
          <span className="accent-pill text-[8px] mb-4 inline-flex">Round 2 · Refined</span>
          <pre className="text-xs font-mono text-white/40 leading-relaxed whitespace-pre-wrap mt-2">
            {round2Raw || "—"}
          </pre>
        </div>
      </div>
    </div>
  );
}
