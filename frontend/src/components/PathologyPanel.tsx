import { motion } from "framer-motion";
import type { GenerateReportData } from "@/types/report";

export interface PathologyPanelProps {
  pathology: NonNullable<GenerateReportData["pathology"]>;
  concepts?: GenerateReportData["concepts"];
}

export default function PathologyPanel({ pathology, concepts = [] }: PathologyPanelProps) {
  const positiveFindings = pathology.positive_findings || [];
  const allFindings = Object.entries(pathology.findings || {});

  return (
    <div className="card-dark p-8 md:p-10">
      {/* Header */}
      <div className="flex items-center justify-between mb-8 pb-5 border-b border-white/[0.06]">
        <div className="flex items-center gap-3">
          <span className="accent-dot" />
          <h2
            style={{ fontFamily: "var(--font-display)" }}
            className="text-xl md:text-2xl font-bold text-white uppercase tracking-wide"
          >
            Pathology Detection
          </h2>
        </div>

        <div className="flex items-center gap-5">
          <div className="flex flex-col items-end gap-1.5">
            <span className="text-[10px] font-mono text-white/40 uppercase tracking-widest">
              Abnormality
            </span>
            <div className="w-28 h-2 bg-white/[0.04] rounded-full overflow-hidden">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${Math.min(100, Math.max(0, pathology.overall_abnormality_score * 100))}%` }}
                transition={{ duration: 1.2, delay: 0.3, ease: [0.16, 1, 0.3, 1] }}
                className="h-full rounded-full accent-bar"
              />
            </div>
          </div>
          <span className="accent-pill text-[9px]">TorchXRV</span>
        </div>
      </div>

      {/* Positive findings — large feature cards */}
      {positiveFindings.length > 0 && (
        <div className="mb-8">
          <h3 className="section-label mb-4 flex items-center gap-2">
            <div className="w-1 h-1 rounded-full bg-[#FF3D00]" />
            Confirmed Findings
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {positiveFindings.map((findingKey, idx) => {
              const findingData = pathology.findings[findingKey];
              if (!findingData) return null;
              const conf = findingData.confidence;
              const relatedConcept = concepts?.find(c =>
                c.raw_label.toLowerCase() === findingKey.toLowerCase() ||
                c.clinical_term.toLowerCase() === findingKey.toLowerCase()
              );

              return (
                <motion.div
                  key={findingKey}
                  initial={{ opacity: 0, y: 15 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.5, delay: idx * 0.1 }}
                  className="relative p-5 rounded-xl bg-white/[0.02] border border-white/[0.06] hover:border-[#FF3D00]/20 transition-all duration-300 group"
                >
                  {/* Top row */}
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <span className="text-base font-semibold text-white tracking-wide">{findingKey.replace(/_/g, " ")}</span>
                      {relatedConcept?.clinical_term && (
                        <span className="block text-xs text-white/40 mt-0.5 capitalize">{relatedConcept.clinical_term}</span>
                      )}
                    </div>
                    {relatedConcept?.icd10_hint && (
                      <span className="text-[10px] font-mono text-[#FF6D00]/70 bg-[#FF3D00]/[0.06] px-2 py-0.5 rounded-md">
                        {relatedConcept.icd10_hint}
                      </span>
                    )}
                  </div>

                  {/* Confidence bar */}
                  <div className="mt-4">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-[9px] uppercase tracking-widest text-white/30">Confidence</span>
                      <span className="text-xs font-mono text-white/70">{(conf * 100).toFixed(1)}%</span>
                    </div>
                    <div className="w-full h-1.5 bg-white/[0.04] rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        whileInView={{ width: `${conf * 100}%` }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.8, delay: 0.2 + idx * 0.1 }}
                        className="h-full rounded-full accent-bar"
                      />
                    </div>
                  </div>

                  {/* Severity chip */}
                  {relatedConcept?.severity && (
                    <div className="mt-3">
                      <span className="text-[9px] uppercase tracking-widest text-white/30 px-2 py-0.5 rounded-md bg-white/[0.03] border border-white/[0.04]">
                        {relatedConcept.severity}
                      </span>
                    </div>
                  )}
                </motion.div>
              );
            })}
          </div>
        </div>
      )}

      {/* All findings grid — small status list */}
      <div>
        <h3 className="section-label mb-4 flex items-center gap-2">
          <div className="w-1 h-1 rounded-full bg-white/20" />
          All Pathology Scores
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-x-6 gap-y-3">
          {allFindings.map(([name, data]) => (
            <div key={name} className="flex items-center justify-between py-1.5 border-b border-white/[0.03]">
              <span className={`text-xs ${data.present ? "text-white/80" : "text-white/25"}`}>
                {name.replace(/_/g, " ")}
              </span>
              <span className={`text-[10px] font-mono ${data.present ? "text-[#FF6D00]" : "text-white/20"}`}>
                {(data.confidence * 100).toFixed(0)}%
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* No findings fallback */}
      {positiveFindings.length === 0 && (
        <div className="mt-6 py-6 text-center">
          <span className="text-sm text-white/30 font-light">No significant pathological findings detected.</span>
        </div>
      )}
    </div>
  );
}
