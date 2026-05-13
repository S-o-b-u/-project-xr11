"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { RetrievedCases } from "@/components/RetrievedCases";
import { Download, ArrowLeft } from "lucide-react";

function adaptPayload(raw: any) {
  const root = raw?.data ?? raw;
  const report = root?.report ?? {};
  const findings = report?.findings ?? report?.final_report ?? "";
  const impression = report?.impression ?? "";
  const recommendation = report?.recommendation ?? "";
  const fullReport = report?.final_report ?? "";
  const severity = (root?.severity?.overall_severity ?? "UNKNOWN").toUpperCase();
  const pathology = root?.pathology ?? null;
  const concepts = root?.concepts ?? [];
  const rawU = root?.uncertainty ?? {};
  const rawV = root?.verification ?? {};
  const retrieved = (root?.retrieval?.retrieved_cases ?? []).map((c: any, i: number) => ({
    id: c.case_id ?? c.id ?? String(i), gold_findings: c.gold_findings ?? "",
    gold_impression: c.gold_impression ?? "", similarity_score: c.final_score ?? c.similarity_score ?? 0,
    visual_score: c.visual_score ?? null, text_score: c.text_score ?? null, pathology_overlap: c.pathology_overlap ?? null,
  }));
  const positiveFindings: string[] = pathology?.positive_findings ?? [];
  const allFindings: [string, { present: boolean; confidence: number }][] = Object.entries(pathology?.findings ?? {}) as any;
  return {
    findings: findings, impression, recommendation, fullReport, severity,
    confidence: rawU.confidence ?? 0, hallSafe: !rawV.hallucination_detected,
    hallRisk: rawV.hallucination_risk ?? "unknown",
    positiveFindings, allFindings, abnormalityScore: pathology?.overall_abnormality_score ?? 0,
    pathology, concepts, retrieved, metadata: root?.metadata ?? null,
    round1: report?.round1_report ?? fullReport, round2: report?.round2_report ?? fullReport,
  };
}

const SEV: Record<string, string> = { NORMAL:"#22c55e", MILD:"#f59e0b", MODERATE:"#f97316", CRITICAL:"#ef4444", UNKNOWN:"#6b7280" };

function Bar({ value, color="#FF3D00", delay=0 }: { value:number; color?:string; delay?:number }) {
  return (
    <div className="w-full rounded-full overflow-hidden" style={{ height:6, background:"rgba(255,255,255,0.06)" }}>
      <motion.div initial={{ width:0 }} animate={{ width:`${Math.round(Math.min(1,Math.max(0,value))*100)}%` }}
        transition={{ duration:0.9, delay, ease:[0.16,1,0.3,1] }} style={{ height:"100%", background:color, borderRadius:99 }} />
    </div>
  );
}

function BentoCard({ children, className="", style={} }: any) {
  return (
    <div className={`rounded-2xl p-5 ${className}`} style={{ background:"#111", border:"1px solid rgba(255,255,255,0.06)", ...style }}>
      {children}
    </div>
  );
}

function Label({ children, className="" }: any) {
  return <p className={`text-[9px] uppercase tracking-[0.25em] text-white/30 mb-2 ${className}`}>{children}</p>;
}

function BigNum({ value, unit="" }: any) {
  return (
    <div className="flex items-baseline gap-1">
      <span style={{ fontFamily:"var(--font-display)", fontSize:"2.2rem", fontWeight:700, color:"white", lineHeight:1, letterSpacing:"-0.04em" }}>{value}</span>
      {unit && <span className="text-sm text-white/30">{unit}</span>}
    </div>
  );
}

export default function ReportPage() {
  const router = useRouter();
  const [adapted, setAdapted] = useState<ReturnType<typeof adaptPayload>|null>(null);
  const [imageUrl, setImageUrl] = useState<string|null>(null);
  const [mounted, setMounted] = useState(false);
  const [scanDone, setScanDone] = useState(false);
  const [rawPayload, setRawPayload] = useState<any>(null);

  useEffect(() => {
    setMounted(true);
    const raw = sessionStorage.getItem("reportData");
    const img = sessionStorage.getItem("imageUrl");
    if (!raw) return;
    try {
      const parsed = JSON.parse(raw);
      if (parsed?.data?.report || parsed?.data?.final_report || parsed?.report) {
        setRawPayload(parsed); setAdapted(adaptPayload(parsed)); setImageUrl(img);
      }
    } catch {}
  }, []);

  useEffect(() => { if (imageUrl) { const t = setTimeout(() => setScanDone(true), 1600); return () => clearTimeout(t); } }, [imageUrl]);

  const handleDownload = useCallback(() => {
    if (!adapted) return;
    const content = [
      `XR 11 RADIOLOGY REPORT\n${"=".repeat(50)}`,
      `Pipeline: ${adapted.metadata?.pipeline_version ?? "XR11_v2"}`,
      `Method: ${adapted.metadata?.generation_method ?? "multi-agent"}`,
      `Severity: ${adapted.severity}`,
      `Confidence: ${Math.round(adapted.confidence * 100)}%`,
      `\nFINDINGS\n${"-".repeat(30)}\n${adapted.findings}`,
      `\nIMPRESSION\n${"-".repeat(30)}\n${adapted.impression}`,
      `\nRECOMMENDATION\n${"-".repeat(30)}\n${adapted.recommendation}`,
      `\nPOSITIVE FINDINGS\n${"-".repeat(30)}\n${adapted.positiveFindings.join(", ") || "None"}`,
      `\nFULL REPORT\n${"-".repeat(30)}\n${adapted.fullReport}`,
    ].join("\n");
    const blob = new Blob([content], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url; a.download = "xr11-report.txt"; a.click();
    URL.revokeObjectURL(url);
  }, [adapted]);

  if (!mounted) return null;

  if (!adapted) return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-5" style={{ background:"#F0EFED" }}>
      <p className="text-xs font-mono uppercase tracking-widest text-black/30">No Analysis Found</p>
      <Link href="/" className="px-6 py-2.5 rounded-full text-[11px] font-semibold uppercase tracking-wider text-white" style={{ background:"#111" }}>Return Home</Link>
    </div>
  );

  const { findings, impression, recommendation, severity, confidence, hallSafe, positiveFindings, allFindings, abnormalityScore, retrieved, metadata, round1, round2 } = adapted;
  const sevColor = SEV[severity] ?? "#6b7280";
  const confPct = Math.round(confidence * 100);

  return (
    <motion.div initial={{ opacity:0 }} animate={{ opacity:1 }} style={{ background:"#F0EFED", minHeight:"100vh" }}>
      <div className="w-full max-w-[1600px] mx-auto px-8 lg:px-14 py-8">

        {/* ── PAGE HEADER ── */}
        <div className="flex items-end justify-between mb-8">
          <div>
            <p className="text-[9px] uppercase tracking-[0.3em] text-black/30 mb-1">Swarm Consensus Reached</p>
            <h1 style={{ fontFamily:"var(--font-display)", fontSize:"clamp(2.2rem,4vw,3.8rem)", fontWeight:700, color:"#111", lineHeight:0.9, letterSpacing:"-0.04em" }}>
              The<br /><span style={{ opacity:0.2 }}>Verdict</span>
            </h1>
          </div>
          <div className="flex items-center gap-3">
            <span className="px-4 py-1.5 rounded-full text-[10px] font-semibold uppercase tracking-wider" style={{ background:`${sevColor}18`, color:sevColor, border:`1px solid ${sevColor}30` }}>{severity}</span>
            <button onClick={handleDownload}
              className="group relative overflow-hidden flex items-center gap-2 px-4 py-2 rounded-full text-[11px] font-semibold uppercase tracking-wider text-black transition-all"
              style={{ background:"rgba(255,255,255,0.9)" }}>
              <div className="absolute inset-0 bg-white translate-y-full group-hover:translate-y-0 transition-transform duration-300 ease-out" />
              <Download className="relative z-10 w-3.5 h-3.5 transition-transform duration-300 group-hover:-translate-y-0.5" />
              <span className="relative z-10">Download</span>
            </button>
            <button onClick={() => { sessionStorage.removeItem("reportData"); sessionStorage.removeItem("imageUrl"); router.push("/"); }}
              className="group relative overflow-hidden flex items-center gap-2 px-5 py-2 rounded-full text-[11px] font-semibold uppercase tracking-wider text-white transition-all"
              style={{ background:"#111" }}>
              <div className="absolute inset-0 bg-white/[0.08] translate-y-full group-hover:translate-y-0 transition-transform duration-300 ease-out" />
              <span className="relative z-10 w-4 h-2.5 rounded-full transition-transform duration-300 group-hover:scale-125" style={{ background:"linear-gradient(135deg,#FF3D00,#FF6D00)" }} />
              <span className="relative z-10">Scan Another</span>
            </button>
          </div>
        </div>

        {/* ── 3-COLUMN DASHBOARD LAYOUT ── */}
        <div className="flex flex-col lg:flex-row gap-4">
          
          {/* ── LEFT COLUMN (Image & Metrics) ── */}
          <div className="w-full lg:w-[340px] flex-shrink-0 flex flex-col gap-4">
            
            {/* X-ray panel - Now compact */}
            <BentoCard style={{ padding:0, overflow:"hidden" }}>
              <div className="px-4 pt-4 pb-3 flex justify-between items-center" style={{ borderBottom:"1px solid rgba(255,255,255,0.05)" }}>
                <Label className="mb-0">The Evidence</Label>
              </div>
              <div className="relative flex items-center justify-center bg-black/40 p-4">
                {imageUrl ? (
                  <>
                    <AnimatePresence>
                      {!scanDone && (
                        <motion.div initial={{ top:"0%" }} animate={{ top:"100%" }} exit={{ opacity:0 }} transition={{ duration:1.4, ease:"easeInOut" }}
                          className="absolute left-0 right-0 h-0.5 z-10 pointer-events-none"
                          style={{ background:"linear-gradient(90deg,transparent,#FF3D00,transparent)", boxShadow:"0 0 14px rgba(255,61,0,0.5)" }} />
                      )}
                    </AnimatePresence>
                    <motion.img src={imageUrl} alt="X-ray" initial={{ clipPath:"inset(0 0 100% 0)" }} animate={{ clipPath:"inset(0 0 0% 0)" }}
                      transition={{ duration:1.4, ease:"easeInOut" }} className="w-full h-auto object-contain rounded"
                      style={{ filter:"grayscale(1) contrast(1.2)" }} />
                  </>
                ) : (
                  <span className="text-white/15 text-sm font-mono py-10">Did you forget the X-ray?</span>
                )}
              </div>
              {positiveFindings.length > 0 && (
                <div className="p-4 flex flex-wrap gap-1.5" style={{ borderTop:"1px solid rgba(255,255,255,0.05)" }}>
                  {positiveFindings.map(f => (
                    <span key={f} className="px-2 py-0.5 rounded-full text-[9px] font-semibold uppercase" style={{ background:"rgba(255,61,0,0.12)", color:"#FF6D00", border:"1px solid rgba(255,61,0,0.18)" }}>{f.replace(/_/g," ")}</span>
                  ))}
                </div>
              )}
            </BentoCard>

            {/* AI Insights panel */}
            <BentoCard>
              <div className="flex justify-between items-center mb-4">
                <Label className="mb-0">Swarm Intelligence</Label>
                <span className={`px-2.5 py-0.5 rounded-full text-[8px] font-semibold uppercase tracking-widest ${hallSafe?"text-emerald-400":"text-red-400"}`}
                  style={{ background: hallSafe?"rgba(34,197,94,0.1)":"rgba(239,68,68,0.1)", border:`1px solid ${hallSafe?"rgba(34,197,94,0.2)":"rgba(239,68,68,0.2)"}` }}>
                  {hallSafe?"Solid":"Sketchy"}
                </span>
              </div>
              <div className="space-y-4">
                <div>
                  <div className="flex justify-between mb-1.5"><span className="text-[9px] uppercase tracking-widest text-white/30">Confidence</span><span className="text-[9px] font-mono text-[#FF6D00]">{confPct}%</span></div>
                  <Bar value={confidence} color="#FF3D00" />
                </div>
                <div>
                  <div className="flex justify-between mb-1.5"><span className="text-[9px] uppercase tracking-widest text-white/30">Abnormality</span><span className="text-[9px] font-mono" style={{ color:sevColor }}>{Math.round(abnormalityScore*100)}%</span></div>
                  <Bar value={abnormalityScore} color={sevColor} delay={0.15} />
                </div>
              </div>
            </BentoCard>

            {/* Metrics Grid 2x2 */}
            <div className="grid grid-cols-2 gap-3">
              {[{ l:"Paranoia Level", v:`${confPct}`, u:"%", s:"MC Dropout" },
                { l:"Severity", v:severity, u:"", s:"Detection" },
                { l:"Plagiarized", v:String(retrieved.length), u:"", s:"Historical Cases" },
                { l:"Red Flags", v:String(positiveFindings.length), u:"", s:`Out of ${allFindings.length}` },
              ].map(m => (
                <BentoCard key={m.l} className="p-4">
                  <Label>{m.l}</Label>
                  <BigNum value={m.v} unit={m.u} />
                  <p className="text-[9px] text-white/25 mt-1 truncate">{m.s}</p>
                </BentoCard>
              ))}
            </div>

          </div>

          {/* ── MIDDLE COLUMN (Main Report Content) ── */}
          <div className="w-full lg:flex-1 flex flex-col gap-4">
            
            <BentoCard>
              <Label>What We Found</Label>
              <p className="text-[13px] text-white/70 leading-relaxed font-light">{findings || "—"}</p>
            </BentoCard>

            <BentoCard>
              <Label>The Bottom Line</Label>
              <p className="text-[13px] text-white/70 leading-relaxed font-medium">{impression || "—"}</p>
            </BentoCard>

            {/* Pathology Grid */}
            {allFindings.length > 0 && (
              <BentoCard>
                <div className="flex items-center gap-3 mb-4">
                  <Label className="mb-0">Abnormality Heatmap</Label>
                  <span className="text-[8px] font-mono text-white/15">TorchXRayVision</span>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-2">
                  {allFindings.map(([name, data]: any) => (
                    <div key={name} className="rounded-xl p-2.5" style={{ background:data.present?"rgba(255,61,0,0.06)":"rgba(255,255,255,0.02)", border:`1px solid ${data.present?"rgba(255,61,0,0.12)":"rgba(255,255,255,0.04)"}` }}>
                      <p className="text-[9px] font-medium mb-1.5 capitalize truncate" style={{ color:data.present?"#FF6D00":"rgba(255,255,255,0.3)" }}>{name.replace(/_/g," ")}</p>
                      <Bar value={data.confidence} color={data.present?"#FF3D00":"rgba(255,255,255,0.08)"} />
                      <p className="text-[8px] font-mono mt-1" style={{ color:data.present?"#FF6D00":"rgba(255,255,255,0.15)" }}>{Math.round(data.confidence*100)}%</p>
                    </div>
                  ))}
                </div>
              </BentoCard>
            )}

            {/* Round Comparison */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {[{ l:"Round 1 · Initial Draft", c:round1 }, { l:"Round 2 · Refined", c:round2 }].map(r => (
                <BentoCard key={r.l}>
                  <Label>{r.l}</Label>
                  <pre className="text-[10px] font-mono text-white/40 whitespace-pre-wrap leading-relaxed max-h-40 overflow-auto">{r.c || "—"}</pre>
                </BentoCard>
              ))}
            </div>

          </div>

          {/* ── RIGHT COLUMN (Context & Retrieval) ── */}
          <div className="w-full lg:w-[380px] flex-shrink-0 flex flex-col gap-4">
            
            <BentoCard>
              <div className="flex justify-between items-center mb-4">
                <Label className="mb-0">Suggested Steps</Label>
                <span className="text-[9px] px-2 py-0.5 rounded-full font-semibold" style={{ background:"rgba(255,61,0,0.1)", color:"#FF6D00", border:"1px solid rgba(255,61,0,0.18)" }}>Plan +</span>
              </div>
              {[{ e:"⚕", l:"Diagnostic", t:"Immediate", items:["Cross-reference symptoms","Check prior imaging","Confirm radiograph quality"] },
                { e:"👤", l:"Specialist", t:"If indicated", items: recommendation?[recommendation]:["Consult relevant specialist","Review with attending"] },
                { e:"📊", l:"Monitoring", t:"Ongoing", items:["Set follow-up reminder","Document progression"] },
              ].map(s => (
                <div key={s.l} className="flex gap-3 mb-4 last:mb-0">
                  <div className="w-6 h-6 rounded-full flex items-center justify-center text-[11px] flex-shrink-0 mt-0.5" style={{ background:"rgba(255,255,255,0.04)", border:"1px solid rgba(255,255,255,0.08)" }}>{s.e}</div>
                  <div>
                    <div className="flex gap-2 items-center mb-0.5"><span className="text-[11px] font-semibold text-white/70">{s.l}</span><span className="text-[9px] text-white/25">{s.t}</span></div>
                    {s.items.map((item,i) => <p key={i} className="text-[10px] text-white/35 leading-tight mb-1">• {item}</p>)}
                  </div>
                </div>
              ))}
            </BentoCard>

            <BentoCard className="flex-1">
              <RetrievedCases retrievedCases={retrieved} />
            </BentoCard>

          </div>
        </div>

        {/* ── FOOTER WATERMARK ── */}
        <div className="mt-12 mb-2 relative overflow-hidden">
          <p style={{ fontFamily:"var(--font-display)", fontSize:"8vw", fontWeight:700, color:"rgba(0,0,0,0.04)", lineHeight:1, letterSpacing:"-0.04em", userSelect:"none" }}>ANALYSIS</p>
          <div className="absolute bottom-2 right-0 text-right">
            <p className="text-[9px] uppercase tracking-[0.25em] text-black/20">{metadata?.pipeline_version ?? "XR11 v2"}</p>
            <p className="text-[9px] uppercase tracking-[0.25em] text-black/15">{metadata?.generation_method ?? "multi-agent"}</p>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
