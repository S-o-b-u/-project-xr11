"""
hallucination_detector.py
─────────────────────────
Sends the generated report text + the original chest X-ray image back to
Gemini and asks it to verify each factual claim in the report against what
is actually visible in the image.

This is a "self-consistency" check: the same multimodal model is used as
both the generator and the verifier, which means it can catch obvious
hallucinations (facts not present in the image) while still benefiting from
its domain knowledge.
"""

import logging
import re
from typing import Any

from src.model.prompt_builder import build_hallucination_prompt

log = logging.getLogger(__name__)

# ── Regex patterns ────────────────────────────────────────────────────────────
# Matches lines like:
#   - CLAIM: heart is enlarged | STATUS: VERIFIED | REASON: visible cardiomegaly
_CLAIM_LINE_RE = re.compile(
    r"-\s*CLAIM:\s*(.+?)\s*\|\s*STATUS:\s*(VERIFIED|UNCERTAIN|LIKELY_HALLUCINATED)\s*\|\s*REASON:\s*(.+)",
    re.IGNORECASE,
)
_OVERALL_RISK_RE = re.compile(
    r"OVERALL_HALLUCINATION_RISK:\s*(LOW|MEDIUM|HIGH)",
    re.IGNORECASE,
)


class HallucinationDetector:
    """Verifies generated report claims against the source chest X-ray image."""

    def __init__(self, vlm_client) -> None:
        """
        Parameters
        ----------
        vlm_client : VLMClient
            Gemini API wrapper; uses generate() (image + text).
        """
        self._client = vlm_client

    def detect(self, image_path: str, generated_report: dict) -> dict[str, Any]:
        """Check each claim in *generated_report* against the X-ray image.

        Parameters
        ----------
        image_path : str
            Path to the chest X-ray PNG.
        generated_report : dict
            Parsed report dict with at least 'findings', 'impression',
            'severity', 'follow_up'.

        Returns
        -------
        dict
            Keys:
            - claim_verifications  : list of {claim, status, reason}
            - overall_risk         : "LOW" | "MEDIUM" | "HIGH"
            - hallucination_score  : float  (fraction of LIKELY_HALLUCINATED)
            - uncertainty_score    : float  (fraction of UNCERTAIN)
            - safe_to_use          : bool   (True if hallucination_score < 0.2)
        """
        defaults: dict[str, Any] = {
            "claim_verifications": [],
            "overall_risk":        "MEDIUM",
            "hallucination_score": 0.5,
            "uncertainty_score":   0.5,
            "safe_to_use":         False,
        }

        try:
            report_text = self._format_report(generated_report)
            prompt      = build_hallucination_prompt(report_text)
            response    = self._client.generate(prompt, image_path, temperature=0.1)
            return self._parse(response, defaults)
        except Exception as exc:
            log.error("[HallucinationDetector] detect() failed: %s", exc, exc_info=True)
            return defaults

    # ── Private ───────────────────────────────────────────────────────────────

    @staticmethod
    def _format_report(report: dict) -> str:
        """Flatten the structured report dict into a readable string for the prompt."""
        parts = []
        for key in ("findings", "impression", "severity", "follow_up", "deviations"):
            value = report.get(key, "")
            if value:
                parts.append(f"{key.upper().replace('_', ' ')}: {value}")
        return "\n".join(parts)

    def _parse(self, text: str, defaults: dict) -> dict[str, Any]:
        result = dict(defaults)

        # ── Parse claim lines ─────────────────────────────────────────────────
        claims: list[dict] = []
        for match in _CLAIM_LINE_RE.finditer(text):
            claims.append({
                "claim":  match.group(1).strip(),
                "status": match.group(2).strip().upper(),
                "reason": match.group(3).strip(),
            })

        result["claim_verifications"] = claims

        # ── Compute scores ────────────────────────────────────────────────────
        total = len(claims)
        if total > 0:
            n_hallucinated = sum(1 for c in claims if c["status"] == "LIKELY_HALLUCINATED")
            n_uncertain    = sum(1 for c in claims if c["status"] == "UNCERTAIN")
            result["hallucination_score"] = round(n_hallucinated / total, 3)
            result["uncertainty_score"]   = round(n_uncertain    / total, 3)

        # ── Overall risk ──────────────────────────────────────────────────────
        m = _OVERALL_RISK_RE.search(text)
        if m:
            result["overall_risk"] = m.group(1).upper()

        # ── Safety flag ───────────────────────────────────────────────────────
        result["safe_to_use"] = result["hallucination_score"] < 0.2

        return result
