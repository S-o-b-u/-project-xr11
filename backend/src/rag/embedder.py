"""
embedder.py
───────────
Wraps sentence-transformers to produce normalized embeddings for
cosine-similarity search via FAISS IndexFlatIP.
"""

import numpy as np
from sentence_transformers import SentenceTransformer


class ReportEmbedder:
    """Embeds radiology report text using a lightweight MiniLM model.

    Embeddings are L2-normalized so that inner-product in FAISS equals
    cosine similarity.
    """

    MODEL_NAME = "all-MiniLM-L6-v2"
    DIM = 384

    def __init__(self) -> None:
        print(f"[Embedder] Loading model '{self.MODEL_NAME}' …")
        self._model = SentenceTransformer(self.MODEL_NAME)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def embed_text(self, text: str) -> np.ndarray:
        """Embed a single string.

        Parameters
        ----------
        text : str
            Input text to embed.

        Returns
        -------
        np.ndarray
            Float32 array of shape ``(384,)``, L2-normalized.
        """
        embedding = self._model.encode(text, convert_to_numpy=True)
        return self._normalize(embedding.reshape(1, -1)).squeeze(0)

    def embed_batch(self, texts: list[str]) -> np.ndarray:
        """Embed a list of strings in one forward pass.

        Parameters
        ----------
        texts : list[str]
            Input strings to embed.

        Returns
        -------
        np.ndarray
            Float32 array of shape ``(N, 384)``, each row L2-normalized.
        """
        embeddings = self._model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
        return self._normalize(embeddings)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize(matrix: np.ndarray) -> np.ndarray:
        """Row-wise L2 normalization."""
        matrix = matrix.astype(np.float32)
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        # Guard against zero-vectors
        norms = np.where(norms == 0, 1.0, norms)
        return matrix / norms
