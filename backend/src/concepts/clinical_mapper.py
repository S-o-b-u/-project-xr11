"""
Module for mapping concepts to clinical ontologies and systems.
"""
from typing import Dict, Any, List

class ClinicalMapper:
    """
    Maps extracted medical concepts to standard clinical vocabularies and systems.
    """
    
    def __init__(self):
        """
        Initializes the clinical mapper with affected system definitions.
        """
        self.pulmonary_terms = {
            "atelectasis", "pulmonary consolidation", "pneumonia", 
            "pulmonary edema", "pulmonary emphysema", "pulmonary fibrosis", 
            "pulmonary infiltrate", "pulmonary nodule", "pulmonary mass"
        }
        self.cardiac_terms = {"cardiomegaly"}
        self.pleural_terms = {"pleural effusion", "pleural thickening"}

    def map(self, concepts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Maps a list of concepts to their corresponding clinical ontology terms and systems.
        
        Parameters
        ----------
        concepts : list of dict
            List of concept dictionaries from ConceptExtractor.
            
        Returns
        -------
        dict
            Dictionary containing mapped systems, primary findings, and impressions.
        """
        all_findings = []
        affected_systems_set = set()
        primary_finding = None
        max_conf = -1.0
        requires_urgent = False
        
        for concept in concepts:
            term = concept.get("clinical_term", "")
            all_findings.append(term)
            
            conf = concept.get("confidence", 0.0)
            if conf > max_conf:
                max_conf = conf
                primary_finding = term
                
            if term in self.pulmonary_terms:
                affected_systems_set.add("pulmonary")
            if term in self.cardiac_terms:
                affected_systems_set.add("cardiac")
            if term in self.pleural_terms:
                affected_systems_set.add("pleural")
                
            if term == "pneumothorax" or (term == "cardiomegaly" and concept.get("severity") == "severe"):
                requires_urgent = True

        affected_systems = list(affected_systems_set)
        
        if not all_findings:
            impression = "No acute cardiopulmonary findings identified."
        else:
            impression = f"Findings consistent with {', '.join(all_findings)}. Clinical correlation recommended."
            
        return {
            "primary_finding": primary_finding,
            "all_findings": all_findings,
            "affected_systems": affected_systems,
            "report_impression": impression,
            "requires_urgent_attention": requires_urgent
        }

if __name__ == "__main__":
    import json
    
    print("Testing ClinicalMapper...")
    mapper = ClinicalMapper()
    dummy_concepts = [
        {
            "finding_id": "finding_001",
            "raw_label": "Atelectasis",
            "clinical_term": "atelectasis",
            "confidence": 0.87,
            "present": True,
            "severity": "severe",
            "icd10_hint": "J98.11"
        },
        {
            "finding_id": "finding_002",
            "raw_label": "Cardiomegaly",
            "clinical_term": "cardiomegaly",
            "confidence": 0.76,
            "present": True,
            "severity": "severe",
            "icd10_hint": "I51.7"
        }
    ]
    mapped = mapper.map(dummy_concepts)
    print(json.dumps(mapped, indent=2))
