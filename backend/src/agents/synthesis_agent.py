"""
Module for the Synthesis Agent.
"""

from typing import Dict, Any


class SynthesisAgent:
    """
    Agent responsible for synthesizing findings from all other agents into a cohesive draft.
    This is the ONLY agent that calls an external API.
    """

    def __init__(self, groq_api_key: str = None, gemini_api_key: str = None):
        """
        Initializes the LLM backend depending on available API keys.
        """
        self.groq_api_key = groq_api_key
        self.gemini_api_key = gemini_api_key
        self.backend = "template"

        if self.groq_api_key:
            self.backend = "groq_llm"
            try:
                import groq

                self.groq_client = groq.Client(api_key=self.groq_api_key)
            except ImportError:
                print("groq library not installed. Falling back to template.")
                self.backend = "template"
        elif self.gemini_api_key:
            self.backend = "gemini_llm"
            try:
                import google.generativeai as genai

                genai.configure(api_key=self.gemini_api_key)
                self.gemini_model = genai.GenerativeModel("gemini-1.5-pro")
            except ImportError:
                print(
                    "google-generativeai library not installed. Falling back to template."
                )
                self.backend = "template"

    def run(
        self,
        disease_output: Dict[str, Any],
        anatomy_output: Dict[str, Any],
        retrieval_output: Dict[str, Any],
        consistency_output: Dict[str, Any],
        use_llm: bool = True,
    ) -> Dict[str, Any]:
        """
        Synthesizes the final context into a cohesive report draft.

        Parameters
        ----------
        disease_output : dict
        anatomy_output : dict
        retrieval_output : dict
        consistency_output : dict
        use_llm : bool

        Returns
        -------
        dict
            The final structured radiology report object.
        """
        concepts = disease_output.get("concepts", [])

        # ── HARD GROUNDING: Only use confirmed (present=True) findings ────────
        confirmed_findings = [c for c in concepts if c.get("present") is True]
        negative_findings  = [c for c in concepts if not c.get("present")]
        
        positive_terms = [c.get("clinical_term", "") for c in confirmed_findings]
        findings_list = ", ".join(positive_terms) if positive_terms else "No acute cardiopulmonary findings"
        
        # Negative findings available for debug; NEVER passed to LLM
        negative_terms = [c.get("clinical_term", "") for c in negative_findings]

        severity_data = disease_output.get("severity_assessment", {})
        severity = severity_data.get("overall_severity", "normal")
        recommendation = severity_data.get("recommendation", "Clinical correlation recommended.")

        retrieved_impression = retrieval_output.get("top_case_report", "")
        
        # Anatomy suspicions are clearly separated and labeled as unconfirmed
        anatomy_conf = anatomy_output.get("confidence", 0.0)
        raw_suspicions = anatomy_output.get("anatomical_suspicions", anatomy_output.get("anatomical_notes", []))
        # Only include anatomy suspicions if confidence gate is met
        anatomy_context = ""
        if anatomy_conf >= 0.75 and raw_suspicions:
            anatomy_context = "Unconfirmed anatomical suspicions (do not treat as confirmed): " + " ".join(raw_suspicions)

        api_calls_used = 0

        findings_str = ""
        impression_str = ""
        recommendation_str = ""
        full_report_str = ""

        if use_llm and self.backend == "groq_llm":
            prompt = (
                f"You are a board-certified radiologist writing a structured chest X-ray report.\n\n"
                f"CONFIRMED PATHOLOGY FINDINGS (present=True, confidence > 0.70):\n"
                f"{findings_list}\n\n"
                f"SEVERITY: {severity}\n\n"
                f"STRICT INSTRUCTIONS — READ CAREFULLY:\n"
                f"- DO NOT infer, speculate, or add any finding not listed above.\n"
                f"- DO NOT mention cardiomegaly, emphysema, hyperinflation, or any other condition unless it appears in CONFIRMED PATHOLOGY FINDINGS.\n"
                f"- DO NOT use findings from historical cases as if they are this patient's findings.\n"
                f"- ONLY describe findings explicitly confirmed above.\n"
                f"- If no confirmed findings exist, report as normal chest X-ray.\n"
                f"- Keep the report concise, clinical, and factual.\n\n"
                f"{anatomy_context}\n"
                f"Reference case impression (for style only, do not copy findings): {retrieved_impression[:150]}\n\n"
                f"Generate a structured radiology report:\n"
                f"FINDINGS: [2-3 sentences. Only confirmed findings.]\n"
                f"IMPRESSION: [1-2 sentences clinical interpretation of confirmed findings only.]\n"
                f"RECOMMENDATION: [{recommendation}]\n"
                f"Maximum 180 words total."
            )
            try:
                chat_completion = self.groq_client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.3-70b-versatile",
                    max_tokens=600,
                )
                api_calls_used += 1
                full_report_str = chat_completion.choices[0].message.content

                # Simple parsing fallback
                sections = full_report_str.split("\n")
                for line in sections:
                    line = line.strip()
                    if line.upper().startswith("FINDINGS:"):
                        findings_str = line[len("FINDINGS:") :].strip()
                    elif line.upper().startswith("IMPRESSION:"):
                        impression_str = line[len("IMPRESSION:") :].strip()
                    elif line.upper().startswith("RECOMMENDATION:"):
                        recommendation_str = line[len("RECOMMENDATION:") :].strip()
            except Exception as e:
                print(f"Groq API call failed: {e}")
                self.backend = "template"

        if self.backend == "template" or not full_report_str:
            # ── Grounded template fallback ────────────────────────────────────
            if positive_terms:
                findings_str = f"The following findings are identified: {findings_list}."
            else:
                findings_str = "No acute cardiopulmonary findings are identified. The lungs appear clear."
            impression_str = f"Overall severity: {severity}. {findings_list if positive_terms else 'Normal chest radiograph.'}"
            recommendation_str = severity_data.get("recommendation", "Clinical correlation recommended.")
            full_report_str = f"FINDINGS: {findings_str}\nIMPRESSION: {impression_str}\nRECOMMENDATION: {recommendation_str}"
            self.backend = "template"

        return {
            "agent": "SynthesisAgent",
            "report": {
                "findings": findings_str,
                "impression": impression_str,
                "recommendation": recommendation_str,
                "full_report": full_report_str,
            },
            "generation_method": self.backend,
            "api_calls_used": api_calls_used,
            "confidence": 0.95 if self.backend != "template" else 0.7,
        }


if __name__ == "__main__":
    import json

    print("Testing SynthesisAgent...")
    agent = SynthesisAgent()
    disease = {
        "concepts": [{"clinical_term": "pneumonia", "present": True}],
        "severity_assessment": {
            "overall_severity": "moderate",
            "recommendation": "Radiologist review.",
        },
    }
    anatomy = {"anatomical_notes": ["Lungs are slightly hyperinflated."]}
    retrieval = {"top_case_report": "Impression: Likely infectious process."}
    consistency = {}

    res = agent.run(disease, anatomy, retrieval, consistency, use_llm=False)
    print(json.dumps(res, indent=2))
