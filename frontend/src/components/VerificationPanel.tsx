import type {
  HallucinationResult,
  KnowledgeGraphResult,
  NliCheckResult,
} from "@/types/report";
import { motion } from "framer-motion";

export interface VerificationPanelProps {
  nli_check: NliCheckResult;
  knowledge_graph: KnowledgeGraphResult;
  hallucination: HallucinationResult;
  className?: string;
}

const nliColors: Record<string, string> = {
  ENTAILS:     "text-emerald-400 border-emerald-400/20 bg-emerald-400/[0.06]",
  CONTRADICTS: "text-red-400 border-red-400/20 bg-red-400/[0.06]",
  NEUTRAL:     "text-amber-400 border-amber-400/20 bg-amber-400/[0.06]",
};

export function VerificationPanel({
  nli_check,
  knowledge_graph,
  hallucination,
  className = "",
}: VerificationPanelProps) {
  const icd10Codes = knowledge_graph.icd10_codes ?? [];

  const cards = [
    {
      label: "NLI Consistency",
      content: (
        <>
          <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-full border text-[10px] font-mono tracking-widest uppercase mb-5 ${nliColors[nli_check.nli_result] ?? nliColors.NEUTRAL}`}>
            <span className="w-1.5 h-1.5 rounded-full bg-current" />
            {String(nli_check.nli_result ?? "—")}
          </span>
          <div className="space-y-2.5">
            <div className="flex justify-between text-[10px] font-mono text-white/40 border-b border-white/[0.04] pb-2">
              <span>SEVERITY</span>
              <span className="text-white/70">{String(nli_check.severity_check ?? "—")}</span>
            </div>
            <div className="flex justify-between text-[10px] font-mono text-white/40 border-b border-white/[0.04] pb-2">
              <span>SCORE</span>
              <span className="text-white/70">{nli_check.consistency_score?.toFixed(3) ?? "—"}</span>
            </div>
          </div>
          {nli_check.contradictions && (
            <div className="mt-4">
              <span className="text-[9px] text-white/30 uppercase tracking-widest block mb-1">Contradictions</span>
              <p className="text-xs text-white/50 font-light leading-relaxed">{nli_check.contradictions}</p>
            </div>
          )}
        </>
      ),
    },
    {
      label: "Ontology Grounding",
      content: (
        <>
          <div className="space-y-2.5 mb-5">
            <div className="flex justify-between text-[10px] font-mono text-white/40 border-b border-white/[0.04] pb-2">
              <span>STD RATE</span>
              <span className="text-white/70">{knowledge_graph.standardization_rate?.toFixed(3) ?? "—"}</span>
            </div>
            <div className="flex justify-between text-[10px] font-mono text-white/40 border-b border-white/[0.04] pb-2">
              <span>TERMS</span>
              <span className="text-white/70">{knowledge_graph.terms_found?.length ?? 0}</span>
            </div>
          </div>
          {icd10Codes.length > 0 && (
            <div>
              <span className="text-[9px] text-white/30 uppercase tracking-widest block mb-2">ICD-10 Mapping</span>
              <div className="flex flex-wrap gap-1.5">
                {icd10Codes.slice(0, 5).map((row) => (
                  <span key={row.icd10_code} className="text-[10px] font-mono text-[#FF6D00]/80 border border-[#FF3D00]/15 bg-[#FF3D00]/[0.04] px-2 py-0.5 rounded-md">
                    {row.icd10_code}
                  </span>
                ))}
                {icd10Codes.length > 5 && <span className="text-[10px] text-white/30">+{icd10Codes.length - 5}</span>}
              </div>
            </div>
          )}
        </>
      ),
    },
    {
      label: "Hallucination Risk",
      content: (
        <>
          <span className={`inline-flex items-center gap-2 px-3 py-1 rounded-full border text-[10px] font-mono tracking-widest uppercase mb-5 ${hallucination.safe_to_use ? "text-emerald-400 border-emerald-400/20 bg-emerald-400/[0.06]" : "text-red-400 border-red-400/20 bg-red-400/[0.06]"}`}>
            <span className="w-1.5 h-1.5 rounded-full bg-current" />
            {hallucination.safe_to_use ? "SAFE" : "REVIEW"}
          </span>
          <div className="space-y-2.5">
            <div className="flex justify-between text-[10px] font-mono text-white/40 border-b border-white/[0.04] pb-2">
              <span>RISK</span>
              <span className="text-white/70">{String(hallucination.overall_risk ?? "—")}</span>
            </div>
            <div className="flex justify-between text-[10px] font-mono text-white/40 border-b border-white/[0.04] pb-2">
              <span>SCORE</span>
              <span className="text-white/70">{hallucination.hallucination_score?.toFixed(3) ?? "—"}</span>
            </div>
            <div className="flex justify-between text-[10px] font-mono text-white/40 border-b border-white/[0.04] pb-2">
              <span>CLAIMS</span>
              <span className="text-white/70">{hallucination.claim_verifications?.length ?? 0}</span>
            </div>
          </div>
        </>
      ),
    },
  ];

  return (
    <div className={`${className}`.trim()}>
      <div className="flex items-center gap-3 mb-6">
        <span className="accent-dot" />
        <h2
          style={{ fontFamily: "var(--font-display)" }}
          className="text-xl md:text-2xl font-bold text-white uppercase tracking-wide"
        >
          Verification
        </h2>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {cards.map((card, i) => (
          <motion.div
            key={card.label}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: i * 0.1 }}
            className="card-dark p-6"
          >
            <span className="accent-pill text-[8px] mb-5 inline-flex">{card.label}</span>
            {card.content}
          </motion.div>
        ))}
      </div>
    </div>
  );
}
