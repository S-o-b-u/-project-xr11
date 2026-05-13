"""
Module for reasoning about disease severity.
"""
from typing import Dict, Any, List

class SeverityReasoner:
    """
    Analyzes mapped medical concepts to determine the severity and progression of findings.
    """
    
    # Pathologies that can immediately elevate severity to severe when confirmed
    CRITICAL_PATHOLOGIES = {
        "pneumothorax", "pulmonary edema", "pulmonary mass"
    }
    
    # Pathologies that are generally low severity even if the model fires them
    LOW_SEVERITY_PATHOLOGIES = {
        "hiatal hernia", "pleural thickening", "pulmonary emphysema",
        "pulmonary fibrosis", "atelectasis"
    }
    
    SEVERITY_RECOMMENDATION = {
        "normal":   "No acute findings. Routine follow-up as clinically indicated.",
        "mild":     "Mild finding(s) noted. Outpatient clinical review recommended.",
        "moderate": "Moderate finding(s) identified. Clinical correlation required. Consider repeat imaging.",
        "severe":   "Urgent radiologist review required. Immediate clinical correlation advised."
    }
    
    def reason(self, concepts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Evaluates severity from ONLY confirmed (present=True) concepts.

        Parameters
        ----------
        concepts : list of dict
            Full concept list from ConceptExtractor (positive + negative).

        Returns
        -------
        dict
        """
        # ── GATE: work only with positive, confirmed findings ─────────────────
        positive = [c for c in concepts if c.get("present") is True]
        negative_findings = [c.get("clinical_term", "") for c in concepts if not c.get("present")]
        
        severity_scores = {c.get("finding_id", "?"): c.get("severity", "unknown") for c in concepts}

        if not positive:
            return {
                "overall_severity": "normal",
                "severity_scores": severity_scores,
                "confidence_weighted_severity": 0.0,
                "positive_finding_count": 0,
                "negative_findings_debug": negative_findings,
                "recommendation": self.SEVERITY_RECOMMENDATION["normal"]
            }

        # ── Score only from positive findings ─────────────────────────────────
        confs = [c.get("confidence", 0.0) for c in positive]
        terms = [c.get("clinical_term", "").lower() for c in positive]
        max_confidence = max(confs)
        confidence_weighted = sum(confs) / len(confs)

        # ── Check for critical pathologies (auto-elevate) ──────────────────────
        has_critical = any(t in self.CRITICAL_PATHOLOGIES for t in terms)
        all_low = all(t in self.LOW_SEVERITY_PATHOLOGIES for t in terms)

        # ── Calibrated severity logic ─────────────────────────────────────────
        if has_critical and max_confidence >= 0.75:
            overall_severity = "severe"
        elif all_low and len(positive) == 1:
            # e.g. hernia alone → mild/moderate at most
            overall_severity = "mild" if max_confidence < 0.75 else "moderate"
        elif max_confidence >= 0.75 and len(positive) >= 2:
            overall_severity = "moderate"
        elif max_confidence >= 0.75:
            overall_severity = "moderate"
        elif max_confidence >= 0.5:
            overall_severity = "mild"
        else:
            overall_severity = "mild"

        return {
            "overall_severity": overall_severity,
            "severity_scores": severity_scores,
            "confidence_weighted_severity": round(confidence_weighted, 4),
            "positive_finding_count": len(positive),
            "negative_findings_debug": negative_findings,
            "recommendation": self.SEVERITY_RECOMMENDATION[overall_severity]
        }

if __name__ == "__main__":
    import json
    
    print("Testing SeverityReasoner...")
    reasoner = SeverityReasoner()
    dummy_concepts = [
        {
            "finding_id": "finding_001",
            "raw_label": "Hernia",
            "clinical_term": "hiatal hernia",
            "confidence": 0.82,
            "present": True,
            "severity": "moderate",
            "icd10_hint": ""
        },
        {
            "finding_id": "finding_002",
            "raw_label": "Effusion",
            "clinical_term": "pleural effusion",
            "confidence": 0.42,
            "present": False,
            "severity": "mild",
            "icd10_hint": "J90"
        }
    ]
    reasoned = reasoner.reason(dummy_concepts)
    print(json.dumps(reasoned, indent=2))
