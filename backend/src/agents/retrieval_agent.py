"""
Module for the Retrieval Agent.
"""
from typing import List, Dict, Any
import numpy as np

class RetrievalAgent:
    """
    Agent responsible for querying external databases or the knowledge graph for context.
    """
    
    def __init__(self, dataset_path: str, faiss_index_path: str, graph_builder, visual_index_path: str = None):
        """
        Sets up the text/visual and graph retrievers.
        """
        self.hybrid_retriever = None
        self.graph_retriever = None
        
        try:
            from src.rag.hybrid_retriever import HybridClinicalRetriever
            from src.graph.graph_retriever import GraphRetriever
            
            self.hybrid_retriever = HybridClinicalRetriever(dataset_path, faiss_index_path, visual_index_path)
            self.graph_retriever = GraphRetriever(graph_builder)
        except ImportError as e:
            print(f"RetrievalAgent initialization warning: {e}")

    def run(self, image_embedding: np.ndarray, concepts: List[Dict[str, Any]], top_k: int = 3) -> Dict[str, Any]:
        """
        Executes the agent's retrieval strategy.
        
        Parameters
        ----------
        image_embedding : np.ndarray
        concepts : list of dict
        top_k : int
        
        Returns
        -------
        dict
            Fused context retrieved from RAG and Knowledge Graph.
        """
        vector_results = []
        if self.hybrid_retriever:
            vector_results = self.hybrid_retriever.retrieve(
                query_image_embedding=image_embedding,
                query_concepts=concepts,
                top_k=top_k
            )
            
        graph_results = []
        graph_context_str = ""
        if self.graph_retriever:
            graph_results = self.graph_retriever.retrieve(concepts, top_k=top_k)
            graph_context_str = self.graph_retriever.get_clinical_context(concepts)
            
        top_case_report = ""
        if vector_results:
            top_case_report = vector_results[0].get("report_text", "")
            
        # Combine context: max 2 reports + graph context
        reports_text = []
        for v in vector_results[:2]:
            r_text = v.get("report_text", "")
            if r_text:
                reports_text.append(r_text)
                
        combined_text = " ".join(reports_text) + " " + graph_context_str
        combined_context = combined_text[:500] if len(combined_text) > 500 else combined_text
        
        return {
            "agent": "RetrievalAgent",
            "vector_results": vector_results,
            "graph_results": graph_results,
            "combined_context": combined_context,
            "top_case_report": top_case_report,
            "retrieval_count": len(vector_results) + len(graph_results)
        }

if __name__ == "__main__":
    import json
    import sys, os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    
    from src.graph.graph_builder import ClinicalGraphBuilder
    
    print("Testing RetrievalAgent...")
    gb = ClinicalGraphBuilder()
    agent = RetrievalAgent("dummy.json", "dummy.index", gb)
    
    dummy_emb = np.random.rand(128).astype(np.float32)
    dummy_concepts = [{"clinical_term": "atelectasis", "present": True, "confidence": 0.8}]
    
    res = agent.run(dummy_emb, dummy_concepts)
    print(json.dumps(res, indent=2))
