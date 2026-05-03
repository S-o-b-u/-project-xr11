"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { RetrievedCases } from "@/components/RetrievedCases";
import { ReportCard } from "@/components/ReportCard";
import { RoundComparison } from "@/components/RoundComparison";
import { SeverityBadge } from "@/components/SeverityBadge";
import { UncertaintyPanel } from "@/components/UncertaintyPanel";
import { VerificationPanel } from "@/components/VerificationPanel";
import type {
  GenerateReportSuccessResponse,
  HallucinationResult,
  KnowledgeGraphResult,
  NliCheckResult,
  UncertaintyData,
} from "@/types/report";

const STORAGE_REPORT = "reportData";
const STORAGE_IMAGE = "imageUrl";

function mergeUncertainty(raw: UncertaintyData | undefined): UncertaintyData {
  const base: UncertaintyData = {
    severity_votes: {},
    majority_severity: "",
    entropy: 0,
    confidence: 0,
    semantic_variance: 0,
    needs_human_review: false,
  };
  if (!raw) return base;
  return {
    ...base,
    ...raw,
    severity_votes: { ...base.severity_votes, ...raw.severity_votes },
  };
}

function mergeNli(raw: NliCheckResult | undefined): NliCheckResult {
  const base: NliCheckResult = {
    nli_result: "NEUTRAL",
    severity_check: "APPROPRIATE",
    contradictions: "",
    consistency_score: 0,
  };
  return raw ? { ...base, ...raw } : base;
}

function mergeKg(raw: KnowledgeGraphResult | undefined): KnowledgeGraphResult {
  const base: KnowledgeGraphResult = {
    terms_found: [],
    radlex_matches: [],
    unmatched_terms: [],
    icd10_codes: [],
    standardization_rate: 0,
  };
  return raw
    ? {
        ...base,
        ...raw,
        terms_found: raw.terms_found ?? base.terms_found,
        radlex_matches: raw.radlex_matches ?? base.radlex_matches,
        unmatched_terms: raw.unmatched_terms ?? base.unmatched_terms,
        icd10_codes: raw.icd10_codes ?? base.icd10_codes,
      }
    : base;
}

function mergeHall(raw: HallucinationResult | undefined): HallucinationResult {
  const base: HallucinationResult = {
    claim_verifications: [],
    overall_risk: "MEDIUM",
    hallucination_score: 0,
    uncertainty_score: 0,
    safe_to_use: false,
  };
  return raw
    ? {
        ...base,
        ...raw,
        claim_verifications:
          raw.claim_verifications ?? base.claim_verifications,
      }
    : base;
}

export default function ReportPage() {
  const router = useRouter();
  const [payload, setPayload] = useState<GenerateReportSuccessResponse | null>(
    null
  );
  const [imageUrl, setImageUrl] = useState<string | null>(null);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    const rawReport = sessionStorage.getItem(STORAGE_REPORT);
    const rawImage = sessionStorage.getItem(STORAGE_IMAGE);

    if (!rawReport) {
      if (rawImage) sessionStorage.removeItem(STORAGE_IMAGE);
      setImageUrl(null);
      return;
    }

    try {
      const parsed = JSON.parse(rawReport) as GenerateReportSuccessResponse;
      if (parsed?.status === "success" && parsed.data?.final_report) {
        setPayload(parsed);
        setImageUrl(rawImage);
      } else {
        sessionStorage.removeItem(STORAGE_REPORT);
        sessionStorage.removeItem(STORAGE_IMAGE);
        setImageUrl(null);
      }
    } catch {
      sessionStorage.removeItem(STORAGE_REPORT);
      sessionStorage.removeItem(STORAGE_IMAGE);
      setImageUrl(null);
    }
  }, []);

  const rawJson = useMemo(() => {
    if (!payload) return "";
    try {
      return JSON.stringify(payload, null, 2);
    } catch {
      return "";
    }
  }, [payload]);

  const analyzeAnother = () => {
    sessionStorage.removeItem(STORAGE_REPORT);
    sessionStorage.removeItem(STORAGE_IMAGE);
    router.push("/");
  };

  if (!mounted) {
    return (
      <div className="flex min-h-full items-center justify-center">
        <p className="text-sm text-zinc-500">Loading…</p>
      </div>
    );
  }

  if (!payload) {
    return (
      <div className="flex min-h-full flex-col items-center justify-center gap-6 px-4 py-16">
        <p className="text-center text-base text-zinc-700 dark:text-zinc-300">
          No report found
        </p>
        <Link
          href="/"
          className="rounded-lg px-5 py-2.5 text-sm font-medium underline underline-offset-4"
        >
          Back to home
        </Link>
      </div>
    );
  }

  const data = payload.data;
  const finalReport = data.final_report;

  return (
    <div className="min-h-full px-4 py-8">
      <div className="mx-auto flex max-w-6xl flex-col gap-10">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <h1 className="text-xl font-semibold tracking-tight lg:text-2xl">
            Final report
          </h1>
          <button
            type="button"
            onClick={analyzeAnother}
            className="rounded-lg px-4 py-2 text-sm font-semibold ring-1 ring-zinc-300 lg:px-5 lg:py-2.5 dark:ring-zinc-600"
          >
            Analyze Another X-Ray
          </button>
        </div>

        <div className="grid grid-cols-1 gap-8 lg:grid-cols-2 lg:gap-10 lg:items-start">
          <div className="flex flex-col gap-3 lg:sticky lg:top-8">
            <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
              Study image
            </p>
            <div className="overflow-hidden rounded-xl ring-1 ring-zinc-200 dark:ring-zinc-800">
              {imageUrl ? (
                <>
                  {/* eslint-disable-next-line @next/next/no-img-element -- data URL from sessionStorage */}
                  <img
                    src={imageUrl}
                    alt="Uploaded chest X-ray"
                    className="mx-auto max-h-[70vh] w-full bg-zinc-100 object-contain dark:bg-zinc-900"
                  />
                </>
              ) : (
                <div className="flex min-h-48 items-center justify-center bg-zinc-100 px-4 py-12 text-center text-sm text-zinc-500 dark:bg-zinc-900 dark:text-zinc-400">
                  No image preview (open from upload flow).
                </div>
              )}
            </div>
          </div>

          <div className="flex flex-col gap-6">
            <div className="flex flex-col gap-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
                Severity
              </p>
              <SeverityBadge severity={finalReport.severity} />
            </div>
            <ReportCard finalReport={finalReport} />
          </div>
        </div>

        <section className="flex flex-col gap-4 border-t border-zinc-200 pt-10 dark:border-zinc-800">
          <h2 className="text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
            Uncertainty
          </h2>
          <UncertaintyPanel uncertainty={mergeUncertainty(data.uncertainty)} />
        </section>

        <section className="flex flex-col gap-4 border-t border-zinc-200 pt-10 dark:border-zinc-800">
          <h2 className="text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
            Verification
          </h2>
          <VerificationPanel
            nli_check={mergeNli(data.nli_check)}
            knowledge_graph={mergeKg(data.knowledge_graph)}
            hallucination={mergeHall(data.hallucination)}
          />
        </section>

        <section className="flex flex-col gap-4 border-t border-zinc-200 pt-10 dark:border-zinc-800">
          <h2 className="text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
            Retrieved cases (RAG)
          </h2>
          <RetrievedCases retrievedCases={data.retrieved_cases ?? []} />
        </section>

        <section className="flex flex-col gap-4 border-t border-zinc-200 pt-10 dark:border-zinc-800">
          <h2 className="text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
            Round 1 vs Round 2
          </h2>
          <RoundComparison
            round1Raw={data.round1_raw}
            round2Raw={data.round2_raw}
          />
        </section>

        <details className="border-t border-zinc-200 pt-10 dark:border-zinc-800">
          <summary className="cursor-pointer text-xs font-semibold uppercase tracking-wide text-zinc-500 dark:text-zinc-400">
            Raw JSON (debug)
          </summary>
          <pre className="mt-4 max-h-[min(70vh,36rem)] overflow-auto rounded-lg bg-zinc-100 p-4 text-xs leading-relaxed dark:bg-zinc-900">
            {rawJson}
          </pre>
        </details>
      </div>
    </div>
  );
}
