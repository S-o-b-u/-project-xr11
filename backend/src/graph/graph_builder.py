"""
Module for building clinical knowledge graphs.
"""
import networkx as nx
from typing import List, Dict, Any

class ClinicalGraphBuilder:
    """
    Constructs a dynamic knowledge graph from extracted concepts and patient history.
    """
    
    def __init__(self):
        """
        Initializes the directed graph and populates the base RadLex nodes and edges.
        """
        self.graph = nx.DiGraph()
        self._build_radlex_graph()

    def _build_radlex_graph(self):
        """
        Manually adds nodes and edges representing chest radiology knowledge.
        """
        # Node groups
        findings = [
            "opacity", "atelectasis", "consolidation", "pleural_effusion", 
            "pneumothorax", "cardiomegaly", "pulmonary_edema", "emphysema", 
            "fibrosis", "pulmonary_nodule", "infiltrate", "pneumonia"
        ]
        anatomy = [
            "left_lung", "right_lung", "left_lower_lobe", "right_lower_lobe", 
            "left_upper_lobe", "right_upper_lobe", "heart", "pleural_space", "diaphragm"
        ]
        diagnoses = [
            "pneumonia_dx", "heart_failure", "copd", "lung_cancer", 
            "tuberculosis", "pulmonary_embolism"
        ]

        # Add Nodes
        for n in findings:
            self.graph.add_node(n, type="finding")
        for n in anatomy:
            self.graph.add_node(n, type="anatomy")
        for n in diagnoses:
            self.graph.add_node(n, type="diagnosis")

        # Add Edges
        edges = [
            ("opacity", "consolidation", "suggests"),
            ("opacity", "atelectasis", "suggests"),
            ("opacity", "pneumonia_dx", "suggests"),
            ("consolidation", "pneumonia_dx", "associated_with"),
            ("pleural_effusion", "heart_failure", "suggests"),
            ("pleural_effusion", "pneumonia_dx", "suggests"),
            ("cardiomegaly", "heart_failure", "indicates"),
            ("pulmonary_edema", "heart_failure", "indicates"),
            ("emphysema", "copd", "associated_with"),
            ("pulmonary_nodule", "lung_cancer", "warrants_workup"),
            ("atelectasis", "left_lower_lobe", "common_location"),
            ("atelectasis", "right_lower_lobe", "common_location"),
            ("pneumothorax", "pleural_space", "located_in"),
            ("infiltrate", "pneumonia_dx", "suggests"),
            ("fibrosis", "copd", "associated_with"),
            
            # 10 additional reasonable medical edges
            ("pneumonia", "consolidation", "causes"),
            ("heart_failure", "cardiomegaly", "causes"),
            ("heart_failure", "pulmonary_edema", "causes"),
            ("tuberculosis", "pulmonary_nodule", "associated_with"),
            ("lung_cancer", "pulmonary_nodule", "causes"),
            ("pulmonary_embolism", "pleural_effusion", "associated_with"),
            ("tuberculosis", "opacity", "suggests"),
            ("copd", "diaphragm", "flattens"),
            ("consolidation", "right_lower_lobe", "common_location"),
            ("cardiomegaly", "heart", "affects")
        ]

        for src, dst, rel in edges:
            self.graph.add_edge(src, dst, relation=rel)

    def build(self, concepts: List[Dict[str, Any]]) -> nx.DiGraph:
        """
        Adds ONLY validated positive concept nodes to the graph.
        
        Validated = present is True AND confidence > 0.6
        Negative or low-confidence concepts are excluded from graph traversal
        to prevent context pollution.
        
        Parameters
        ----------
        concepts : list of dict
            Full concept list (positive + negative).
            
        Returns
        -------
        nx.DiGraph
        """
        # Gate: only confirmed, high-confidence findings enter the graph
        validated_graph_concepts = [
            c for c in concepts
            if c.get("present") is True and c.get("confidence", 0.0) > 0.6
        ]
        excluded = [c.get("clinical_term", "") for c in concepts if c not in validated_graph_concepts]
        
        for concept in validated_graph_concepts:
            node_id = concept.get("finding_id", "unknown_concept")
            clinical_term = concept.get("clinical_term", "")
            clean_term = clinical_term.replace(" ", "_").lower()
            
            self.graph.add_node(node_id, type="concept", **concept)
            
            # Link the dynamic concept node to the static finding node if it exists
            if clean_term in self.graph.nodes:
                self.graph.add_edge(node_id, clean_term, relation="instance_of")
                
        return self.graph
    
    def build_debug_summary(self, concepts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Returns debug info about which concepts were admitted to or excluded from the graph."""
        validated = [c.get("clinical_term", "") for c in concepts
                     if c.get("present") is True and c.get("confidence", 0.0) > 0.6]
        excluded = [c.get("clinical_term", "") for c in concepts
                    if not (c.get("present") is True and c.get("confidence", 0.0) > 0.6)]
        return {"graph_admitted": validated, "graph_excluded_debug": excluded}

    def get_related_findings(self, finding: str) -> List[str]:
        """
        Returns a list of nodes reachable within 2 hops from the given finding node.
        """
        if finding not in self.graph:
            return []
        
        # Calculate lengths in undirected version to find neighbors easily
        lengths = nx.single_source_shortest_path_length(self.graph.to_undirected(), finding, cutoff=2)
        # Exclude the source finding itself (length 0)
        return [n for n, length in lengths.items() if length > 0]

    def get_diagnosis_hints(self, finding: str) -> List[str]:
        """
        Returns all nodes connected to finding with specific diagnostic relations.
        """
        if finding not in self.graph:
            return []
            
        hints = set()
        target_relations = {"suggests", "associated_with", "indicates", "causes"}
        
        # Look at outgoing edges
        for _, dst, data in self.graph.out_edges(finding, data=True):
            if data.get("relation") in target_relations:
                hints.add(dst)
                
        # Look at incoming edges (e.g. if 'pneumonia causes consolidation', then consolidation suggests pneumonia)
        for src, _, data in self.graph.in_edges(finding, data=True):
            if data.get("relation") in target_relations:
                hints.add(src)
                
        return list(hints)

    def export_graph_summary(self) -> Dict[str, Any]:
        """
        Returns a summary dictionary of the graph elements.
        """
        nodes = self.graph.nodes(data=True)
        finding_nodes = [n for n, d in nodes if d.get("type") == "finding"]
        anatomy_nodes = [n for n, d in nodes if d.get("type") == "anatomy"]
        diagnosis_nodes = [n for n, d in nodes if d.get("type") == "diagnosis"]
        
        return {
            "total_nodes": self.graph.number_of_nodes(),
            "total_edges": self.graph.number_of_edges(),
            "finding_nodes": finding_nodes,
            "anatomy_nodes": anatomy_nodes,
            "diagnosis_nodes": diagnosis_nodes
        }

if __name__ == "__main__":
    import json
    
    print("Testing ClinicalGraphBuilder...")
    builder = ClinicalGraphBuilder()
    
    dummy_concepts = [
        {
            "finding_id": "finding_001",
            "clinical_term": "pulmonary edema",
            "confidence": 0.9
        }
    ]
    
    builder.build(dummy_concepts)
    
    summary = builder.export_graph_summary()
    print("Graph Summary:")
    print(json.dumps({
        "total_nodes": summary["total_nodes"],
        "total_edges": summary["total_edges"],
        "sample_findings": summary["finding_nodes"][:5]
    }, indent=2))
    
    print("\nRelated to 'pulmonary_edema':", builder.get_related_findings("pulmonary_edema"))
    print("Diagnosis hints for 'pulmonary_edema':", builder.get_diagnosis_hints("pulmonary_edema"))
