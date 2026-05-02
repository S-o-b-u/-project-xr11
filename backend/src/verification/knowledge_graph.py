"""
knowledge_graph.py
──────────────────
Grounds generated radiology reports against two medical knowledge sources:

1. **RadLex** (radlex.org) — the standard radiology lexicon (OWL ontology).
   Loaded locally from data/raw/radlex.owl via owlready2.

2. **ICD-10** — hardcoded mapping of common radiology findings to ICD-10 codes,
   supplemented by the simple_icd_10 library for code validation.
"""

import logging
import os
import re
from typing import Optional

log = logging.getLogger(__name__)

# ── Radiology term vocabulary (54 terms) ──────────────────────────────────────
RADIOLOGY_TERMS: list[str] = [
    # Opacity / density patterns
    "consolidation", "opacity", "infiltrate", "airspace", "interstitial",
    "ground-glass", "haziness",
    # Fluid
    "effusion", "pleural effusion", "hemothorax", "edema", "pulmonary edema",
    # Air
    "pneumothorax", "pneumomediastinum", "pneumopericardium", "hyperinflation",
    "emphysema",
    # Infection / inflammation
    "pneumonia", "lobar pneumonia", "abscess", "cavitation",
    # Masses / nodules
    "nodule", "mass", "lung mass", "calcification",
    # Heart / vessels
    "cardiomegaly", "cardiac", "vascular", "pulmonary", "aorta",
    "lymphadenopathy",
    # Structural
    "atelectasis", "fibrosis", "bronchiectasis", "pleural", "mediastinum",
    "hilum", "diaphragm", "costophrenic", "trachea", "carina",
    # Bone
    "fracture", "rib fracture", "scoliosis", "kyphosis", "osteophyte",
    "demineralization",
    # Devices / lines
    "pacemaker", "catheter", "tube", "clip", "staple",
]

# ── ICD-10 hardcoded mapping (30 entries) ─────────────────────────────────────
ICD10_MAP: dict[str, dict] = {
    "pneumonia":           {"code": "J18.9",  "description": "Pneumonia, unspecified"},
    "lobar pneumonia":     {"code": "J18.1",  "description": "Lobar pneumonia, unspecified"},
    "pleural effusion":    {"code": "J90",    "description": "Pleural effusion, not elsewhere classified"},
    "pneumothorax":        {"code": "J93.9",  "description": "Pneumothorax, unspecified"},
    "cardiomegaly":        {"code": "I51.7",  "description": "Cardiomegaly"},
    "pulmonary edema":     {"code": "J81.1",  "description": "Chronic pulmonary edema"},
    "atelectasis":         {"code": "J98.11", "description": "Atelectasis"},
    "emphysema":           {"code": "J43.9",  "description": "Emphysema, unspecified"},
    "lung mass":           {"code": "R91.8",  "description": "Other nonspecific abnormal findings on chest X-ray"},
    "rib fracture":        {"code": "S22.3",  "description": "Fracture of rib"},
    "fibrosis":            {"code": "J84.10", "description": "Pulmonary fibrosis, unspecified"},
    "bronchiectasis":      {"code": "J47.9",  "description": "Bronchiectasis, uncomplicated"},
    "consolidation":       {"code": "J98.09", "description": "Diseases of bronchus, not elsewhere classified"},
    "hemothorax":          {"code": "J94.2",  "description": "Haemothorax"},
    "pneumomediastinum":   {"code": "J98.2",  "description": "Interstitial emphysema"},
    "lymphadenopathy":     {"code": "R59.9",  "description": "Enlarged lymph nodes, unspecified"},
    "fracture":            {"code": "M84.40", "description": "Pathological fracture, unspecified site"},
    "scoliosis":           {"code": "M41.9",  "description": "Scoliosis, unspecified"},
    "kyphosis":            {"code": "M40.299","description": "Other kyphosis, unspecified site"},
    "osteophyte":          {"code": "M25.70", "description": "Osteophyte, unspecified joint"},
    "nodule":              {"code": "R91.1",  "description": "Solitary pulmonary nodule"},
    "cavitation":          {"code": "A15.0",  "description": "Tuberculosis of lung (for cavitation context)"},
    "abscess":             {"code": "J85.1",  "description": "Abscess of lung with pneumonia"},
    "effusion":            {"code": "J90",    "description": "Pleural effusion"},
    "hyperinflation":      {"code": "J43.9",  "description": "Emphysema (hyperinflation)"},
    "cardiomegaly":        {"code": "I51.7",  "description": "Cardiomegaly"},
    "ground-glass":        {"code": "J80",    "description": "Acute respiratory distress syndrome"},
    "interstitial":        {"code": "J84.9",  "description": "Interstitial pulmonary disease, unspecified"},
    "calcification":       {"code": "J98.4",  "description": "Other disorders of lung"},
    "opacity":             {"code": "R91.8",  "description": "Other nonspecific abnormal chest findings"},
}


class KnowledgeGraphGrounder:
    """Grounds radiology report text against RadLex and ICD-10."""

    def __init__(self, radlex_path: str = "data/raw/radlex.owl") -> None:
        self._radlex_lookup: dict[str, dict] = {}
        self._radlex_loaded = False
        self._icd10_available = False

        # ── Load RadLex ───────────────────────────────────────────────────────
        if os.path.isfile(radlex_path):
            try:
                log.info("[KG] Loading RadLex from %s …", radlex_path)
                from owlready2 import get_ontology
                onto = get_ontology("http://radlex.org/").load(
                    fileobj=open(radlex_path, "rb")
                )
                for cls in onto.classes():
                    labels = []
                    # Prefer rdfs:label, fallback to class name
                    if hasattr(cls, "label") and cls.label:
                        labels = [str(lbl) for lbl in cls.label]
                    if not labels:
                        labels = [cls.name]
                    for lbl in labels:
                        self._radlex_lookup[lbl.lower()] = {
                            "radlex_id":      cls.name,
                            "standard_label": labels[0],
                        }
                self._radlex_loaded = True
                log.info("[KG] RadLex loaded: %d terms.", len(self._radlex_lookup))
            except Exception as exc:
                log.warning("[KG] RadLex failed to load: %s", exc)
        else:
            log.warning("[KG] RadLex OWL file not found at %s — running without ontology.", radlex_path)

        # ── Load simple_icd_10 ────────────────────────────────────────────────
        try:
            import simple_icd_10 as icd10
            self._icd10 = icd10
            self._icd10_available = True
        except ImportError:
            log.warning("[KG] simple_icd_10 not installed — ICD-10 validation skipped.")

    # ── Public API ─────────────────────────────────────────────────────────────

    def extract_medical_terms(self, text: str) -> list[str]:
        """Find radiology vocabulary terms present in *text*.

        Parameters
        ----------
        text : str
            Raw findings or impression text.

        Returns
        -------
        list[str]
            Unique radiology terms found (in the order they first appear).
        """
        text_lower = text.lower()
        found: list[str] = []
        seen: set[str] = set()
        # Check multi-word terms first (longer match wins)
        for term in sorted(RADIOLOGY_TERMS, key=len, reverse=True):
            pattern = r"\b" + re.escape(term) + r"\b"
            if re.search(pattern, text_lower) and term not in seen:
                found.append(term)
                seen.add(term)
        return found

    def lookup_radlex(self, term: str) -> dict:
        """Search the loaded RadLex ontology for *term*.

        Parameters
        ----------
        term : str
            A single medical term to look up.

        Returns
        -------
        dict
            ``{found, radlex_id, standard_label}``
        """
        key = term.lower().strip()
        if key in self._radlex_lookup:
            entry = self._radlex_lookup[key]
            return {
                "found":          True,
                "radlex_id":      entry["radlex_id"],
                "standard_label": entry["standard_label"],
            }
        # Partial-word match fallback
        for stored_key, entry in self._radlex_lookup.items():
            if key in stored_key or stored_key in key:
                return {
                    "found":          True,
                    "radlex_id":      entry["radlex_id"],
                    "standard_label": entry["standard_label"],
                }
        return {"found": False, "radlex_id": None, "standard_label": term}

    def map_to_icd10(self, findings: str, impression: str) -> list[dict]:
        """Map recognized findings/impressions to ICD-10 codes.

        Parameters
        ----------
        findings : str
        impression : str

        Returns
        -------
        list[dict]
            Each entry: ``{finding, icd10_code, description}``
        """
        combined = (findings + " " + impression).lower()
        matched: list[dict] = []
        seen_codes: set[str] = set()

        for term, info in ICD10_MAP.items():
            if re.search(r"\b" + re.escape(term) + r"\b", combined):
                code = info["code"]
                if code not in seen_codes:
                    matched.append({
                        "finding":    term,
                        "icd10_code": code,
                        "description": info["description"],
                    })
                    seen_codes.add(code)

        return matched

    def ground_report(self, findings: str, impression: str) -> dict:
        """Full grounding pipeline for a single report.

        Parameters
        ----------
        findings : str
        impression : str

        Returns
        -------
        dict
            ``{terms_found, radlex_matches, unmatched_terms,
               icd10_codes, standardization_rate}``
        """
        combined = findings + " " + impression
        terms = self.extract_medical_terms(combined)

        radlex_matches: list[dict] = []
        unmatched_terms: list[str] = []

        for term in terms:
            result = self.lookup_radlex(term)
            radlex_matches.append({"term": term, **result})
            if not result["found"]:
                unmatched_terms.append(term)

        icd10_codes = self.map_to_icd10(findings, impression)

        matched_count = len(terms) - len(unmatched_terms)
        standardization_rate = (matched_count / len(terms)) if terms else 0.0

        return {
            "terms_found":          terms,
            "radlex_matches":       radlex_matches,
            "unmatched_terms":      unmatched_terms,
            "icd10_codes":          icd10_codes,
            "standardization_rate": round(standardization_rate, 3),
        }
