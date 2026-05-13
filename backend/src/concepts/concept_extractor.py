"""
Module for extracting medical concepts from raw pathology detection results.
"""
from typing import Dict, Any, List

class ConceptExtractor:
    """
    Extracts high-level medical concepts and entities from raw pathology detection results.
    """
    
    def __init__(self):
        """
        Initializes the concept extractor with clinical mapping dictionaries.
        """
        self.clinical_terms_map = {
            "Atelectasis": "atelectasis",
            "Consolidation": "pulmonary consolidation",
            "Infiltration": "pulmonary infiltrate",
            "Pneumothorax": "pneumothorax",
            "Edema": "pulmonary edema",
            "Emphysema": "pulmonary emphysema",
            "Fibrosis": "pulmonary fibrosis",
            "Effusion": "pleural effusion",
            "Pneumonia": "pneumonia",
            "Pleural_Thickening": "pleural thickening",
            "Cardiomegaly": "cardiomegaly",
            "Nodule": "pulmonary nodule",
            "Mass": "pulmonary mass",
            "Hernia": "hiatal hernia"
        }
        
        self.icd10_hints = {
            "Atelectasis": "J98.11",
            "Effusion": "J90",
            "Pneumonia": "J18.9",
            "Pneumothorax": "J93.9",
            "Cardiomegaly": "I51.7",
            "Edema": "J81.1"
        }

    def _get_severity_label(self, confidence: float) -> str:
        """Helper to get a basic severity string from confidence."""
        if confidence < 0.3:
            return "normal"
        elif confidence < 0.5:
            return "mild"
        elif confidence < 0.75:
            return "moderate"
        else:
            return "severe"

    def extract(self, pathology_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Processes pathology results and returns a list of standardized medical concepts.
        
        Parameters
        ----------
        pathology_results : dict
            The output from PathologyDetector.detect().
            
        Returns
        -------
        list of dict
            A list of concept dictionaries for each relevant finding.
        """
        concepts = []
        findings = pathology_results.get("findings", {})
        
        idx = 1
        for raw_label, data in findings.items():
            present = data.get("present", False)
            confidence = data.get("confidence", 0.0)
            
            # Only include findings where present=True OR confidence > 0.3
            if present or confidence > 0.3:
                clinical_term = self.clinical_terms_map.get(raw_label, raw_label.lower())
                icd10 = self.icd10_hints.get(raw_label, "")
                severity = self._get_severity_label(confidence)
                
                concept = {
                    "finding_id": f"finding_{idx:03d}",
                    "raw_label": raw_label,
                    "clinical_term": clinical_term,
                    "confidence": confidence,
                    "present": present,
                    "severity": severity,
                    "icd10_hint": icd10
                }
                concepts.append(concept)
                idx += 1
                
        return concepts

if __name__ == "__main__":
    import json
    
    print("Testing ConceptExtractor...")
    extractor = ConceptExtractor()
    dummy_results = {
        "findings": {
            "Atelectasis": {"present": True, "confidence": 0.87},
            "Pneumothorax": {"present": False, "confidence": 0.15},
            "Effusion": {"present": False, "confidence": 0.42}
        }
    }
    extracted = extractor.extract(dummy_results)
    print(json.dumps(extracted, indent=2))
