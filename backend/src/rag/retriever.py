"""
retriever.py
────────────
High-level RAG retriever that combines ReportEmbedder + VectorStore
to find similar historical radiology cases for few-shot prompting.
"""

from .embedder import ReportEmbedder
from .vector_store import VectorStore


class RAGRetriever:
    """Retrieves similar radiology reports and formats them for LLM prompts."""

    def __init__(self, vector_store: VectorStore, embedder: ReportEmbedder) -> None:
        self._store = vector_store
        self._embedder = embedder

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def retrieve(self, query_text: str, k: int = 3) -> list[dict]:
        """Find the k most similar reports to *query_text*.

        Parameters
        ----------
        query_text : str
            Free-form text describing the X-ray (e.g. the prompt or a
            preliminary findings summary).
        k : int
            Number of similar cases to retrieve.

        Returns
        -------
        list[dict]
            Each dict contains:
            ``{gold_findings, gold_impression, similarity_score, …}``
            (the full metadata dict plus similarity_score).
        """
        query_embedding = self._embedder.embed_text(query_text)
        return self._store.search(query_embedding, k=k)

    # ------------------------------------------------------------------
    # Prompt formatting
    # ------------------------------------------------------------------

    def format_context(self, retrieved_cases: list[dict]) -> str:
        """Format retrieved cases as a readable context block for the LLM.

        Parameters
        ----------
        retrieved_cases : list[dict]
            Output of :meth:`retrieve`.

        Returns
        -------
        str
            Multi-line string ready to be injected into a prompt, e.g.::

                Similar case 1:
                FINDINGS: The heart size is normal ...
                IMPRESSION: No acute cardiopulmonary abnormality.
                ---
                Similar case 2:
                ...
        """
        if not retrieved_cases:
            return "No similar cases found."

        blocks = []
        for i, case in enumerate(retrieved_cases, start=1):
            score = case.get("similarity_score", 0.0)
            block = (
                f"Similar case {i} (similarity: {score:.3f}):\n"
                f"FINDINGS: {case.get('gold_findings', 'N/A')}\n"
                f"IMPRESSION: {case.get('gold_impression', 'N/A')}\n"
                f"---"
            )
            blocks.append(block)

        return "\n".join(blocks)
