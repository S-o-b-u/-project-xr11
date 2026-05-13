"use client";

import { generateReport } from "@/lib/api";
import axios from "axios";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { AnimatePresence, motion, useMotionValue, useSpring, useTransform } from "framer-motion";
import { Network, Database, Cpu, RefreshCw, ShieldCheck, FileText, Check, ArrowRight } from "lucide-react";
import { useCallback, useEffect, useRef, useState, type DragEvent, type ChangeEvent } from "react";
import { TiltCard } from "@/components/TiltCard";
import dynamic from "next/dynamic";

const ACCEPT_TYPES = new Set(["image/png", "image/jpeg", "image/jpg"]);
const PIPELINE_STEPS = ["Waking the agents...","Arguing about pathology","Extracting multimodal truth","Building the knowledge graph","Interrogating 3,955 historical cases","Synthesizing the verdict","Checking for hallucinations","Finalizing payload..."];

function isAcceptedImage(f: File) { const t = f.type.toLowerCase(); if (ACCEPT_TYPES.has(t)) return true; const n = f.name.toLowerCase(); return n.endsWith(".png")||n.endsWith(".jpg")||n.endsWith(".jpeg"); }
function readFileAsDataUrl(f: File): Promise<string> { return new Promise((res,rej)=>{ const fr=new FileReader(); fr.onload=()=>res(fr.result as string); fr.onerror=()=>rej(fr.error); fr.readAsDataURL(f); }); }
function parseAxiosMessage(err: unknown): string { if (!axios.isAxiosError(err)) return err instanceof Error?err.message:"Something went wrong."; const d=err.response?.data as any; if(d&&typeof d==="object"&&"detail"in d){const x=d.detail; if(typeof x==="string") return x;} return err.message||"Request failed."; }

export default function Home() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const stepIntervalRef = useRef<ReturnType<typeof setInterval>|null>(null);
  const [file, setFile] = useState<File|null>(null);
  const [previewUrl, setPreviewUrl] = useState<string|null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [loading, setLoading] = useState(false);
  const [stepIndex, setStepIndex] = useState(0);
  const [error, setError] = useState<string|null>(null);

  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);
  const springX = useSpring(mouseX, { stiffness: 60, damping: 20 });
  const springY = useSpring(mouseY, { stiffness: 60, damping: 20 });
  const heroX = useTransform(springX, x => x * 18);
  const heroY = useTransform(springY, y => y * 12);
  const [carouselIndex, setCarouselIndex] = useState(0);
  
  useEffect(() => {
    const onMove = (e: MouseEvent) => { mouseX.set((e.clientX/window.innerWidth)-0.5); mouseY.set((e.clientY/window.innerHeight)-0.5); };
    window.addEventListener("mousemove", onMove);
    return () => { window.removeEventListener("mousemove", onMove); if(stepIntervalRef.current) clearInterval(stepIntervalRef.current); };
  }, [mouseX, mouseY]);

  useEffect(() => () => { if(previewUrl) URL.revokeObjectURL(previewUrl); }, [previewUrl]);

  const assignFile = useCallback((next: File|null) => {
    setError(null);
    setPreviewUrl(prev => { if(prev) URL.revokeObjectURL(prev); if(!next||!isAcceptedImage(next)) return null; return URL.createObjectURL(next); });
    if(!next){setFile(null);return;}
    if(!isAcceptedImage(next)){setFile(null);setError("Please use a PNG or JPG/JPEG chest X-ray image.");return;}
    setFile(next);
  }, []);

  const openPicker = () => fileInputRef.current?.click();
  const onInputChange = (e: ChangeEvent<HTMLInputElement>) => { assignFile(e.target.files?.[0]??null); e.target.value=""; };
  const onDragOver = (e: DragEvent) => { e.preventDefault(); e.stopPropagation(); setDragActive(true); };
  const onDragLeave = (e: DragEvent) => { e.preventDefault(); e.stopPropagation(); setDragActive(false); };
  const onDrop = (e: DragEvent) => { e.preventDefault(); e.stopPropagation(); setDragActive(false); assignFile(e.dataTransfer.files?.[0]??null); };

  const handleGenerate = async () => {
    if(!file||loading) return;
    setError(null); setLoading(true); setStepIndex(0);
    if(stepIntervalRef.current) clearInterval(stepIntervalRef.current);
    stepIntervalRef.current = setInterval(() => setStepIndex(i=>Math.min(i+1,PIPELINE_STEPS.length-1)), 2400);
    try {
      const [result, imageUrl] = await Promise.all([generateReport(file), readFileAsDataUrl(file)]);
      sessionStorage.setItem("reportData", JSON.stringify(result));
      sessionStorage.setItem("imageUrl", imageUrl);
      router.push("/report");
    } catch(err) { setError(parseAxiosMessage(err)); }
    finally { if(stepIntervalRef.current){clearInterval(stepIntervalRef.current);stepIntervalRef.current=null;} setLoading(false); }
  };

  return (
    <motion.div initial={{ opacity:0 }} animate={{ opacity:1 }} className="w-full flex flex-col">

      {/* ══ HERO — Light Theme ══ */}
      <section className="relative w-full overflow-hidden" style={{ minHeight: "100vh", background: "#F0EFED" }}>
        
        {/* Content */}
        <div className="relative z-10 w-full max-w-[1500px] mx-auto px-8 lg:px-14 h-full flex flex-col items-center" style={{ minHeight: "100vh" }}>
          
          {/* Top row: left text + right card */}
          <div className="grid grid-cols-3 items-start gap-0 pt-24 w-full">
            
            {/* LEFT: massive headline + begin now */}
            <motion.div initial={{ opacity:0, y:20 }} animate={{ opacity:1, y:0 }} transition={{ duration:0.7, ease:[0.16,1,0.3,1] }} className="flex flex-col gap-6 pt-2 ">
              <h2 style={{ fontFamily:"var(--font-display)", fontSize:"clamp(3rem, 5vw, 5.5rem)", fontWeight:700, color:"#111", lineHeight:0.95, letterSpacing:"-0.03em" }}>
                REDEFINE<br />
                <span style={{ fontWeight:300, color:"#666" }}>IMAGING.</span>
              </h2>
              <p style={{ fontSize:"clamp(14px, 1.2vw, 16px)", color:"#777", maxWidth:320, lineHeight:1.7 }}>
                Because relying on a single tired radiologist at 3 AM is so last decade. We use a 12-step multi-agent AI swarm instead.
              </p>
              <button onClick={openPicker}
                className="relative overflow-hidden group self-start flex items-center gap-3 px-6 py-3 rounded-full font-semibold text-white text-[12px] tracking-wide transition-all"
                style={{ background:"#111", boxShadow:"0 2px 16px rgba(0,0,0,0.18)" }}>
                <div className="absolute inset-0 bg-white/[0.08] translate-y-full group-hover:translate-y-0 transition-transform duration-300 ease-out rounded-full" />
                <span className="relative z-10 w-8 h-5 rounded-full transition-transform duration-300 group-hover:scale-110" style={{ background:"linear-gradient(135deg,#FF3D00,#FF6D00)" }} />
                <span className="relative z-10">Wake the Agents</span>
                <ArrowRight className="relative z-10 w-3.5 h-3.5 opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all duration-300" />
              </button>
            </motion.div>

            {/* CENTER: empty placeholder since image is absolute now */}
            <div className="pointer-events-none" />

            {/* RIGHT: floating premium cards */}
            <motion.div initial={{ opacity:0, y:-15 }} animate={{ opacity:1, y:0 }} transition={{ duration:0.7, delay:0.25, ease:[0.16,1,0.3,1] }} className="flex flex-col items-end gap-4 pt-2">
              
              <div className="flex gap-4">
                {/* Square 1: Diagnostic Match */}
                <div className="w-[140px] h-[140px] bg-[#111] rounded-[24px] p-4 flex flex-col justify-between relative overflow-hidden border border-white/5 shadow-2xl">
                  <div className="flex justify-between items-start z-10">
                    <p className="text-[9px] uppercase tracking-wider text-white/50 font-semibold">Accuracy</p>
                  </div>
                  <div className="absolute inset-0 flex items-center justify-center opacity-40 top-4">
                    <svg viewBox="0 0 100 40" className="w-full h-full drop-shadow-[0_4px_6px_rgba(255,109,0,0.5)]" preserveAspectRatio="none">
                      <path d="M-5,35 Q15,20 25,25 T45,15 T65,20 T85,5 T105,10" fill="none" stroke="#FF6D00" strokeWidth="2.5" strokeLinecap="round" />
                    </svg>
                  </div>
                  <div className="z-10">
                    <div className="text-4xl font-bold text-white tracking-tighter" style={{ fontFamily:"var(--font-display)" }}>94<span className="text-xl">%</span></div>
                    <p className="text-[8px] text-white/30 uppercase mt-1">RadLex Match</p>
                  </div>
                </div>

                {/* Square 2: Performance Latency */}
                <div className="w-[140px] h-[140px] bg-[#111] rounded-[24px] p-4 flex flex-col justify-between relative overflow-hidden border border-white/5 shadow-2xl">
                  <div className="absolute top-0 right-0 w-32 h-32 bg-[#A3FF00] rounded-full blur-[40px] opacity-[0.08] -translate-y-12 translate-x-12" />
                  <div className="flex justify-between items-start z-10">
                    <p className="text-[9px] uppercase tracking-wider text-white/50 font-semibold">Latency</p>
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#A3FF00" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"></polyline><polyline points="16 7 22 7 22 13"></polyline></svg>
                  </div>
                  <div className="z-10">
                    <div className="text-4xl font-bold text-[#A3FF00] tracking-tighter" style={{ fontFamily:"var(--font-display)" }}>65<span className="text-xl">s</span></div>
                    <p className="text-[8px] text-white/30 uppercase mt-1">Per Generation</p>
                  </div>
                </div>
              </div>

              {/* Live Carousel: auto-rotating wide cards */}
              <div className="w-[296px] h-[120px] relative">
                <AnimatePresence mode="wait">
                  {(() => {
                    const CAROUSEL_SLIDES = [
                      { tag: "Architecture", accent: "#FF6D00", leftBg: "linear-gradient(135deg, #FF6D00, #FF3D00)", leftText: "XR", title: "12-Step Parallel Reasoning", desc: "Agents debate pathology until consensus is reached." },
                      { tag: "Verified", accent: "#A3FF00", leftBg: "linear-gradient(135deg, #A3FF00, #6BBF00)", leftText: "✓", title: "Hallucination-Proof Output", desc: "Every finding cross-checked against 3,955 historical cases." },
                      { tag: "Pipeline", accent: "#00D4FF", leftBg: "linear-gradient(135deg, #00D4FF, #0088CC)", leftText: "⚡", title: "Multi-Modal Fusion Engine", desc: "Vision + language models arguing at machine speed." },
                      { tag: "Precision", accent: "#FF6D00", leftBg: "linear-gradient(135deg, #FF3D00, #CC2200)", leftText: "Δ", title: "Uncertainty Quantification", desc: "Confidence intervals on every single diagnosis line." },
                    ];
                    const slide = CAROUSEL_SLIDES[carouselIndex % CAROUSEL_SLIDES.length];
                    return (
                      <motion.div
                        key={carouselIndex}
                        initial={{ opacity: 0, y: 20, scale: 0.97 }}
                        animate={{ opacity: 1, y: 0, scale: 1 }}
                        exit={{ opacity: 0, y: -20, scale: 0.97 }}
                        transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
                        className="absolute inset-0 rounded-[24px] overflow-hidden flex shadow-2xl bg-[#111] border border-white/5"
                      >
                        <div className="w-[110px] h-full relative flex items-center justify-center overflow-hidden" style={{ background: slide.leftBg }}>
                          <div className="absolute inset-0 bg-white opacity-20" style={{ clipPath: "polygon(0 0, 100% 0, 100% 30%, 0 60%)" }} />
                          <span className="absolute text-5xl font-black tracking-tighter text-black/20" style={{ textShadow: "1px 1px 0 rgba(255,255,255,0.25), -1px -1px 0 rgba(0,0,0,0.15)", fontFamily: "var(--font-display)" }}>{slide.leftText}</span>
                        </div>
                        <div className="flex-1 p-5 flex flex-col justify-center">
                          <p className="text-[8px] uppercase tracking-[0.2em] mb-1 font-bold" style={{ color: slide.accent }}>{slide.tag}</p>
                          <p className="text-sm text-white font-medium leading-tight mb-1">{slide.title}</p>
                          <p className="text-[9px] text-white/40 leading-relaxed mt-1">{slide.desc}</p>
                        </div>
                      </motion.div>
                    );
                  })()}
                </AnimatePresence>
                {/* Dot indicators */}
                <div className="absolute -bottom-5 left-1/2 -translate-x-1/2 flex gap-1.5">
                  {[0,1,2,3].map(i => (
                    <div key={i} className="w-1 h-1 rounded-full transition-all duration-300" style={{ background: (carouselIndex % 4) === i ? "#FF6D00" : "rgba(255,255,255,0.15)" }} />
                  ))}
                </div>
              </div>

            </motion.div>
          </div>

          {/* Hero Image Stuck to Bottom (No float, no blend mode) */}
          <motion.div 
            style={{ x:heroX }} 
            className="absolute bottom-0 left-1/2 -translate-x-1/2 z-20 pointer-events-none flex items-end justify-center"
          >
            <Image
              src="/hero.png?v=2" alt="XR 11 AI Radiology"
              width={1050} height={950}
              priority
              unoptimized
              className="object-contain select-none"
              style={{ filter:"drop-shadow(0 40px 80px rgba(0,0,0,0.15))", maxHeight:"88vh", width:"auto", objectPosition: "bottom" }}
            />
          </motion.div>
        </div>

        {/* Bottom: massive watermark — sits behind hero image (z-10 < hero z-20) */}
        <div className="absolute bottom-0 left-0 right-0 overflow-visible pointer-events-none select-none z-10" style={{ lineHeight:0.85 }}>
          <motion.div style={{ x:heroX, fontFamily:"var(--font-display)", fontSize:"14vw", fontWeight:800, letterSpacing:"-0.08em", color:"rgba(17,17,17,0.065)", textTransform:"uppercase", whiteSpace:"nowrap", marginLeft: "-0.5vw", paddingBottom: "2vw" }} aria-hidden>
            radiology
          </motion.div>
        </div>
      </section>


      {/* ══ UPLOAD SECTION ══ */}
      <section id="upload-section" className="relative w-full bg-[#050505] flex flex-col items-center overflow-hidden" style={{ zIndex:10 }}>
        
        {/* Massive background watermark */}
        <div className="absolute inset-0 pointer-events-none flex items-center justify-center opacity-[0.02] select-none">
          <span style={{ fontFamily:"var(--font-display)", fontSize:"25vw", fontWeight:900, whiteSpace:"nowrap", color:"white" }}>DROP</span>
        </div>

        <div className="relative w-full max-w-[720px] mx-auto px-8 pb-24 pt-24 z-10">

          <label htmlFor="xray-upload" className="sr-only">Upload X-ray</label>
          <input id="xray-upload" ref={fileInputRef} type="file" accept="image/png,image/jpeg,.jpg,.jpeg" className="sr-only" onChange={onInputChange} />

          <AnimatePresence mode="wait">
            {loading ? (
              <motion.div key="loading" initial={{ opacity:0 }} animate={{ opacity:1 }} exit={{ opacity:0 }}
                className="relative flex flex-col items-center justify-center" style={{ minHeight:320 }}>
                <AnimatePresence mode="wait">
                  <motion.div key={stepIndex}
                    initial={{ opacity:0, y:40, filter:"blur(8px)" }}
                    animate={{ opacity:1, y:0, filter:"blur(0px)" }}
                    exit={{ opacity:0, y:-40, filter:"blur(8px)" }}
                    transition={{ duration:0.65, ease:[0.16,1,0.3,1] }}
                    className="absolute text-center">
                    <p style={{ fontFamily:"var(--font-display)", fontSize:"clamp(2rem,4vw,3rem)", fontWeight:700, color:"white", letterSpacing:"-0.04em", lineHeight:1 }}>
                      {["Connecting","Retrieving","Sampling","Generating","Refining","Verifying","Finalising"][stepIndex]}
                    </p>
                    <p className="text-sm text-white/30 mt-3 tracking-widest uppercase">{PIPELINE_STEPS[stepIndex]}</p>
                  </motion.div>
                </AnimatePresence>
                <div className="absolute bottom-0 left-0 right-0 h-px bg-white/[0.05]">
                  <motion.div initial={{ scaleX:0 }} animate={{ scaleX:(stepIndex+1)/PIPELINE_STEPS.length }}
                    style={{ originX:0, background:"linear-gradient(90deg,#FF3D00,#FF6D00)", height:"100%" }}
                    transition={{ duration:0.5 }} />
                </div>
                <p className="absolute bottom-4 text-[9px] font-mono text-white/20 tracking-[0.3em] uppercase">{stepIndex+1}/{PIPELINE_STEPS.length} · ~60–90s</p>
              </motion.div>
            ) : (
              <motion.div key="upload" initial={{ opacity:0 }} animate={{ opacity:1 }} exit={{ opacity:0 }} className="space-y-6">
                
                {/* Premium Drop zone */}
                <motion.div whileHover={{ scale:1.02 }} whileTap={{ scale:0.98 }}
                  onDragOver={onDragOver} onDragLeave={onDragLeave} onDrop={onDrop} onClick={openPicker}
                  className="relative cursor-pointer rounded-[2rem] flex flex-col items-center justify-center transition-all duration-500 overflow-hidden group"
                  style={{ 
                    height: 360, 
                    background: dragActive ? "rgba(255,61,0,0.05)" : "rgba(255,255,255,0.02)", 
                    border: `1px solid ${dragActive ? "rgba(255,61,0,0.4)" : "rgba(255,255,255,0.08)"}`, 
                    boxShadow: dragActive ? "0 0 40px rgba(255,61,0,0.1) inset" : "0 20px 40px rgba(0,0,0,0.5)" 
                  }}>
                  
                  {/* Glass highlight */}
                  <div className="absolute inset-0 bg-gradient-to-b from-white/[0.04] to-transparent pointer-events-none" />

                  {previewUrl ? (
                    <motion.div initial={{ opacity:0, scale:0.92 }} animate={{ opacity:1, scale:1 }} className="flex flex-col items-center gap-5 z-10">
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img src={previewUrl} alt="Preview" className="max-h-60 object-contain rounded-xl shadow-2xl" style={{ filter:"grayscale(1) contrast(1.15)", border:"1px solid rgba(255,255,255,0.1)" }} />
                      <span className="text-[11px] font-mono text-white/40 bg-black/50 px-4 py-1.5 rounded-full">{file?.name}</span>
                    </motion.div>
                  ) : (
                    <div className="text-center space-y-4 z-10">
                      <div className="mx-auto w-14 h-14 rounded-full border border-white/10 flex items-center justify-center bg-white/[0.02] group-hover:bg-white/[0.06] transition-colors duration-300">
                        <ArrowRight className="w-5 h-5 text-white/30 -rotate-90 group-hover:text-white/70 transition-colors duration-300" />
                      </div>
                      <p className="text-[13px] uppercase tracking-[0.25em] font-semibold" style={{ color: dragActive?"#FF6D00":"rgba(255,255,255,0.4)" }}>
                        {dragActive?"Drop to initiate sequence":"Drop Radiograph Here"}
                      </p>
                      <p className="text-[10px] font-mono text-white/20 tracking-wider">SUPPORTED: PNG / JPG</p>
                    </div>
                  )}

                  {/* Floating Brand Logo over the drop zone */}
                  {!previewUrl && (
                    <motion.div
                      className="absolute bottom-8 right-12 pointer-events-none flex items-center justify-center"
                      animate={{ 
                        y: [0, -12, 0],
                        rotate: [0, 4, -4, 0]
                      }}
                      transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
                    >
                      <div className="w-16 h-16 rounded-2xl flex items-center justify-center shadow-none border border-white/10 relative overflow-hidden"
                        style={{ background: "linear-gradient(135deg,#FF3D00,#FF6D00)" }}>
                        <div className="absolute inset-0 bg-white opacity-20" style={{ clipPath: "polygon(0 0, 100% 0, 100% 30%, 0 60%)" }} />
                        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="black" strokeWidth="3" strokeLinecap="round" className="relative z-10">
                          <path d="M12 5v14M5 12h14" />
                        </svg>
                      </div>
                    </motion.div>
                  )}
                </motion.div>

                {/* Pipeline button — clean white pill with smooth hover */}
                <button
                  onClick={handleGenerate} disabled={!file||loading}
                  className="relative overflow-hidden w-full flex items-center justify-center gap-3 py-4 rounded-full font-semibold text-[13px] tracking-wide transition-all duration-300 disabled:opacity-20 disabled:cursor-not-allowed group"
                  style={{ background:"white", color:"black" }}>
                  <div className="absolute inset-0 bg-gray-200 translate-y-full group-hover:translate-y-0 transition-transform duration-300 ease-out" />
                  <span className="relative z-10 w-6 h-4 rounded-full flex-shrink-0 transition-transform duration-300 group-hover:rotate-12" style={{ background:"linear-gradient(135deg,#FF3D00,#FF6D00)" }} />
                  <span className="relative z-10">Run Multi-Agent Pipeline</span>
                  <ArrowRight className="relative z-10 w-4 h-4 opacity-40 group-hover:translate-x-1 group-hover:opacity-100 transition-all duration-300" />
                </button>
              </motion.div>
            )}
          </AnimatePresence>

          {error && (
            <motion.div initial={{ opacity:0 }} animate={{ opacity:1 }} className="mt-4 p-4 rounded-xl" style={{ background:"rgba(239,68,68,0.05)", border:"1px solid rgba(239,68,68,0.15)" }}>
              <p className="text-xs tracking-widest uppercase text-red-400">{error}</p>
            </motion.div>
          )}
        </div>
      </section>

      {/* ══ BENTO FEATURES ══ */}
      <section className="w-full max-w-[1500px] mx-auto px-8 lg:px-14 py-28">
        <motion.div initial={{ opacity:0, y:40 }} whileInView={{ opacity:1, y:0 }} viewport={{ once:true }} transition={{ duration:0.8 }} className="mb-14">
          <span className="accent-pill mb-5 inline-flex">Core Architecture</span>
          <h2 style={{ fontFamily:"var(--font-display)", fontSize:"clamp(2.5rem,5vw,5rem)", fontWeight:700, color:"white", letterSpacing:"-0.04em", lineHeight:0.88 }}>
            Built on How<br /><span style={{ opacity:0.2 }}>Radiologists Think</span>
          </h2>
        </motion.div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[["2","Retrieval","Retrieval-Augmented Context","3,955 radiologist reports searched before generating a single word."],
            ["1","Verification","NLI Fact-Checking","A separate agent re-reads every claim looking for contradictions."],
            ["1","Grounding","RadLex Ontology","68,000 standardized concepts. ICD-10 codes mapped automatically."],
            ["2","Uncertainty","Monte Carlo Dropout","Same X-ray analyzed 10 times. If they disagree — the system says so."],
          ].map(([span,pill,title,body],i) => (
            <motion.div key={title} initial={{ opacity:0, y:25 }} whileInView={{ opacity:1, y:0 }} viewport={{ once:true }} transition={{ duration:0.5, delay:i*0.08 }}
              className={`${span==="2"?"md:col-span-2":""}`}>
              <TiltCard className="h-[320px]">
                <div>
                  <span className="accent-pill text-[8px] mb-4 inline-flex">{pill}</span>
                  <h3 className="text-xl font-semibold text-white mb-2">{title}</h3>
                  <p className="text-sm text-white/35 leading-relaxed">{body}</p>
                </div>
              </TiltCard>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ══ STATS ══ */}
      <section className="w-full py-24">
        <div className="max-w-[1500px] mx-auto px-8 lg:px-14">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-10 md:gap-16">
            {[["94%","RadLex Match"],["3,955","Indexed Reports"],["+11%","ROUGE-L Gain"],["R2","Self-Refinement"]].map(([n,l],i)=>(
              <motion.div key={l} initial={{ opacity:0, y:20 }} whileInView={{ opacity:1, y:0 }} viewport={{ once:true }} transition={{ duration:0.5, delay:i*0.08 }} className="text-center">
                <p style={{ fontFamily:"var(--font-display)", fontSize:"clamp(2.2rem,5vw,3.5rem)", fontWeight:700, color:"white", letterSpacing:"-0.04em", lineHeight:1 }}>{n}</p>
                <p className="text-[10px] uppercase tracking-[0.2em] text-white/30 mt-2">{l}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ══ FAQ ══ */}
      <section className="w-full py-24">
        <div className="max-w-[1000px] mx-auto px-8 lg:px-14">
          <h2 style={{ fontFamily:"var(--font-display)", fontSize:"clamp(2rem,4vw,3.5rem)", fontWeight:700, color:"white", letterSpacing:"-0.04em", lineHeight:0.9 }} className="mb-14">
            What You Should<br /><span style={{ opacity:0.25 }}>Ask Before Trusting</span><br /><span style={{ opacity:0.1 }}>Any Medical AI</span>
          </h2>
          {[["Why ten model passes instead of one?","One pass gives the model's best guess. Ten passes give a distribution. The entropy of that distribution is your uncertainty score."],
            ["How is this different from prompting GPT-4?","A single prompt call gives no retrieval context, no self-critique, no uncertainty measure. XR 11 runs five distinct agents in sequence."],
            ["What happens when uncertain about severity?","The system surfaces the full vote distribution. Entropy rises, the needs_human_review flag triggers, and the report is marked for confirmation."],
            ["What datasets power the retrieval?","Indiana University Chest X-ray dataset — 3,955 reports by clinical radiologists paired with 7,470 chest X-rays. No synthetic data."],
          ].map(([q,a],i)=>(
            <motion.div key={i} initial={{ opacity:0, y:12 }} whileInView={{ opacity:1, y:0 }} viewport={{ once:true }} transition={{ duration:0.4, delay:i*0.06 }}
              className="group border-b py-5 cursor-pointer" style={{ borderColor:"rgba(255,255,255,0.05)" }}>
              <div className="flex justify-between items-center gap-4">
                <div className="flex items-center gap-3">
                  <span className="accent-dot flex-shrink-0" />
                  <h4 className="text-base text-white/70 group-hover:text-white transition-colors font-light">{q}</h4>
                </div>
                <span className="text-white/20 text-xl group-hover:text-[#FF6D00] transition-colors flex-shrink-0">+</span>
              </div>
              <p className="hidden group-hover:block text-sm text-white/35 mt-3 pl-5 leading-relaxed max-w-2xl">{a}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ══ BIG SAAS FOOTER ══ */}
      <footer className="relative w-full overflow-hidden bg-black pt-28 pb-10" style={{ borderTop: "1px solid rgba(255,255,255,0.05)" }}>
        <div className="relative z-10 max-w-[1500px] mx-auto px-8 lg:px-14 flex flex-col">
          
          <div className="flex flex-col lg:flex-row justify-between items-start lg:items-end gap-12 mb-28">
            <div>
              <p style={{ fontFamily:"var(--font-display)", fontSize:"clamp(3rem,8vw,8rem)", fontWeight:700, color:"white", letterSpacing:"-0.04em", lineHeight:0.85 }}>
                READY TO<br/>
                <span className="text-white/30">REDEFINE</span>
              </p>
            </div>
            <div className="flex flex-col gap-6 items-start lg:items-end text-left lg:text-right">
              <p className="text-sm text-white/40 max-w-sm leading-relaxed font-light">
                Experience clinical-grade chest X-ray analysis powered by a distributed multi-agent intelligence pipeline.
              </p>
              <button onClick={() => { window.scrollTo({ top: 0, behavior: 'smooth' }); setTimeout(openPicker, 600); }} 
                className="group relative overflow-hidden px-7 py-3.5 rounded-full bg-white text-black font-semibold text-[11px] uppercase tracking-[0.2em] transition-all">
                <span className="relative z-10 flex items-center gap-3">
                  <span className="w-2 h-2 rounded-full" style={{ background:"linear-gradient(135deg,#FF3D00,#FF6D00)" }} />
                  Start Analysis
                </span>
                <div className="absolute inset-0 bg-[#e5e5e5] translate-y-full group-hover:translate-y-0 transition-transform duration-300 ease-out" />
              </button>
            </div>
          </div>

          <div className="flex flex-col md:flex-row justify-between items-center gap-6 pt-8" style={{ borderTop: "1px solid rgba(255,255,255,0.1)" }}>
            <div className="flex items-center gap-3">
               <span className="w-5 h-5 rounded-md flex items-center justify-center flex-shrink-0"
                 style={{ background: "linear-gradient(135deg,#FF3D00,#FF6D00)" }}>
                 <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="black" strokeWidth="3" strokeLinecap="round">
                   <path d="M12 5v14M5 12h14" />
                 </svg>
               </span>
               <span style={{ fontFamily:"var(--font-display)" }} className="text-sm font-bold tracking-[0.3em] uppercase text-white">XR 11</span>
            </div>
            <div className="text-[9px] font-mono uppercase tracking-[0.2em] text-white/30 flex flex-wrap gap-4 md:gap-8 justify-center">
               <span>Built by Souvik Rahut</span>
               <span className="hidden md:inline">·</span>
               <span>2025 BTech IT</span>
               <span className="hidden md:inline">·</span>
               <span>All rights reserved</span>
            </div>
          </div>
        </div>
        
        {/* Massive Watermark */}
        <div className="absolute bottom-[-15%] left-0 right-0 pointer-events-none select-none flex justify-center w-full">
           <p style={{ fontFamily:"var(--font-display)", fontSize:"24vw", fontWeight:700, color:"rgba(255,255,255,0.015)", letterSpacing:"-0.04em", lineHeight:0.75, whiteSpace:"nowrap" }}>
             RADIOLOGY
           </p>
        </div>
      </footer>
    </motion.div>
  );
}
