"""
Module for the Consistency Agent.
"""
from typing import Dict, Any, List

class ConsistencyAgent:
    """
    Agent responsible for checking logical consistency between visual findings and generated text.
    """
    
    def __init__(self):
        """
        Loads the ClinicalNLI model if available, otherwise runs entirely rule-based.
        """
        self.nli_model = None
        try:
            from src.medical_models.med_nli import ClinicalNLI
            self.nli_model = ClinicalNLI()
        except Exception as e:
            print(f"Failed to load ClinicalNLI: {e}. Falling back to rule-based consistency check only.")

    def run(self, report_text: str, concepts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validates the consistency of the report against the extracted concepts.
        
        Steps:
        1. Build premise claims from concepts
        2. Run NLI check against the generated report_text
        3. Perform hard-coded impossible combination rule checks
        """
        contradictions_found = []
        nli_scores = {}
        impossible_combinations = []
        
        # Rule-based impossible combination checks
        terms = [c.get("clinical_term", "").lower() for c in concepts if c.get("present")]
        severities = [c.get("severity", "") for c in concepts if c.get("present")]
        
        if "pneumothorax" in terms and "pleural effusion" in terms:
            impossible_combinations.append("pneumothorax + pleural effusion: verify laterality")
            
        if "normal" in severities and "severe" in severities:
            impossible_combinations.append("normal + severe findings together: flag as inconsistency")

        if self.nli_model is not None and report_text:
            hypothesis = report_text[:256]
            for concept in concepts:
                if not concept.get("present"):
                    continue
                term = concept.get("clinical_term", "")
                sev = concept.get("severity", "unknown")
                premise = f"The patient has {term} with {sev} severity."
                
                try:
                    # Execute NLI check
                    result = self.nli_model.check_consistency(findings=premise, impression=hypothesis, severity=sev)
                    is_contradiction = result.get("nli_result", "") == "CONTRADICTS"
                    score = result.get("consistency_score", 0.0)
                    
                    nli_scores[term] = score
                    if is_contradiction:
                        contradictions_found.append(f"Contradiction between finding '{term}' and text: '{hypothesis}'")
                except Exception as e:
                    print(f"NLI check failed for {term}: {e}")
                    
        consistent = len(contradictions_found) == 0 and len(impossible_combinations) == 0
        confidence = 1.0 if consistent else 0.5
        
        return {
            "agent": "ConsistencyAgent",
            "consistent": consistent,
            "contradictions_found": contradictions_found,
            "nli_scores": nli_scores,
            "impossible_combinations": impossible_combinations,
            "confidence": confidence
        }

if __name__ == "__main__":
    import json
    print("Testing ConsistencyAgent...")
    agent = ConsistencyAgent()
    dummy_text = "The lungs are clear and expanded. No pneumothorax."
    dummy_concepts = [
        {"clinical_term": "pneumothorax", "present": True, "severity": "severe"},
        {"clinical_term": "pleural effusion", "present": True, "severity": "mild"}
    ]
    res = agent.run(dummy_text, dummy_concepts)
    print(json.dumps(res, indent=2))
