"""
Module for cross-modal verification.
Detects hallucinations by aligning textual reports with visual embeddings.
"""
import numpy as np
from typing import Dict, Any, List

class CrossModalChecker:
    """
    Verifies that the generated textual report aligns with the visual image embeddings.
    """
    
    def __init__(self, hallucination_threshold: float = 0.20):
        """
        Initializes the cross-modal checker.
        """
        self.threshold = hallucination_threshold
        
        # Load EmbeddingEngine as required
        try:
            from src.vision.embedding_engine import EmbeddingEngine
            self.embedding_engine = EmbeddingEngine()
        except Exception as e:
            print(f"Failed to load EmbeddingEngine: {e}")
            self.embedding_engine = None
            
        # Primary: sentence_transformers. Fallback: EmbeddingEngine text encoder
        try:
            from sentence_transformers import SentenceTransformer
            self.sentence_model = SentenceTransformer("all-MiniLM-L6-v2")
            self.uses_st = True
        except ImportError:
            self.sentence_model = self.embedding_engine
            self.uses_st = False

    def _encode_sentence(self, sentence: str) -> np.ndarray:
        """
        Encodes a single sentence into a normalized embedding.
        """
        if self.uses_st and self.sentence_model is not None:
            emb = self.sentence_model.encode([sentence], convert_to_numpy=True)[0]
            norm = np.linalg.norm(emb)
            return emb / norm if norm > 0 else emb
        elif self.embedding_engine is not None:
            return self.embedding_engine.encode_text(sentence)
        else:
            return np.array([])

    def check(
        self,
        image_embedding: np.ndarray,
        report_text: str,
        positive_findings_count: int = None
    ) -> Dict[str, Any]:
        """
        Checks for hallucinations by comparing text semantics with visual embeddings.
        
        Parameters
        ----------
        image_embedding : np.ndarray
        report_text : str
        positive_findings_count : int, optional
            Number of confirmed findings — relaxes threshold for sparse/mild cases.
        """
        # Split into sentences
        raw_sentences = []
        for s in report_text.split(". "):
            raw_sentences.extend(s.split(".\n"))
        sentences = [s.strip() for s in raw_sentences if s.strip()]
        
        if not sentences:
            return {
                "hallucination_detected": False,
                "overall_alignment": 0.0,
                "sentence_scores": [],
                "flagged_sentences": [],
                "hallucination_risk": "low",
                "confidence": 1.0
            }

        # Adaptive threshold: relax for mild / single-finding reports
        effective_threshold = self.threshold  # default 0.20
        if positive_findings_count is not None and positive_findings_count <= 1:
            effective_threshold = 0.12  # very relaxed for normal / single subtle finding

        # Normalize image embedding once
        img_norm = np.linalg.norm(image_embedding)
        img_emb_unit = image_embedding / img_norm if img_norm > 0 else image_embedding

        sentence_scores = []
        flagged_sentences = []
        similarities = []
        
        for sentence in sentences:
            s_emb = self._encode_sentence(sentence)
            sim = 0.0
            
            if len(s_emb) > 0:
                # Project text embedding to same dim as image if possible
                if s_emb.shape == img_emb_unit.shape:
                    s_norm = np.linalg.norm(s_emb)
                    s_emb_unit = s_emb / s_norm if s_norm > 0 else s_emb
                    # Full cosine similarity (both vectors unit-normed)
                    sim = float(np.dot(img_emb_unit, s_emb_unit))
                    # Cosine can return values in [-1, 1]; clamp to [0, 1] for alignment
                    sim = float(max(0.0, min(sim, 1.0)))
                else:
                    # Dimension mismatch — try EmbeddingEngine fallback
                    if self.embedding_engine is not None:
                        try:
                            fb_emb = self.embedding_engine.encode_text(sentence)
                            if fb_emb.shape == img_emb_unit.shape:
                                fb_norm = np.linalg.norm(fb_emb)
                                fb_unit = fb_emb / fb_norm if fb_norm > 0 else fb_emb
                                sim = float(max(0.0, min(np.dot(img_emb_unit, fb_unit), 1.0)))
                        except Exception:
                            pass
            
            flagged = sim < effective_threshold
            if flagged:
                flagged_sentences.append(sentence)
            similarities.append(sim)
            sentence_scores.append({"sentence": sentence, "similarity": round(sim, 4), "flagged": flagged})
            
        overall_alignment = float(np.mean(similarities)) if similarities else 0.0
        flag_ratio = len(flagged_sentences) / len(sentences)

        # Risk tiers
        if overall_alignment > 0.35:
            hallucination_risk = "low"
        elif overall_alignment > 0.18:
            hallucination_risk = "medium"
        else:
            hallucination_risk = "high"

        # Only override to high if majority (>50%) of sentences flagged
        # (avoids false positives from short reports with 1-2 low-sim sentences)
        if flag_ratio > 0.50:
            hallucination_risk = "high"

        # hallucination_detected requires majority flagged AND high risk
        hallucination_detected = flag_ratio > 0.50 and hallucination_risk == "high"

        return {
            "hallucination_detected": hallucination_detected,
            "overall_alignment": round(overall_alignment, 4),
            "sentence_scores": sentence_scores,
            "flagged_sentences": flagged_sentences,
            "hallucination_risk": hallucination_risk,
            "flag_ratio": round(flag_ratio, 4),
            "confidence": round(max(0.0, 1.0 - flag_ratio), 4)
        }

    def verify_findings(self, detected_findings: List[str], report_text: str) -> Dict[str, Any]:
        """
        Rule-based check verifying if detected findings exist in text and checking for contradictions.
        """
        results = {}
        report_lower = report_text.lower()
        
        for finding in detected_findings:
            f_lower = finding.lower().replace("_", " ")
            
            found = f_lower in report_lower
            # Basic contradiction check: "no <finding>"
            contradicted = f"no {f_lower}" in report_lower or f"without {f_lower}" in report_lower
            
            # The prompt requires returning `{"finding": bool_found} dict for each finding`,
            # but also asks to check for contradictions. Wrapping it in a sub-dict preserves both.
            results[finding] = {
                "found": found,
                "contradicted": contradicted
            }
            
        return results

    def get_verification_summary(self, check_result: Dict[str, Any]) -> str:
        """
        Returns a human-readable verification summary string.
        """
        risk = check_result.get("hallucination_risk", "unknown")
        align = check_result.get("overall_alignment", 0.0)
        n_flagged = len(check_result.get("flagged_sentences", []))
        
        return f"Cross-modal verification: {risk} risk. Overall alignment: {align:.4f}. {n_flagged} sentences flagged."

if __name__ == "__main__":
    import json
    import sys, os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    
    print("Testing CrossModalChecker...")
    checker = CrossModalChecker()
    
    # Simulating CLIP embedding size 512
    dummy_img_emb = np.random.rand(512).astype(np.float32)
    dummy_img_emb /= np.linalg.norm(dummy_img_emb)
    
    dummy_report = "The lungs are clear. There is a small pleural effusion. Heart size is normal."
    
    res = checker.check(dummy_img_emb, dummy_report)
    
    print("\nCheck Result (Summary):")
    print(json.dumps({
        "hallucination_detected": res["hallucination_detected"],
        "overall_alignment": res["overall_alignment"],
        "hallucination_risk": res["hallucination_risk"],
        "flagged_count": len(res["flagged_sentences"])
    }, indent=2))
    
    print("\nVerification Summary:")
    print(checker.get_verification_summary(res))
    
    print("\nFindings Verification:")
    findings_res = checker.verify_findings(["pleural effusion", "pneumothorax"], dummy_report)
    print(json.dumps(findings_res, indent=2))
