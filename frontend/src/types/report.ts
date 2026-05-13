/** Severity level returned with the structured report. */
export type ReportSeverity = "NORMAL" | "MILD" | "MODERATE" | "CRITICAL";

/** Structured fields shown to the user after generation. */
export interface FinalReport {
  findings: string;
  impression: string;
  severity: ReportSeverity;
  follow_up: string;
  deviations: string;
}

/**
 * Vote counts per severity label from the uncertainty head.
 * Keys are typically severity strings; exact keys depend on the backend.
 */
export type SeverityVotes = Record<string, number>;

export interface Uncertainty {
  severity_votes: SeverityVotes;
  majority_severity: string;
  entropy: number;
  confidence: number;
  semantic_variance: number;
  needs_human_review: boolean;
}

/** Alias for consumers that reference uncertainty payload by this name. */
export type UncertaintyData = Uncertainty;

/** NLI consistency check (`verification.nli_results` on the backend). */
export interface NliCheckResult {
  nli_result: "ENTAILS" | "NEUTRAL" | "CONTRADICTS";
  severity_check: "APPROPRIATE" | "TOO_HIGH" | "TOO_LOW";
  contradictions: string;
  consistency_score: number;
}

export interface RadlexMatchEntry {
  term: string;
  found: boolean;
  radlex_id: string | null;
  standard_label: string;
}

export interface Icd10CodeEntry {
  finding: string;
  icd10_code: string;
  description: string;
}

/** RadLex + ICD-10 grounding (`verification.kg_results`). */
export interface KnowledgeGraphResult {
  terms_found: string[];
  radlex_matches: RadlexMatchEntry[];
  unmatched_terms: string[];
  icd10_codes: Icd10CodeEntry[];
  standardization_rate: number;
}

export type ClaimVerificationStatus =
  | "VERIFIED"
  | "UNCERTAIN"
  | "LIKELY_HALLUCINATED";

export interface ClaimVerification {
  claim: string;
  status: ClaimVerificationStatus;
  reason: string;
}

/** Image-grounded hallucination check (`verification.hallucination_results`). */
export interface HallucinationResult {
  claim_verifications: ClaimVerification[];
  overall_risk: "LOW" | "MEDIUM" | "HIGH";
  hallucination_score: number;
  uncertainty_score: number;
  safe_to_use: boolean;
}

/** One RAG neighbor case returned from retrieval (top-k similar reports). */
export interface RetrievedCase {
  id: string;
  gold_findings: string;
  gold_impression: string;
  similarity_score: number;
}

/** Payload nested under `data` on a successful generate-report response. */
export interface GenerateReportData {
  final_report: FinalReport;
  round1_raw: string;
  round2_raw: string;
  retrieved_cases: RetrievedCase[];
  uncertainty: UncertaintyData;
  rag_context_used: string;
  nli_check: NliCheckResult;
  knowledge_graph: KnowledgeGraphResult;
  hallucination: HallucinationResult;
  pathology?: {
    findings: Record<string, { present: boolean; confidence: number }>;
    positive_findings: string[];
    overall_abnormality_score: number;
  };
  concepts?: Array<{
    finding_id: string;
    raw_label: string;
    clinical_term: string;
    confidence: number;
    severity: string;
    icd10_hint: string;
  }>;
  agents?: {
    anatomy?: Record<string, unknown>;
    disease?: Record<string, unknown>;
    consistency?: Record<string, unknown>;
    synthesis?: Record<string, unknown>;
  };
  metadata?: {
    api_calls_used: number;
    generation_method: string;
    pipeline_version: string;
  };
}

/** Top-level successful response from POST /api/generate-report. */
export interface GenerateReportSuccessResponse {
  status: "success";
  data: GenerateReportData;
}
