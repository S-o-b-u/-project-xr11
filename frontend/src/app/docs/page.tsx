"use client";

import { motion } from "framer-motion";

const PIPELINE_STEPS = [
  {
    title: "Retrieval",
    desc: "Extracts image embeddings using MedCLIP and searches the FAISS index for top 3 historically similar cases to provide clinical context.",
    color: "bg-emerald-400"
  },
  {
    title: "Quantification",
    desc: "Runs 5 Monte Carlo dropout passes to estimate model uncertainty, outputting severity votes, entropy, and semantic variance.",
    color: "bg-amber-400"
  },
  {
    title: "Round 1 Gen",
    desc: "Drafts the initial findings and impressions based on the target radiograph and retrieved RAG context (Temperature 0.3).",
    color: "bg-violet-400"
  },
  {
    title: "Round 2 Refine",
    desc: "Critiques the Round 1 draft for contradictions, formatting, and clinical flow, producing the final refined text.",
    color: "bg-blue-400"
  },
  {
    title: "Verification",
    desc: "Grounds terms in the RadLex ontology (OWL), checks NLI entailment against Round 1, and assigns a Hallucination Risk score.",
    color: "bg-rose-400"
  }
];

export default function DocsPage() {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { 
      opacity: 1,
      transition: { staggerChildren: 0.15, delayChildren: 0.2 }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, x: -20 },
    visible: { opacity: 1, x: 0, transition: { duration: 0.8, ease: [0.16, 1, 0.3, 1] } }
  };

  return (
    <div className="flex-1 max-w-[1600px] w-full mx-auto px-10 pb-32 pt-16 flex flex-col justify-center min-h-[70vh]">
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_1.5fr] gap-24">
        
        {/* Left Col */}
        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          className="space-y-6"
        >
          <h1 
            style={{ fontFamily: "var(--font-display)" }}
            className="text-[clamp(3rem,6vw,5.5rem)] font-bold uppercase leading-[0.85] tracking-tighter text-white"
          >
            Pipeline<br />Architecture
          </h1>
          <p className="text-sm tracking-wide text-white/40 max-w-md leading-relaxed font-light">
            The XR 11 operates on a multi-stage deterministic pipeline ensuring clinical accuracy, grounded context, and rigid uncertainty bounds.
          </p>
        </motion.div>

        {/* Right Col */}
        <motion.div 
          variants={containerVariants}
          initial="hidden"
          animate="visible"
          className="relative border-l border-white/5 pl-12 py-4"
        >
          <div className="space-y-16">
            {PIPELINE_STEPS.map((step, i) => (
              <motion.div key={step.title} variants={itemVariants} className="relative">
                {/* Timeline dot */}
                <div className="absolute -left-[53px] top-1.5 w-2 h-2 rounded-full border border-white bg-[#08080f]" />
                
                <h3 className="text-xl font-light text-white mb-3 flex items-center gap-4">
                  <span className="text-[10px] font-mono tracking-widest text-white/40 border border-white/10 px-2 py-0.5 rounded">
                    PHASE 0{i + 1}
                  </span>
                  {step.title}
                </h3>
                <p className="text-sm leading-relaxed text-white/50 font-light">
                  {step.desc}
                </p>
              </motion.div>
            ))}
          </div>
        </motion.div>

      </div>
    </div>
  );
}
