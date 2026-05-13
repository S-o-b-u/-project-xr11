import type { RetrievedCase } from "@/types/report";
import { motion } from "framer-motion";

export interface RetrievedCasesProps {
  retrievedCases: RetrievedCase[];
  className?: string;
}

export function RetrievedCases({
  retrievedCases,
  className = "",
}: RetrievedCasesProps) {
  const topThree = retrievedCases.slice(0, 3);

  return (
    <div className={`flex flex-col ${className}`.trim()}>
      <div className="flex items-center gap-2 mb-5">
        <span className="accent-dot" style={{ width: 6, height: 6 }} />
        <h2 className="section-label">Retrieval Context</h2>
      </div>

      {topThree.length === 0 ? (
        <p className="text-xs text-white/30 font-light">No similar cases returned.</p>
      ) : (
        <ol className="flex flex-col gap-4">
          {topThree.map((item, index) => {
            const score = item.similarity_score ?? 0;
            // Handle both raw 0-1 scores and display any extra fields
            const extra = item as Record<string, unknown>;
            const visualScore  = typeof extra.visual_score === "number" ? extra.visual_score : null;
            const textScore    = typeof extra.text_score === "number" ? extra.text_score : null;
            const pathOverlap  = typeof extra.pathology_overlap === "number" ? extra.pathology_overlap : null;

            return (
              <motion.li
                key={item.id || `case-${index}`}
                className="card-dark p-4 rounded-xl"
                initial={{ x: 20, opacity: 0 }}
                whileInView={{ x: 0, opacity: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: index * 0.08 }}
              >
                {/* Top bar */}
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className="text-[9px] font-mono tracking-widest text-white/30 uppercase">
                      #{index + 1}
                    </span>
                    {item.id && (
                      <span className="text-[10px] font-mono text-white/50">
                        Case {item.id}
                      </span>
                    )}
                  </div>
                  <motion.span
                    className="text-xs font-mono text-[#FF6D00] font-semibold"
                    initial={{ opacity: 0, scale: 0.5 }}
                    whileInView={{ opacity: 1, scale: 1 }}
                    viewport={{ once: true }}
                    transition={{ type: "spring", stiffness: 400, damping: 25, delay: 0.2 + index * 0.08 }}
                  >
                    {(score * 100).toFixed(1)}%
                  </motion.span>
                </div>

                {/* Score breakdown bars */}
                {(visualScore !== null || textScore !== null || pathOverlap !== null) && (
                  <div className="space-y-2 mb-3">
                    {[
                      { label: "Visual", value: visualScore },
                      { label: "Text", value: textScore },
                      { label: "Pathology", value: pathOverlap },
                    ].filter(s => s.value !== null).map(s => (
                      <div key={s.label} className="flex items-center gap-3">
                        <span className="text-[8px] font-mono text-white/25 uppercase w-14 shrink-0">{s.label}</span>
                        <div className="flex-1 h-1 bg-white/[0.04] rounded-full overflow-hidden">
                          <motion.div
                            initial={{ width: 0 }}
                            whileInView={{ width: `${Math.min(100, (s.value ?? 0) * 100)}%` }}
                            viewport={{ once: true }}
                            transition={{ duration: 0.6, delay: 0.3 }}
                            className="h-full rounded-full accent-bar"
                          />
                        </div>
                        <span className="text-[9px] font-mono text-white/30 w-8 text-right">
                          {((s.value ?? 0) * 100).toFixed(0)}
                        </span>
                      </div>
                    ))}
                  </div>
                )}

                {/* Findings text */}
                <p className="text-[11px] leading-relaxed text-white/40 font-light line-clamp-2">
                  {item.gold_findings || item.gold_impression || "—"}
                </p>
              </motion.li>
            );
          })}
        </ol>
      )}
    </div>
  );
}
