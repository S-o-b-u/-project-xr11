"use client";

import { useEffect, useState } from "react";
import axios from "axios";
import { motion } from "framer-motion";

interface StatsData {
  dataset_size: number;
  index_size: number;
}

export default function SystemPage() {
  const [stats, setStats] = useState<StatsData | null>(null);
  const [health, setHealth] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [statsRes, healthRes] = await Promise.all([
          axios.get("http://127.0.0.1:8000/api/stats"),
          axios.get("http://127.0.0.1:8000/health"),
        ]);
        setStats(statsRes.data);
        setHealth(healthRes.data.status);
      } catch (e) {
        console.error("Failed to fetch system data", e);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { 
      opacity: 1,
      transition: { staggerChildren: 0.1, delayChildren: 0.2 }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.8, ease: [0.16, 1, 0.3, 1] } }
  };

  return (
    <div className="flex-1 max-w-[1600px] w-full mx-auto px-10 pb-32 flex flex-col justify-center min-h-[70vh]">
      <motion.div 
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 md:grid-cols-2 gap-24"
      >
        <motion.div variants={itemVariants} className="space-y-6">
          <h1 
            style={{ fontFamily: "var(--font-display)" }}
            className="text-[clamp(3rem,6vw,5.5rem)] font-bold uppercase leading-[0.85] tracking-tighter text-white"
          >
            System<br />Status
          </h1>
          <p className="text-sm tracking-wide text-white/40 max-w-md leading-relaxed font-light">
            Live diagnostic metrics from the FastAPI backend. Monitoring FAISS vector index and dataset integrity.
          </p>
        </motion.div>

        <motion.div variants={itemVariants} className="flex flex-col justify-center space-y-16">
          {loading ? (
            <div className="animate-pulse space-y-4">
              <div className="h-4 w-32 bg-white/10 rounded"></div>
              <div className="h-12 w-48 bg-white/10 rounded"></div>
            </div>
          ) : (
            <>
              <div className="space-y-4">
                <h3 className="section-label">API Health</h3>
                <div className="flex items-center gap-4">
                  <span className={`inline-flex items-center gap-2 px-3 py-1 text-[10px] font-mono uppercase tracking-widest border rounded-full
                    ${health === "ok" ? "text-emerald-400 border-emerald-400/30" : "text-rose-400 border-rose-400/30"}`}>
                    <span className="w-1.5 h-1.5 rounded-full bg-current" />
                    {health === "ok" ? "ONLINE" : "OFFLINE"}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-8 border-t border-white/5 pt-8">
                <div className="space-y-2">
                  <h3 className="section-label">FAISS Index Size</h3>
                  <div className="flex items-baseline gap-2">
                    <span className="text-4xl font-light text-white">
                      {stats?.index_size ?? "—"}
                    </span>
                    <span className="text-xs text-white/40 font-mono">VECTORS</span>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <h3 className="section-label">Dataset Size</h3>
                  <div className="flex items-baseline gap-2">
                    <span className="text-4xl font-light text-white">
                      {stats?.dataset_size ?? "—"}
                    </span>
                    <span className="text-xs text-white/40 font-mono">RECORDS</span>
                  </div>
                </div>
              </div>
            </>
          )}
        </motion.div>
      </motion.div>
    </div>
  );
}
