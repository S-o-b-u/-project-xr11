import type { UncertaintyData } from "@/types/report";
import { motion } from "framer-motion";

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
  const { confidence, entropy, semantic_variance, needs_human_review, severity_votes } = uncertainty;
  const confidencePct = confidenceToPercent(confidence);
  const voteEntries = Object.entries(severity_votes).sort((a, b) => b[1] - a[1]);
  const maxVotes = Math.max(...voteEntries.map(([, count]) => count), 1);

  return (
    <div className={`card-dark p-8 md:p-10 ${className}`.trim()}>
      {/* Header */}
      <div className="flex items-center justify-between mb-8 pb-5 border-b border-white/[0.06]">
        <div className="flex items-center gap-3">
          <span className="accent-dot" />
          <h2
            style={{ fontFamily: "var(--font-display)" }}
            className="text-xl md:text-2xl font-bold text-white uppercase tracking-wide"
          >
            Uncertainty
          </h2>
        </div>
        {needs_human_review && (
          <span className="accent-pill text-[9px]">
            <span className="w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse" />
            Review Recommended
          </span>
        )}
      </div>

      {/* Big numbers row */}
      <div className="grid grid-cols-3 gap-8 mb-10">
        {/* Confidence — hero number */}
        <div className="flex flex-col">
          <span className="section-label mb-3">Confidence</span>
          <div className="flex items-baseline gap-1">
            <motion.span
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              style={{ fontFamily: "var(--font-display)" }}
              className="text-5xl md:text-6xl font-bold text-white tracking-tight"
            >
              {confidencePct.toFixed(0)}
            </motion.span>
            <span className="text-xl text-white/30 font-light">%</span>
          </div>
          {/* Mini bar */}
          <div className="w-full h-1.5 bg-white/[0.04] rounded-full mt-3 overflow-hidden">
            <motion.div
              initial={{ width: 0 }}
              whileInView={{ width: `${confidencePct}%` }}
              viewport={{ once: true }}
              transition={{ duration: 1, delay: 0.3 }}
              className="h-full rounded-full accent-bar"
            />
          </div>
        </div>

        {/* Entropy */}
        <div className="flex flex-col">
          <span className="section-label mb-3">Entropy</span>
          <motion.span
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.1 }}
            className="text-4xl md:text-5xl font-light text-white tracking-tight"
          >
            {formatMetric(entropy)}
          </motion.span>
        </div>

        {/* Semantic Variance */}
        <div className="flex flex-col">
          <span className="section-label mb-3">Variance</span>
          <motion.span
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="text-4xl md:text-5xl font-light text-white tracking-tight"
          >
            {formatMetric(semantic_variance)}
          </motion.span>
        </div>
      </div>

      {/* Vote distribution */}
      <div>
        <h3 className="section-label mb-5 flex items-center gap-2">
          <div className="w-1 h-1 rounded-full bg-[#FF3D00]" />
          Monte Carlo Severity Votes
        </h3>
        {voteEntries.length === 0 ? (
          <p className="text-xs text-white/30">No vote data returned.</p>
        ) : (
          <div className="space-y-4">
            {voteEntries.map(([label, count], index) => {
              const pct = (count / maxVotes) * 100;
              const isMajority = label === uncertainty.majority_severity;

              return (
                <div key={label} className="grid grid-cols-[100px_1fr_40px] items-center gap-5">
                  <span className={`text-[10px] font-mono tracking-widest uppercase ${isMajority ? "text-[#FF6D00]" : "text-white/40"}`}>
                    {label}
                  </span>
                  <div className="h-2 w-full bg-white/[0.04] rounded-full relative overflow-hidden">
                    <motion.div
                      className={`absolute top-0 left-0 h-full rounded-full ${isMajority ? "accent-bar" : "bg-white/20"}`}
                      initial={{ width: 0 }}
                      whileInView={{ width: `${pct}%` }}
                      viewport={{ once: true }}
                      transition={{ duration: 0.8, delay: 0.3 + index * 0.1, ease: [0.16, 1, 0.3, 1] }}
                    />
                    {isMajority && (
                      <motion.div
                        className="absolute top-0 left-0 h-full rounded-full"
                        initial={{ opacity: 0 }}
                        whileInView={{ opacity: [0, 0.4, 0] }}
                        viewport={{ once: true }}
                        transition={{ duration: 1.5, repeat: 2, delay: 1.1 }}
                        style={{ width: `${pct}%`, background: "linear-gradient(90deg, #FF3D00, #FF6D00)", filter: "blur(6px)" }}
                      />
                    )}
                  </div>
                  <span className="text-xs font-mono text-white/50 text-right">
                    {count}
                  </span>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
