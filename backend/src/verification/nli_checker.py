"""
nli_checker.py
──────────────
Uses Gemini (text-only) to check whether the findings, impression,
and severity of a generated report are logically consistent with each
other (Natural Language Inference style).
"""

import logging
import re

from src.model.prompt_builder import build_nli_prompt

log = logging.getLogger(__name__)

# Regex patterns for parsing Gemini's structured NLI response
_NLI_RESULT_RE    = re.compile(r"NLI_RESULT:\s*(ENTAILS|NEUTRAL|CONTRADICTS)", re.IGNORECASE)
_SEV_CHECK_RE     = re.compile(r"SEVERITY_CHECK:\s*(APPROPRIATE|TOO_HIGH|TOO_LOW)", re.IGNORECASE)
_CONTRADICTIONS_RE = re.compile(r"CONTRADICTIONS:\s*(.*?)(?:\n[A-Z_]+:|$)", re.IGNORECASE | re.DOTALL)
_SCORE_RE         = re.compile(r"CONSISTENCY_SCORE:\s*([0-9]*\.?[0-9]+)")


class NLIChecker:
    """Verifies the internal logical consistency of a generated radiology report."""

    def __init__(self, vlm_client) -> None:
        """
        Parameters
        ----------
        vlm_client : VLMClient
            Our Gemini API wrapper; uses generate_no_image for text-only calls.
        """
        self._client = vlm_client

    def check(self, findings: str, impression: str, severity: str) -> dict:
        """Check consistency between findings, impression, and severity.

        Parameters
        ----------
        findings : str
            The FINDINGS section of the generated report.
        impression : str
            The IMPRESSION section of the generated report.
        severity : str
            The SEVERITY label (NORMAL / MILD / MODERATE / CRITICAL).

        Returns
        -------
        dict
            Keys:
            - nli_result        : "ENTAILS" | "NEUTRAL" | "CONTRADICTS"
            - severity_check    : "APPROPRIATE" | "TOO_HIGH" | "TOO_LOW"
            - contradictions    : str (details or "None")
            - consistency_score : float [0.0, 1.0]
        """
        # Safe defaults (used if parsing fails)
        defaults = {
            "nli_result":        "NEUTRAL",
            "severity_check":    "APPROPRIATE",
            "contradictions":    "Could not verify (parse error)",
            "consistency_score": 0.5,
        }

        try:
            prompt   = build_nli_prompt(findings, impression, severity)
            response = self._client.generate_no_image(prompt, temperature=0.1)
            return self._parse(response, defaults)
        except Exception as exc:
            log.error("[NLIChecker] check() failed: %s", exc, exc_info=True)
            return defaults

    # ── Private ───────────────────────────────────────────────────────────────

    def _parse(self, text: str, defaults: dict) -> dict:
        result = dict(defaults)

        m = _NLI_RESULT_RE.search(text)
        if m:
            result["nli_result"] = m.group(1).upper()

        m = _SEV_CHECK_RE.search(text)
        if m:
            result["severity_check"] = m.group(1).upper()

        m = _CONTRADICTIONS_RE.search(text)
        if m:
            result["contradictions"] = m.group(1).strip()

        m = _SCORE_RE.search(text)
        if m:
            try:
                score = float(m.group(1))
                result["consistency_score"] = round(max(0.0, min(1.0, score)), 3)
            except ValueError:
                pass

        return result
