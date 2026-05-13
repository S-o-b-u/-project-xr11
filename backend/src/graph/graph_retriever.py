"""
Module for retrieving information from the clinical graph.
"""
from typing import List, Dict, Any
import networkx as nx

class GraphRetriever:
    """
    Retrieves relevant subgraphs and context from the clinical knowledge graph.
    """
    
    def __init__(self, graph_builder):
        """
        Initializes the retriever with a reference to the ClinicalGraphBuilder.
        """
        self.graph_builder = graph_builder
        self.graph = graph_builder.graph

    def _validated_concepts(self, concepts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Returns only concepts that are confirmed and exceed confidence threshold."""
        return [
            c for c in concepts
            if c.get("present") is True and c.get("confidence", 0.0) > 0.6
        ]

    def retrieve(self, concepts: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieves graph-based insights using ONLY validated positive concepts.
        
        Parameters
        ----------
        concepts : list of dict
            Full concept list (will be filtered internally).
        top_k : int
        
        Returns
        -------
        list of dict
        """
        validated = self._validated_concepts(concepts)
        
        results = []
        undirected_graph = self.graph.to_undirected()
        
        for concept in validated:
            raw_term = concept.get("clinical_term", "")
            confidence = concept.get("confidence", 1.0)
            clean_term = raw_term.replace(" ", "_").lower()
            
            if clean_term not in self.graph:
                continue
                
            related_findings = self.graph_builder.get_related_findings(clean_term)
            diag_hints = self.graph_builder.get_diagnosis_hints(clean_term)
            
            for related in related_findings:
                try:
                    path_len = nx.shortest_path_length(undirected_graph, source=clean_term, target=related)
                except nx.NetworkXNoPath:
                    path_len = 2
                    
                score = (1.0 / (path_len + 1)) * confidence
                sig = "Diagnostic hint" if related in diag_hints else "Related clinical finding"
                
                try:
                    path = nx.shortest_path(undirected_graph, source=clean_term, target=related)
                except nx.NetworkXNoPath:
                    path = [clean_term, related]
                
                results.append({
                    "source_finding": raw_term,
                    "related_finding": related,
                    "relation_path": path,
                    "relevance_score": score,
                    "clinical_significance": sig
                })
                
        # Deduplicate: keep highest score per unique related finding
        best_results = {}
        for r in results:
            rf = r["related_finding"]
            if rf not in best_results or r["relevance_score"] > best_results[rf]["relevance_score"]:
                best_results[rf] = r
                
        sorted_results = sorted(best_results.values(), key=lambda x: x["relevance_score"], reverse=True)
        return sorted_results[:top_k]

    def get_clinical_context(self, concepts: List[Dict[str, Any]]) -> str:
        """
        Returns a formatted string describing graph-based context for LLM use.
        ONLY uses validated (present=True, confidence>0.6) concepts.
        """
        validated = self._validated_concepts(concepts)
        
        contexts = []
        for concept in validated:
            raw_term = concept.get("clinical_term", "")
            clean_term = raw_term.replace(" ", "_").lower()
            
            if clean_term not in self.graph:
                continue
                
            diag_hints = self.graph_builder.get_diagnosis_hints(clean_term)
            related = self.graph_builder.get_related_findings(clean_term)
            related = [r for r in related if r not in diag_hints]
            
            diag_str = ", ".join(diag_hints) if diag_hints else "no specific diagnoses"
            related_str = ", ".join(related[:3]) if related else "other clinical factors"
            
            contexts.append(
                f"Confirmed finding: {raw_term} (conf={concept.get('confidence', 0):.2f}) "
                f"is associated with {diag_str}. Related: {related_str}."
            )
            
        if not contexts:
            return "No confirmed pathological graph associations found."
        return " ".join(contexts)

if __name__ == "__main__":
    import sys
    import os
    # For testing without absolute path imports
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    
    from src.graph.graph_builder import ClinicalGraphBuilder
    import json
    
    print("Testing GraphRetriever...")
    builder = ClinicalGraphBuilder()
    
    dummy_concepts = [
        {
            "finding_id": "finding_001",
            "clinical_term": "pulmonary edema",
            "confidence": 0.9
        },
        {
            "finding_id": "finding_002",
            "clinical_term": "pleural effusion",
            "confidence": 0.8
        }
    ]
    
    # Add concepts to builder
    builder.build(dummy_concepts)
    
    retriever = GraphRetriever(builder)
    
    retrieved = retriever.retrieve(dummy_concepts, top_k=3)
    print("\nRetrieval Results (Top 3):")
    print(json.dumps(retrieved, indent=2))
    
    print("\nClinical Context Summary:")
    print(retriever.get_clinical_context(dummy_concepts))
