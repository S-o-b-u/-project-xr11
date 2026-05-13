"""
Hybrid Clinical Retriever for RAG.
Combines visual similarity, pathology Jaccard overlap, and text embedding similarity.
"""
import os
import json
import pickle
import re
import numpy as np
import logging
from typing import List, Dict, Any, Optional

log = logging.getLogger(__name__)

# Medical term normalization: maps raw pathology labels → searchable synonyms
# Used for Jaccard overlap so "Hernia" matches "hernia" in gold_findings text
PATHOLOGY_SYNONYMS = {
    "hiatal hernia": ["hernia", "hiatal"],
    "cardiomegaly": ["cardiomegaly", "enlarged heart", "cardiac enlargement", "enlarged cardiac"],
    "pleural effusion": ["effusion", "pleural effusion", "pleural fluid"],
    "pulmonary edema": ["edema", "pulmonary edema", "vascular congestion"],
    "atelectasis": ["atelectasis", "volume loss", "collapse"],
    "pulmonary consolidation": ["consolidation", "airspace disease", "airspace opacity"],
    "pneumothorax": ["pneumothorax"],
    "pneumonia": ["pneumonia", "infectious process", "infection"],
    "pulmonary emphysema": ["emphysema", "hyperinflation", "hyperinflated"],
    "pulmonary fibrosis": ["fibrosis", "interstitial"],
    "pleural thickening": ["pleural thickening", "thickening"],
    "pulmonary nodule": ["nodule", "nodular"],
    "pulmonary mass": ["mass", "lesion"],
    "pulmonary infiltrate": ["infiltrate", "infiltration", "opacity"],
}


class HybridClinicalRetriever:
    """
    Retrieves relevant clinical cases by combining text, visual, and pathology signals.
    """
    def __init__(self, dataset_path: str, faiss_index_path: str, visual_index_path: Optional[str] = None):
        self.weights = {"visual": 0.45, "pathology": 0.35, "text": 0.20}
        self.dataset = []
        self.faiss_index = None
        self.text_metadata = []  # parallel to FAISS rows — each entry is the full report dict
        self.visual_index = None
        self.visual_metadata = []
        self.text_model = None

        _BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        _DATA_DIR = os.path.join(_BASE_DIR, "data", "processed")

        # Load Dataset
        try:
            if os.path.exists(dataset_path):
                with open(dataset_path, "r", encoding="utf-8") as f:
                    self.dataset = json.load(f)
                log.info(f"Loaded dataset with {len(self.dataset)} items")
            else:
                logging.warning(f"Dataset not found at {dataset_path}.")
        except Exception as e:
            logging.error(f"Failed to load dataset: {e}")

        # Load FAISS
        try:
            import faiss
            if os.path.exists(faiss_index_path):
                self.faiss_index = faiss.read_index(faiss_index_path)
                log.info(f"FAISS index loaded: {self.faiss_index.ntotal} vectors")

            # Resolve metadata path relative to data/processed/
            meta_path = os.path.join(_DATA_DIR, "faiss_metadata.pkl")
            if os.path.exists(meta_path):
                with open(meta_path, "rb") as f:
                    self.text_metadata = pickle.load(f)
                log.info(f"FAISS text metadata loaded: {len(self.text_metadata)} entries")
            else:
                log.warning(f"FAISS metadata not found at {meta_path}")
        except ImportError:
            logging.warning("faiss package not installed. Text FAISS retrieval disabled.")
        except Exception as e:
            logging.error(f"Failed to load FAISS or text metadata: {e}")

        # Load Visual Index
        if visual_index_path and os.path.exists(visual_index_path):
            try:
                self.visual_index = np.load(visual_index_path)
                vis_meta_path = os.path.join(_DATA_DIR, "visual_index_meta.pkl")
                if os.path.exists(vis_meta_path):
                    with open(vis_meta_path, "rb") as f:
                        self.visual_metadata = pickle.load(f)
                log.info(f"Visual index loaded: {self.visual_index.shape}")
            except Exception as e:
                logging.error(f"Failed to load visual index or metadata: {e}")

        # Initialize Text Model
        try:
            from sentence_transformers import SentenceTransformer
            self.text_model = SentenceTransformer("all-MiniLM-L6-v2")
        except ImportError:
            logging.warning("sentence_transformers not installed. Text retrieval disabled.")
        except Exception as e:
            logging.error(f"Failed to load SentenceTransformer: {e}")

    # ── helpers ──────────────────────────────────────────────────────────────

    def _get_case_id(self, item) -> str:
        """Extract a string case_id from a dataset item (dict or str)."""
        if isinstance(item, dict):
            return str(item.get("id", ""))
        return str(item)

    def _get_case_data(self, case_id) -> dict:
        if isinstance(self.dataset, dict):
            return self.dataset.get(case_id, {})
        elif isinstance(self.dataset, list):
            return next(
                (item for item in self.dataset
                 if isinstance(item, dict) and str(item.get("id", "")) == str(case_id)),
                {}
            )
        return {}

    @staticmethod
    def _build_report_text(case: dict) -> str:
        """Synthesize report_text from gold_findings + gold_impression."""
        findings = case.get("gold_findings", "") or ""
        impression = case.get("gold_impression", "") or ""
        text = case.get("report_text", "") or ""
        if text:
            return text
        return (findings + " " + impression).strip()

    @staticmethod
    def _extract_keywords(text: str) -> set:
        """Extract meaningful keyword tokens from free-text for Jaccard overlap."""
        if not text:
            return set()
        # lowercase, split on common separators
        tokens = re.split(r'[,;.\n]+', text.lower())
        # keep tokens > 3 chars, strip whitespace
        return set(t.strip() for t in tokens if len(t.strip()) > 3)

    @staticmethod
    def _expand_query_terms(query_terms: set) -> set:
        """Expand clinical terms using synonym map for better Jaccard overlap."""
        expanded = set(query_terms)
        for term in query_terms:
            synonyms = PATHOLOGY_SYNONYMS.get(term, [])
            expanded.update(synonyms)
        return expanded

    # ── main retrieve ────────────────────────────────────────────────────────

    def update_weights(self, visual: float, pathology: float, text: float):
        if abs((visual + pathology + text) - 1.0) > 1e-5:
            raise ValueError("Weights must sum to 1.0")
        self.weights = {"visual": visual, "pathology": pathology, "text": text}

    def retrieve(self,
                 query_image_embedding: np.ndarray,
                 query_concepts: List[Dict[str, Any]],
                 query_report_text: str = "",
                 top_k: int = 5) -> List[Dict[str, Any]]:
        """Executes the hybrid retrieval pipeline."""
        candidates = set()
        effective_weights = self.weights.copy()

        # ── 1. TEXT RETRIEVAL via FAISS (weight 0.20) ────────────────────────
        text_scores = {}
        if self.text_model is not None and self.faiss_index is not None and query_report_text:
            try:
                emb = self.text_model.encode([query_report_text], convert_to_numpy=True)
                emb = emb.astype(np.float32)
                # L2-normalize query to match IndexFlatIP convention
                norm = np.linalg.norm(emb)
                if norm > 0:
                    emb = emb / norm

                k_search = min(top_k * 3, self.faiss_index.ntotal)
                if k_search > 0:
                    # IndexFlatIP returns inner-product scores (= cosine for normalized vectors)
                    # Scores are in [-1, 1] range
                    scores, indices = self.faiss_index.search(emb, k_search)

                    for score, idx in zip(scores[0], indices[0]):
                        if idx < 0 or idx >= len(self.text_metadata):
                            continue
                        meta_item = self.text_metadata[idx]
                        case_id = self._get_case_id(meta_item)
                        if not case_id:
                            continue
                        # Normalize IP score from [-1,1] → [0,1]
                        normalized = (float(score) + 1.0) / 2.0
                        normalized = max(0.0, min(normalized, 1.0))
                        text_scores[case_id] = normalized
                        candidates.add(case_id)

                    log.info(f"TEXT RETRIEVAL: {len(text_scores)} candidates, "
                             f"raw scores range [{scores[0].min():.4f}, {scores[0].max():.4f}]")
            except Exception as e:
                logging.warning(f"Text retrieval failed: {e}")
                effective_weights["text"] = 0.0
        else:
            effective_weights["text"] = 0.0

        # ── 2. VISUAL RETRIEVAL (weight 0.45) ────────────────────────────────
        visual_scores = {}
        if self.visual_index is not None and len(self.visual_index) > 0 and query_image_embedding is not None:
            try:
                q_emb = query_image_embedding.flatten().astype(np.float32)

                # Normalize query
                q_norm = np.linalg.norm(q_emb)
                if q_norm > 0:
                    q_emb = q_emb / q_norm

                # Normalize database vectors
                db_norms = np.linalg.norm(self.visual_index, axis=1, keepdims=True)
                db_norms = np.where(db_norms == 0, 1.0, db_norms)
                db_normalized = self.visual_index / db_norms

                # Cosine similarities (both sides normalized → dot = cosine)
                raw_sims = np.dot(db_normalized, q_emb)

                k_search = min(top_k * 3, len(raw_sims))
                top_indices = np.argsort(raw_sims)[::-1][:k_search]

                for idx in top_indices:
                    if idx < len(self.visual_metadata):
                        case_id = self._get_case_id(self.visual_metadata[idx])
                        if not case_id:
                            continue
                        # Normalize cosine from [-1,1] → [0,1]
                        raw_val = float(raw_sims[idx])
                        normalized = (raw_val + 1.0) / 2.0
                        normalized = max(0.0, min(normalized, 1.0))
                        visual_scores[case_id] = normalized
                        candidates.add(case_id)

                log.info(f"VISUAL RETRIEVAL: {len(visual_scores)} candidates, "
                         f"raw cosine range [{raw_sims.min():.4f}, {raw_sims.max():.4f}]")
            except Exception as e:
                logging.warning(f"Visual retrieval failed: {e}")
                effective_weights["visual"] = 0.0
        else:
            effective_weights["visual"] = 0.0

        # ── 3. PATHOLOGY OVERLAP SCORING (weight 0.35) ───────────────────────
        query_findings = set()
        for concept in query_concepts:
            if concept.get("present", False) or concept.get("confidence", 0.0) > 0.5:
                query_findings.add(concept.get("clinical_term", "").lower())

        # Expand query terms with synonyms for better matching
        expanded_query = self._expand_query_terms(query_findings)

        pathology_scores = {}
        if not candidates and self.dataset:
            if isinstance(self.dataset, dict):
                candidates = set(self.dataset.keys())
            elif isinstance(self.dataset, list):
                candidates = set(
                    str(item.get("id", i))
                    for i, item in enumerate(self.dataset) if isinstance(item, dict)
                )

        for case_id in candidates:
            case_data = self._get_case_data(case_id)
            report_text = self._build_report_text(case_data)
            case_keywords = self._extract_keywords(report_text)

            if not expanded_query and not case_keywords:
                overlap = 0.1  # both empty = very low neutral
            elif not expanded_query or not case_keywords:
                overlap = 0.0
            else:
                # Check how many expanded query terms appear in the case text
                matches = sum(1 for term in expanded_query if any(term in kw for kw in case_keywords))
                overlap = matches / len(expanded_query) if expanded_query else 0.0

            pathology_scores[case_id] = float(max(0.0, min(overlap, 1.0)))

        # ── 4. SCORE FUSION ──────────────────────────────────────────────────
        total_weight = sum(effective_weights.values())
        if total_weight == 0:
            logging.warning("All retrieval components failed or skipped.")
            w_vis, w_path, w_text = 0.0, 0.0, 0.0
        else:
            w_vis = effective_weights["visual"] / total_weight
            w_path = effective_weights["pathology"] / total_weight
            w_text = effective_weights["text"] / total_weight

        fusion_results = []
        for case_id in candidates:
            v_score = float(max(0.0, min(visual_scores.get(case_id, 0.0), 1.0)))
            p_score = float(max(0.0, min(pathology_scores.get(case_id, 0.0), 1.0)))
            t_score = float(max(0.0, min(text_scores.get(case_id, 0.0), 1.0)))

            final_score = (v_score * w_vis) + (p_score * w_path) + (t_score * w_text)
            final_score = float(max(0.0, min(final_score, 1.0)))

            case_data = self._get_case_data(case_id)
            report_text = self._build_report_text(case_data)

            fusion_results.append({
                "case_id": case_id,
                "image_path": case_data.get("image_path", ""),
                "gold_findings": case_data.get("gold_findings", ""),
                "gold_impression": case_data.get("gold_impression", ""),
                "report_text": report_text[:300],
                "final_score": round(final_score, 4),
                "visual_score": round(v_score, 4),
                "pathology_overlap": round(p_score, 4),
                "text_score": round(t_score, 4),
                "matching_findings": list(query_findings)
            })

        fusion_results.sort(key=lambda x: x["final_score"], reverse=True)

        top_results = fusion_results[:top_k]
        for rank, res in enumerate(top_results, 1):
            res["rank"] = rank

        if top_results:
            log.info(f"RETRIEVAL TOP-1: score={top_results[0]['final_score']:.4f} "
                     f"vis={top_results[0]['visual_score']:.4f} "
                     f"path={top_results[0]['pathology_overlap']:.4f} "
                     f"text={top_results[0]['text_score']:.4f}")

        return top_results

    def get_retrieval_explanation(self, result: Dict[str, Any]) -> str:
        cid = result.get("case_id", "Unknown")
        fs = result.get("final_score", 0.0)
        vs = result.get("visual_score", 0.0)
        ps = result.get("pathology_overlap", 0.0)
        ts = result.get("text_score", 0.0)
        return (f"Retrieved case {cid} with similarity {fs:.4f}. "
                f"Visual: {vs:.4f}, Pathology overlap: {ps:.4f}, Text: {ts:.4f}.")
