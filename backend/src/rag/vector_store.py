"""
vector_store.py
───────────────
FAISS-backed vector store for radiology report retrieval.

Uses IndexFlatIP (inner product) which equals cosine similarity when
vectors are L2-normalized (as ReportEmbedder guarantees).
"""

import pickle

import faiss
import numpy as np


class VectorStore:
    """Stores report embeddings in a FAISS flat inner-product index."""

    def __init__(self, dimension: int = 384) -> None:
        self._dim = dimension
        self._index = faiss.IndexFlatIP(dimension)
        self._metadata: list[dict] = []   # parallel to index rows

    # ------------------------------------------------------------------
    # Building the index
    # ------------------------------------------------------------------

    def add_reports(self, reports: list[dict], embedder) -> None:
        """Embed all reports and insert them into the FAISS index.

        Each report is embedded as a single string:
            "findings: <gold_findings> impression: <gold_impression>"

        Parameters
        ----------
        reports : list[dict]
            Dicts with at least ``gold_findings`` and ``gold_impression``.
        embedder : ReportEmbedder
            Embedder instance used to encode the texts.
        """
        if not reports:
            print("[VectorStore] No reports to add.")
            return

        texts = [
            f"findings: {r['gold_findings']} impression: {r['gold_impression']}"
            for r in reports
        ]

        print(f"[VectorStore] Embedding {len(texts)} reports …")
        embeddings = embedder.embed_batch(texts)  # (N, 384) float32, normalized

        self._index.add(embeddings)
        self._metadata.extend(reports)

        print(f"[VectorStore] Index now contains {self._index.ntotal} vectors.")

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, index_path: str, metadata_path: str) -> None:
        """Serialize the FAISS index and metadata to disk.

        Parameters
        ----------
        index_path : str
            File path for the FAISS index (``.bin``).
        metadata_path : str
            File path for the pickled metadata list (``.pkl``).
        """
        faiss.write_index(self._index, index_path)
        with open(metadata_path, "wb") as fp:
            pickle.dump(self._metadata, fp)
        print(f"[VectorStore] Saved index to {index_path}")
        print(f"[VectorStore] Saved metadata to {metadata_path}")

    def load(self, index_path: str, metadata_path: str) -> None:
        """Load a previously saved index and metadata from disk.

        Parameters
        ----------
        index_path : str
            File path of the FAISS index (``.bin``).
        metadata_path : str
            File path of the pickled metadata list (``.pkl``).
        """
        self._index = faiss.read_index(index_path)
        with open(metadata_path, "rb") as fp:
            self._metadata = pickle.load(fp)
        print(f"[VectorStore] Loaded {self._index.ntotal} vectors from {index_path}")

    # ------------------------------------------------------------------
    # Retrieval
    # ------------------------------------------------------------------

    def search(self, query_embedding: np.ndarray, k: int = 3) -> list[dict]:
        """Return the top-k most similar reports.

        Parameters
        ----------
        query_embedding : np.ndarray
            1-D float32 array of shape ``(384,)``, L2-normalized.
        k : int
            Number of results to return.

        Returns
        -------
        list[dict]
            Each dict is the original report dict with an added
            ``similarity_score`` key (cosine similarity, 0-1).
        """
        if self._index.ntotal == 0:
            return []

        k = min(k, self._index.ntotal)
        query = query_embedding.astype(np.float32).reshape(1, -1)
        scores, indices = self._index.search(query, k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
            entry = dict(self._metadata[idx])
            entry["similarity_score"] = float(score)
            results.append(entry)

        return results
