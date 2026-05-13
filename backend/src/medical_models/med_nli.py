from transformers import pipeline

class ClinicalNLI:
    def __init__(self):
        self.nli = pipeline(
            "zero-shot-classification",
            model="typeform/distilbert-base-uncased-mnli",
            device=-1
        )
        print("ClinicalNLI loaded (local, CPU)")

    def check_consistency(self, findings: str, impression: str, severity: str) -> dict:
        # CHECK 1: Does impression follow from findings?
        entailment_score = 0.0
        nli_result = "NEUTRAL"
        
        if impression and findings:
            result = self.nli(
                impression,
                candidate_labels=[findings[:200]], # limit length if very long
                hypothesis_template="{}"
            )
            entailment_score = result["scores"][0]
            
            if entailment_score > 0.7:
                nli_result = "ENTAILS"
            elif entailment_score > 0.4:
                nli_result = "NEUTRAL"
            else:
                nli_result = "CONTRADICTS"

        # CHECK 2: Is severity appropriate?
        severity_descriptors = {
            "CRITICAL": ["emergency", "urgent", "severe", "critical", "immediate", "life-threatening"],
            "MODERATE": ["moderate", "significant", "notable", "concerning", "follow-up required"],
            "MILD":     ["mild", "minor", "minimal", "slight", "small"],
            "NORMAL":   ["clear", "normal", "unremarkable", "no acute", "no abnormality"]
        }
        
        severity_check = "APPROPRIATE"
        imp_lower = impression.lower()
        
        if severity == "CRITICAL":
            has_critical = any(d in imp_lower for d in severity_descriptors["CRITICAL"])
            has_mild = any(d in imp_lower for d in severity_descriptors["MILD"])
            if not has_critical and has_mild:
                severity_check = "TOO_LOW"
        elif severity == "NORMAL":
            has_critical = any(d in imp_lower for d in severity_descriptors["CRITICAL"])
            has_moderate = any(d in imp_lower for d in severity_descriptors["MODERATE"])
            if has_critical or has_moderate:
                severity_check = "TOO_HIGH"
                
        # CHECK 3: Internal findings contradiction
        contradictions = "None"
        # Simplistic approach without full sentence tokenization for speed:
        # If findings contain both "normal" and "abnormal" near each other, flag it
        if "normal" in findings.lower() and "abnormal" in findings.lower():
            contradictions = "Found both 'normal' and 'abnormal' in findings, potential contradiction."
            
        # Compute a pseudo-consistency score
        consistency_score = entailment_score
        if severity_check != "APPROPRIATE":
            consistency_score -= 0.2
        if contradictions != "None":
            consistency_score -= 0.3
            
        consistency_score = max(0.0, min(1.0, consistency_score))

        return {
            "nli_result": nli_result,
            "entailment_score": round(entailment_score, 4),
            "severity_check": severity_check,
            "contradictions": contradictions,
            "consistency_score": round(consistency_score, 4),
            "model_used": "local-MiniLM (no API)"
        }
