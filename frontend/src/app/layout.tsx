
import type { Metadata } from "next";
import { Geist_Mono, Syncopate, Outfit } from "next/font/google";
import Link from "next/link";
import SmoothScroll from "@/components/SmoothScroll";
import "./globals.css";

const outfit = Outfit({ variable: "--font-body", subsets: ["latin"] });
const geistMono = Geist_Mono({ variable: "--font-geist-mono", subsets: ["latin"] });
const syncopate = Syncopate({ variable: "--font-display", subsets: ["latin"], weight: ["400", "700"] });

export const metadata: Metadata = {
  title: "The XR 11 — Multimodal AI Radiology",
  description: "Multimodal AI pipeline for automated radiology report generation with uncertainty quantification and verification.",
  applicationName: "The XR 11",
  robots: { index: false, follow: false },
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className={`${outfit.variable} ${geistMono.variable} ${syncopate.variable} h-full antialiased`}>
      <body className="flex min-h-full flex-col bg-black">

        {/* ── Navigation ── */}
        <header className="fixed top-0 left-0 right-0 z-50 pointer-events-none" style={{ height: 64 }}>
          <div className="w-full max-w-[1500px] mx-auto px-8 lg:px-14 h-full flex items-center justify-between">

            {/* Brand */}
            <div className="flex items-center gap-2.5 pointer-events-auto">
              <div className="w-6 h-6 rounded-md flex items-center justify-center flex-shrink-0"
                style={{ background: "linear-gradient(135deg,#FF3D00,#FF6D00)" }}>
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="black" strokeWidth="3" strokeLinecap="round">
                  <path d="M12 5v14M5 12h14" />
                </svg>
              </div>
              <Link href="/">
                <span style={{ fontFamily: "var(--font-display)" }}
                  className="text-[12px] font-bold tracking-[0.3em] uppercase text-white hover:opacity-60 transition-opacity drop-shadow-[0_1px_3px_rgba(0,0,0,0.4)]">
                  XR 11
                </span>
              </Link>
            </div>

            {/* Center nav — dark frosted pill, always legible */}
            <nav className="hidden md:flex items-center gap-1 pointer-events-auto px-2 py-1.5 rounded-full"
              style={{ 
                background: "rgba(20, 20, 20, 0.55)", 
                backdropFilter: "blur(24px) saturate(180%)", 
                border: "1px solid rgba(255, 255, 255, 0.08)",
                boxShadow: "0 8px 32px rgba(0, 0, 0, 0.2), inset 0 1px 1px rgba(255, 255, 255, 0.06)"
              }}>
              {["Home", "Upload", "System", "Docs"].map((label) => (
                <Link key={label} href={label === "Upload" || label === "Home" ? "/" : "#"}
                  className="px-4 py-1.5 rounded-full text-[11px] tracking-[0.12em] uppercase font-bold text-white/70 transition-all duration-300 hover:text-white hover:bg-white/10">
                  {label}
                </Link>
              ))}
            </nav>

            {/* CTA */}
            <div className="pointer-events-auto">
              <Link href="/"
                className="flex items-center gap-2.5 px-5 py-2 rounded-full text-[11px] font-semibold uppercase tracking-[0.12em] transition-all duration-200 text-white"
                style={{ background: "rgba(20, 20, 20, 0.7)", backdropFilter: "blur(12px)", border: "1px solid rgba(255,255,255,0.08)" }}>
                <span className="w-4 h-2.5 rounded-full" style={{ background: "linear-gradient(135deg,#FF3D00,#FF6D00)" }} />
                Analyze
              </Link>
            </div>
          </div>
        </header>

        {/* ── Main content ── */}
        <div className="relative z-10 flex min-h-0 flex-1 flex-col">
          <SmoothScroll>
            {children}
          </SmoothScroll>
        </div>
      </body>
    </html>
  );
}
