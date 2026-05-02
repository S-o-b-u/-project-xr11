"""
report_generator.py
────────────────────
Orchestrates the full Multimodal Medical Report Generation pipeline:

  Step 1 — RAG Retrieval        (few-shot grounding from similar cases)
  Step 2 — Uncertainty Sampling (Monte-Carlo severity + semantic variance)
  Step 3 — Round 1 Generation   (RAG-grounded initial report)
  Step 4 — Round 2 Refinement   (lower-temperature verification pass)
  Step 5 — Assemble core result dict
  Step 6 — Verification         (NLI check, KG grounding, Hallucination detection)

Each step is wrapped in its own try/except so a failure in one step
never crashes the pipeline — it falls back to a safe default and logs
the error.
"""

import logging
import os
import re
from typing import Any, Dict

from .vlm_client import VLMClient
from .prompt_builder import build_round1_prompt, build_round2_prompt
from src.rag.embedder import ReportEmbedder
from src.rag.vector_store import VectorStore
from src.rag.retriever import RAGRetriever
from src.uncertainty.sampler import UncertaintySampler
from src.verification.nli_checker import NLIChecker
from src.verification.knowledge_graph import KnowledgeGraphGrounder
from src.verification.hallucination_detector import HallucinationDetector

log = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)

# ── Paths to pre-built FAISS artefacts ───────────────────────────────────────
_BASE_DIR     = os.path.dirname(os.path.dirname(os.path.dirname(
                    os.path.dirname(os.path.abspath(__file__)))))  # backend/
_INDEX_PATH   = os.path.join(_BASE_DIR, "data", "processed", "faiss_index.bin")
_META_PATH    = os.path.join(_BASE_DIR, "data", "processed", "faiss_metadata.pkl")

# ── Regex patterns for structured output parsing ──────────────────────────────
_SECTION_PATTERNS: Dict[str, re.Pattern] = {
    "findings":   re.compile(
        r"FINDINGS:\s*(.*?)(?:\n(?:IMPRESSION|SEVERITY|FOLLOW_UP|DEVIATIONS):|$)",
        re.IGNORECASE | re.DOTALL),
    "impression": re.compile(
        r"IMPRESSION:\s*(.*?)(?:\n(?:FINDINGS|SEVERITY|FOLLOW_UP|DEVIATIONS):|$)",
        re.IGNORECASE | re.DOTALL),
    "severity":   re.compile(
        r"SEVERITY:\s*(.*?)(?:\n(?:FINDINGS|IMPRESSION|FOLLOW_UP|DEVIATIONS):|$)",
        re.IGNORECASE | re.DOTALL),
    "follow_up":  re.compile(
        r"FOLLOW_UP:\s*(.*?)(?:\n(?:FINDINGS|IMPRESSION|SEVERITY|DEVIATIONS):|$)",
        re.IGNORECASE | re.DOTALL),
    "deviations": re.compile(
        r"DEVIATIONS:\s*(.*?)(?:\n(?:FINDINGS|IMPRESSION|SEVERITY|FOLLOW_UP):|$)",
        re.IGNORECASE | re.DOTALL),
}
_SEVERITY_CANONICAL = {"NORMAL", "MILD", "MODERATE", "CRITICAL"}


class ReportGenerator:
    """Full pipeline orchestrator for AI-powered radiology report generation."""

    def __init__(self) -> None:
        log.info("Initialising ReportGenerator …")

        # ── Core VLM client ───────────────────────────────────────────────────
        self.vlm_client = VLMClient()

        # ── Embedding model (shared by RAG and Uncertainty) ───────────────────
        self.embedder = ReportEmbedder()

        # ── FAISS vector store + retriever ────────────────────────────────────
        self.vector_store = VectorStore(dimension=ReportEmbedder.DIM)
        if os.path.isfile(_INDEX_PATH) and os.path.isfile(_META_PATH):
            self.vector_store.load(_INDEX_PATH, _META_PATH)
            log.info("FAISS index loaded (%d vectors).", self.vector_store._index.ntotal)
        else:
            log.warning(
                "FAISS index not found at %s — RAG retrieval will be skipped. "
                "Run scripts/build_index.py first.", _INDEX_PATH
            )

        self.retriever = RAGRetriever(self.vector_store, self.embedder)

        # ── Uncertainty sampler (5 samples to respect free-tier limits) ───────
        self.sampler = UncertaintySampler(
            self.vlm_client,
            n_samples=5,
            temperature=0.7,
        )

        # ── Verification components ───────────────────────────────────────────
        self.nli_checker  = NLIChecker(self.vlm_client)
        self.kg_grounder  = KnowledgeGraphGrounder(
            radlex_path=os.path.join(_BASE_DIR, "data", "raw", "radlex.owl")
        )
        self.hallucination_detector = HallucinationDetector(self.vlm_client)

        log.info("ReportGenerator ready.")

    # ── Structured output parser ─────────────────────────────────────────────

    def parse_structured_output(self, raw_text: str) -> Dict[str, str]:
        """Extract all structured sections from a raw VLM response.

        Handles missing sections gracefully — returns an empty string for any
        section that isn't found, and normalises the SEVERITY to one of the
        four canonical values (or 'UNKNOWN').

        Parameters
        ----------
        raw_text : str
            Raw text response from the VLM.

        Returns
        -------
        dict
            Keys: findings, impression, severity, follow_up, deviations
        """
        result: Dict[str, str] = {
            "findings":   "",
            "impression": "",
            "severity":   "UNKNOWN",
            "follow_up":  "",
            "deviations": "",
        }

        for field, pattern in _SECTION_PATTERNS.items():
            match = pattern.search(raw_text)
            if match:
                result[field] = match.group(1).strip()

        # Normalise severity to canonical label
        sev = result["severity"].upper()
        for label in _SEVERITY_CANONICAL:
            if label in sev:
                result["severity"] = label
                break
        else:
            if result["severity"] not in _SEVERITY_CANONICAL:
                result["severity"] = "UNKNOWN"

        return result

    # ── Main pipeline ─────────────────────────────────────────────────────────

    def generate_report(self, image_path: str) -> Dict[str, Any]:
        """Run the full 6-step report generation + verification pipeline.

        Parameters
        ----------
        image_path : str
            Absolute path to the chest X-ray PNG image.

        Returns
        -------
        dict
            {final_report, round1_raw, round2_raw, retrieved_cases,
             uncertainty, rag_context_used,
             verification: {nli_results, kg_results, hallucination_results}}
        """
        log.info("=== Starting report generation for: %s ===", image_path)

        # ── Defaults (used if a step fails) ──────────────────────────────────
        rag_context      = ""
        retrieved_cases  = []
        uncertainty      = {}
        round1_raw       = ""
        round2_raw       = ""
        final_report     = self.parse_structured_output("")

        # ─────────────────────────────────────────────────────────────────────
        # STEP 1 — RAG Retrieval
        # ─────────────────────────────────────────────────────────────────────
        log.info("Step 1: RAG retrieval …")
        try:
            query_text = f"chest x-ray analysis {os.path.basename(image_path)}"
            raw_cases = self.retriever.retrieve(query_text, k=3)
            rag_context = self.retriever.format_context(raw_cases)

            # Slim down to only the fields the frontend needs
            retrieved_cases = [
                {
                    "id":               c.get("id", ""),
                    "gold_findings":    c.get("gold_findings", ""),
                    "gold_impression":  c.get("gold_impression", ""),
                    "similarity_score": c.get("similarity_score", 0.0),
                }
                for c in raw_cases
            ]
            log.info("Retrieved %d similar cases.", len(retrieved_cases))
        except Exception as exc:
            log.error("Step 1 (RAG) failed: %s", exc, exc_info=True)

        # ─────────────────────────────────────────────────────────────────────
        # STEP 2 — Uncertainty Quantification
        # ─────────────────────────────────────────────────────────────────────
        log.info("Step 2: Uncertainty quantification …")
        try:
            uncertainty_prompt = build_round1_prompt(rag_context=rag_context)
            uncertainty = self.sampler.full_uncertainty_analysis(
                uncertainty_prompt, image_path, self.embedder
            )
            log.info(
                "Uncertainty — entropy: %.3f, confidence: %.3f, needs_review: %s",
                uncertainty.get("entropy", -1),
                uncertainty.get("confidence", -1),
                uncertainty.get("needs_human_review", "?"),
            )
        except Exception as exc:
            log.error("Step 2 (Uncertainty) failed: %s", exc, exc_info=True)

        # ─────────────────────────────────────────────────────────────────────
        # STEP 3 — Round 1 Generation (RAG-grounded, deterministic)
        # ─────────────────────────────────────────────────────────────────────
        log.info("Step 3: Round 1 generation …")
        try:
            round1_prompt = build_round1_prompt(rag_context=rag_context)
            round1_raw = self.vlm_client.generate(
                round1_prompt, image_path, temperature=0.3
            )
            log.info("Round 1 complete (%d chars).", len(round1_raw))
        except Exception as exc:
            log.error("Step 3 (Round 1) failed: %s", exc, exc_info=True)

        # ─────────────────────────────────────────────────────────────────────
        # STEP 4 — Round 2 Refinement (lower temperature for precision)
        # ─────────────────────────────────────────────────────────────────────
        log.info("Step 4: Round 2 refinement …")
        try:
            if round1_raw:
                round2_prompt = build_round2_prompt(round1_raw)
                round2_raw = self.vlm_client.generate(
                    round2_prompt, image_path, temperature=0.2
                )
                final_report = self.parse_structured_output(round2_raw)
                log.info("Round 2 complete (%d chars).", len(round2_raw))
            else:
                log.warning("Skipping Round 2 — Round 1 produced no output.")
        except Exception as exc:
            log.error("Step 4 (Round 2) failed: %s", exc, exc_info=True)
            # Fall back to parsing whatever Round 1 gave us
            if round1_raw:
                final_report = self.parse_structured_output(round1_raw)

        # ─────────────────────────────────────────────────────────────────────
        # STEP 5 — Assemble core result
        # ─────────────────────────────────────────────────────────────────────
        log.info("Step 5: Assembling core result …")
        result: Dict[str, Any] = {
            "final_report":     final_report,
            "round1_raw":       round1_raw,
            "round2_raw":       round2_raw,
            "retrieved_cases":  retrieved_cases,
            "uncertainty":      uncertainty,
            "rag_context_used": rag_context,
        }

        # ─────────────────────────────────────────────────────────────────────
        # STEP 6 — Verification
        # ─────────────────────────────────────────────────────────────────────
        log.info("Step 6: Verification (NLI + KG + Hallucination) …")
        nli_results          = {}
        kg_results           = {}
        hallucination_results = {}

        findings   = final_report.get("findings",   "")
        impression = final_report.get("impression", "")
        severity   = final_report.get("severity",   "UNKNOWN")

        try:
            nli_results = self.nli_checker.check(findings, impression, severity)
            log.info("NLI: %s (score=%.2f)",
                     nli_results.get("nli_result", "?"),
                     nli_results.get("consistency_score", -1))
        except Exception as exc:
            log.error("Step 6a (NLI) failed: %s", exc, exc_info=True)

        try:
            kg_results = self.kg_grounder.ground_report(findings, impression)
            log.info("KG: standardization_rate=%.2f",
                     kg_results.get("standardization_rate", -1))
        except Exception as exc:
            log.error("Step 6b (KG) failed: %s", exc, exc_info=True)

        try:
            hallucination_results = self.hallucination_detector.detect(
                image_path, final_report
            )
            log.info("Hallucination: score=%.2f, safe=%s",
                     hallucination_results.get("hallucination_score", -1),
                     hallucination_results.get("safe_to_use", "?"))
        except Exception as exc:
            log.error("Step 6c (Hallucination) failed: %s", exc, exc_info=True)

        result["verification"] = {
            "nli_results":           nli_results,
            "kg_results":            kg_results,
            "hallucination_results": hallucination_results,
        }

        log.info("=== Report generation complete. ===")
        return result
