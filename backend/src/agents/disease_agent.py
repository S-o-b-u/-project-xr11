"""
Module for the Disease Agent.
"""
from typing import Dict, Any
import numpy as np

# Use absolute imports for full XR11 backend usage
from src.concepts.concept_extractor import ConceptExtractor
from src.concepts.severity_reasoner import SeverityReasoner

class DiseaseAgent:
    """
    Agent responsible for diagnosing and characterizing detected pathologies.
    """
    
    def __init__(self):
        """
        Initializes the disease logic with concept and severity processors.
        """
        self.concept_extractor = ConceptExtractor()
        self.severity_reasoner = SeverityReasoner()

    def run(self, pathology_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the agent's logic on pathology findings.
        """
        # 1. Extract ALL concepts (positive + negative)
        all_concepts = self.concept_extractor.extract(pathology_result)
        
        # 2. Filter to confirmed positive concepts only for downstream reasoning
        positive_concepts = [c for c in all_concepts if c.get("present") is True]
        negative_concepts = [c for c in all_concepts if not c.get("present")]
        
        # 3. Run severity reasoner — ONLY on positive concepts
        severity_assessment = self.severity_reasoner.reason(positive_concepts)
        
        positive_findings_count = len(positive_concepts)
        confs = [c.get("confidence", 0.0) for c in positive_concepts]
        confidence = float(np.mean(confs)) if confs else 1.0
        
        primary_hint = "No acute disease"
        if positive_concepts:
            sorted_c = sorted(positive_concepts, key=lambda x: x.get("confidence", 0.0), reverse=True)
            primary_hint = sorted_c[0].get("clinical_term", "unknown condition")
            
        clinical_summary = f"Identified {positive_findings_count} confirmed finding(s). Primary: {primary_hint}."
        
        return {
            "agent": "DiseaseAgent",
            # Pass full concept list for UI debug; downstream agents filter themselves
            "concepts": all_concepts,
            "positive_concepts": positive_concepts,
            "negative_concepts_debug": [c.get("clinical_term") for c in negative_concepts],
            "positive_findings_count": positive_findings_count,
            "severity_assessment": severity_assessment,
            "primary_diagnosis_hint": primary_hint,
            "clinical_summary": clinical_summary,
            "confidence": confidence
        }

if __name__ == "__main__":
    import json
    import sys, os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    
    print("Testing DiseaseAgent...")
    agent = DiseaseAgent()
    dummy_path = {
        "findings": {
            "Atelectasis": {"present": True, "confidence": 0.87},
            "Pneumothorax": {"present": False, "confidence": 0.15}
        }
    }
    res = agent.run(dummy_path)
    print(json.dumps(res, indent=2))
