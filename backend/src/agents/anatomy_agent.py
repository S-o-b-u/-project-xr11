"""
Module for the Anatomy Agent.
Produces ANATOMICAL SUSPICIONS only — never overrides confirmed pathology detector output.
"""
from typing import Dict, Any, List

# Minimum confidence required for anatomy hints to influence synthesis
ANATOMY_CONFIDENCE_GATE = 0.75

class AnatomyAgent:
    """
    Agent responsible for surfacing anatomical observations.
    
    IMPORTANT: This agent produces SUSPICIONS, not confirmed findings.
    Synthesis must never treat anatomy hints as confirmed pathology.
    """
    
    def __init__(self):
        self.normal_ranges = {
            "heart_width_ratio": (0.35, 0.55),
            "lung_symmetry_threshold": 0.15
        }

    def run(self, segmentation_result: Dict[str, Any], pathology_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyzes anatomical observations gated by the pathology detector.
        
        Rules:
        - Anatomy hints are only raised if confidence > ANATOMY_CONFIDENCE_GATE (0.75)
        - Anatomy agent NEVER overrides pathology detector's present=False
        - All outputs are labeled as suspicions, not confirmed findings
        """
        findings = pathology_result.get("findings", {})
        
        anatomical_suspicions: List[str] = []
        # Legacy key preserved for template fallback compatibility
        anatomical_notes: List[str] = []

        # ── Cardiomegaly ──────────────────────────────────────────────────────
        cardiomegaly_data = findings.get("Cardiomegaly", {})
        cardiomegaly_conf = cardiomegaly_data.get("confidence", 0.0)
        # Only flag if pathology detector also confirmed it AND confidence is high
        cardiomegaly_confirmed_by_detector = cardiomegaly_data.get("present", False)
        cardiomegaly_suspected = cardiomegaly_conf > ANATOMY_CONFIDENCE_GATE and cardiomegaly_confirmed_by_detector

        # ── Emphysema / Hyperinflation ─────────────────────────────────────────
        emphysema_data = findings.get("Emphysema", {})
        emphysema_conf = emphysema_data.get("confidence", 0.0)
        emphysema_confirmed_by_detector = emphysema_data.get("present", False)
        lung_hyperinflation = emphysema_conf > ANATOMY_CONFIDENCE_GATE and emphysema_confirmed_by_detector

        # ── Build suspicion notes ─────────────────────────────────────────────
        if cardiomegaly_suspected:
            msg = "Anatomical suspicion: enlarged cardiac silhouette. Confidence: {:.0%}.".format(cardiomegaly_conf)
            anatomical_suspicions.append(msg)
            anatomical_notes.append(msg)
        if lung_hyperinflation:
            msg = "Anatomical suspicion: hyperinflated lung fields. Confidence: {:.0%}.".format(emphysema_conf)
            anatomical_suspicions.append(msg)
            anatomical_notes.append(msg)

        normal_anatomy = not (cardiomegaly_suspected or lung_hyperinflation)
        if normal_anatomy:
            normal_msg = "No significant anatomical deviation detected."
            anatomical_suspicions.append(normal_msg)
            anatomical_notes.append(normal_msg)

        # Overall anatomy confidence (only from gated signals)
        gated_confs = [c for c in [cardiomegaly_conf, emphysema_conf] if c > ANATOMY_CONFIDENCE_GATE]
        confidence = float(sum(gated_confs) / len(gated_confs)) if gated_confs else 0.0

        return {
            "agent": "AnatomyAgent",
            "normal_anatomy": normal_anatomy,
            "cardiomegaly_suspected": cardiomegaly_suspected,
            "lung_hyperinflation": lung_hyperinflation,
            # Clearly labeled as suspicions not confirmations
            "anatomical_suspicions": anatomical_suspicions,
            # Legacy key for backward compat with synthesis template
            "anatomical_notes": anatomical_notes,
            "confidence": confidence,
            "note": "These are anatomical suspicions only. Do not treat as confirmed pathology."
        }

if __name__ == "__main__":
    import json
    print("Testing AnatomyAgent...")
    agent = AnatomyAgent()
    dummy_pathology = {
        "findings": {
            "Cardiomegaly": {"confidence": 0.8, "present": True},
            "Emphysema": {"confidence": 0.2, "present": False}
        }
    }
    res = agent.run({}, dummy_pathology)
    print(json.dumps(res, indent=2))
