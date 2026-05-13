import { SeverityBadge } from "@/components/SeverityBadge";
import type { FinalReport, GenerateReportData } from "@/types/report";

export interface ReportCardProps {
  finalReport: FinalReport;
  metadata?: GenerateReportData["metadata"];
  className?: string;
}

export function ReportCard({ finalReport, metadata, className = "" }: ReportCardProps) {
  const { findings, impression, severity, follow_up, deviations } = finalReport;

  const sections = [
    { label: "Findings", content: findings },
    { label: "Impression", content: impression },
    { label: "Follow-up", content: follow_up },
    { label: "Deviations", content: deviations },
  ];

  return (
    <div className={`card-dark p-8 md:p-10 ${className}`.trim()}>
      {/* Header */}
      <div className="flex items-center justify-between mb-10 pb-5 border-b border-white/[0.06]">
        <div className="flex items-center gap-3">
          <span className="accent-dot" />
          <h2
            style={{ fontFamily: "var(--font-display)" }}
            className="text-xl md:text-2xl font-bold text-white uppercase tracking-wide"
          >
            Clinical Evaluation
          </h2>
        </div>
        <div className="flex items-center gap-4">
          {metadata?.generation_method && (
            <span className="accent-pill text-[9px]">
              {metadata.generation_method.includes("template") || metadata.generation_method.includes("fallback") ? "Template" : "Groq LLM"}
            </span>
          )}
          <SeverityBadge severity={severity} />
        </div>
      </div>

      {/* Sections */}
      <div className="space-y-10">
        {sections.map((s) => (
          <section key={s.label}>
            <div className="flex items-center gap-2 mb-3">
              <div className="w-1 h-1 rounded-full bg-[#FF3D00]" />
              <h3 className="section-label">{s.label}</h3>
            </div>
            <p className="whitespace-pre-wrap text-sm leading-[1.8] text-white/75 font-light tracking-wide pl-3 border-l border-white/[0.04]">
              {s.content || "—"}
            </p>
          </section>
        ))}
      </div>
    </div>
  );
}
