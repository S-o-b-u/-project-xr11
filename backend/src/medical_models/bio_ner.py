from transformers import pipeline

class MedicalNER:
    def __init__(self):
        self.ner = pipeline(
            "ner",
            model="d4data/biomedical-ner-all",
            aggregation_strategy="simple",
            device=-1
        )
        print("MedicalNER loaded (local, CPU)")

    def extract_entities(self, text: str) -> dict:
        results = self.ner(text)
        
        all_entities = []
        findings_terms = []
        anatomical_regions = []
        unique_terms = set()
        high_confidence_terms = []
        
        for res in results:
            term = res["word"].strip()
            group = res["entity_group"]
            score = float(res["score"])
            
            if term not in unique_terms:
                unique_terms.add(term)
                all_entities.append({
                    "term": term,
                    "type": group,
                    "confidence": round(score, 4)
                })
                
                if group in ["DISEASE", "SIGN_SYMPTOM", "BIOLOGICAL_STRUCTURE"]:
                    findings_terms.append(term)
                
                if group == "BIOLOGICAL_STRUCTURE":
                    anatomical_regions.append(term)
                    
                if score > 0.85:
                    high_confidence_terms.append(term)
                    
        return {
            "all_entities": all_entities,
            "findings": findings_terms,
            "anatomical_regions": anatomical_regions,
            "entity_count": len(all_entities),
            "high_confidence_terms": high_confidence_terms
        }

    def compare_with_classifier(self, ner_entities: dict, classifier_output: dict) -> dict:
        consistent = True
        inconsistencies = []
        
        findings_lower = [f.lower() for f in ner_entities["findings"]]
        
        top_finding = classifier_output.get("top_finding", "")
        top_confidence = classifier_output.get("top_confidence", 0.0)
        
        if top_finding.upper() == "PNEUMONIA" and top_confidence > 0.7:
            # Check if pneumonia or related terms appear in NER findings
            related_terms = ["pneumonia", "consolidation", "infiltrate", "opacity", "infection"]
            found_related = any(any(rt in f for f in findings_lower) for rt in related_terms)
            
            if not found_related:
                consistent = False
                inconsistencies.append("Classifier predicted high-confidence PNEUMONIA, but no related terms were found in report findings.")
                
        cross_validation_score = 1.0 if consistent else max(0.0, 1.0 - (len(inconsistencies) * 0.2))
                
        return {
            "consistent": consistent,
            "inconsistencies": inconsistencies,
            "cross_validation_score": cross_validation_score
        }
