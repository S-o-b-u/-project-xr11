"""
sampler.py
──────────
Monte-Carlo uncertainty estimation for radiology report generation.

Strategy
~~~~~~~~
The same prompt is sent to the VLM multiple times at a higher temperature
so that the stochastic decoding exposes genuine model uncertainty.  Two
complementary signals are computed:

1. **Severity vote entropy** — discrete uncertainty over the 4-class
   severity label (NORMAL / MILD / MODERATE / CRITICAL).
2. **Semantic variance** — mean pairwise cosine distance between all
   sampled report embeddings.  High variance means the model is producing
   qualitatively different reports, which is a strong uncertainty signal
   even when severity labels happen to agree.
"""

import math
import re

import numpy as np

# ── Severity labels (canonical order) ────────────────────────────────────────
_SEVERITY_LABELS = ["NORMAL", "MILD", "MODERATE", "CRITICAL"]
_SEVERITY_PATTERN = re.compile(
    r"SEVERITY:\s*(NORMAL|MILD|MODERATE|CRITICAL)", re.IGNORECASE
)
# Maximum possible Shannon entropy for 4 equal-probability classes
_MAX_ENTROPY = math.log2(4)


class UncertaintySampler:
    """Estimates model uncertainty via repeated stochastic sampling.

    Parameters
    ----------
    vlm_client : VLMClient
        An instance of our Gemini API wrapper that exposes
        ``generate(prompt, image_path, temperature=…)``.
    n_samples : int
        Number of independent samples to draw per analysis.
    temperature : float
        Sampling temperature forwarded to the VLM for all calls.
        Higher values increase output diversity and expose uncertainty.
    """

    def __init__(self, vlm_client, n_samples: int = 10, temperature: float = 0.7) -> None:
        self._client = vlm_client
        self.n_samples = n_samples
        self.temperature = temperature

    # ── Sampling ─────────────────────────────────────────────────────────────

    def sample(self, prompt: str, image_path: str) -> list[str]:
        """Call the VLM *n_samples* times and collect raw text responses.

        Parameters
        ----------
        prompt : str
            The radiologist prompt to send each time.
        image_path : str
            Path to the chest X-ray image.

        Returns
        -------
        list[str]
            List of *n_samples* raw response strings.
        """
        responses: list[str] = []
        for i in range(self.n_samples):
            print(f"[UncertaintySampler] Sample {i + 1}/{self.n_samples} …")
            text = self._client.generate(
                prompt, image_path, temperature=self.temperature
            )
            responses.append(text)
        return responses

    # ── Severity vote analysis ────────────────────────────────────────────────

    def extract_severities(self, samples: list[str]) -> dict:
        """Extract SEVERITY fields from all samples and compute vote statistics.

        Parameters
        ----------
        samples : list[str]
            Raw text responses from :meth:`sample`.

        Returns
        -------
        dict
            ``{votes, majority, entropy, confidence}``

            * ``votes``      — counts per severity class
            * ``majority``   — class with the highest vote count
            * ``entropy``    — Shannon entropy normalized to [0, 1]
                               (0 = fully certain, 1 = maximally uncertain)
            * ``confidence`` — ``1 - entropy``
        """
        votes = {label: 0 for label in _SEVERITY_LABELS}

        for text in samples:
            match = _SEVERITY_PATTERN.search(text)
            if match:
                label = match.group(1).upper()
                votes[label] = votes.get(label, 0) + 1
            # Unrecognised / missing SEVERITY → counted in no bucket (abstention)

        total_votes = sum(votes.values())

        # Majority severity
        majority = max(votes, key=lambda k: votes[k])

        # Shannon entropy (normalized by log2(4))
        if total_votes == 0:
            entropy = 1.0  # complete uncertainty if nothing was parseable
        else:
            proportions = [v / total_votes for v in votes.values() if v > 0]
            raw_entropy = -sum(p * math.log2(p) for p in proportions)
            entropy = raw_entropy / _MAX_ENTROPY  # normalize to [0, 1]

        confidence = 1.0 - entropy

        return {
            "votes": votes,
            "majority": majority,
            "entropy": round(entropy, 4),
            "confidence": round(confidence, 4),
        }

    # ── Semantic variance ─────────────────────────────────────────────────────

    def compute_semantic_variance(self, samples: list[str], embedder) -> float:
        """Measure how semantically spread the sampled reports are.

        Each sample is embedded; then we compute the mean pairwise cosine
        *distance* (1 − cosine similarity) across all unique pairs.

        Parameters
        ----------
        samples : list[str]
            Raw text responses from :meth:`sample`.
        embedder : ReportEmbedder
            Embedder instance (already loaded, provides ``embed_batch``).

        Returns
        -------
        float
            Mean pairwise cosine distance in [0, 1].
            High value → reports are diverse → high semantic uncertainty.
        """
        if len(samples) < 2:
            return 0.0

        # Shape: (N, 384), already L2-normalized
        embeddings = embedder.embed_batch(samples)

        # Cosine similarity matrix via inner product (normalized vectors)
        sim_matrix = embeddings @ embeddings.T  # (N, N)

        # Collect upper-triangle values (unique pairs, excluding diagonal)
        n = len(samples)
        upper_indices = np.triu_indices(n, k=1)
        similarities = sim_matrix[upper_indices]

        # Convert to cosine distance
        distances = 1.0 - similarities
        mean_distance = float(np.mean(distances))

        return round(mean_distance, 4)

    # ── Full analysis pipeline ────────────────────────────────────────────────

    def full_uncertainty_analysis(
        self, prompt: str, image_path: str, embedder
    ) -> dict:
        """Run the complete uncertainty estimation pipeline.

        Executes sampling, severity vote analysis, and semantic variance
        computation, then packages everything into a single result dict.

        Parameters
        ----------
        prompt : str
            The radiologist prompt to send to the VLM.
        image_path : str
            Path to the chest X-ray image.
        embedder : ReportEmbedder
            Embedder for semantic variance computation.

        Returns
        -------
        dict
            ``{samples, severity_votes, majority_severity, entropy,
               confidence, semantic_variance, needs_human_review}``

            * ``needs_human_review`` — ``True`` when entropy > 0.6
              OR confidence < 0.5, indicating the model is unsure.
        """
        print(f"[UncertaintySampler] Starting full uncertainty analysis "
              f"({self.n_samples} samples, T={self.temperature}) …")

        # 1 — Draw samples
        samples = self.sample(prompt, image_path)

        # 2 — Severity vote statistics
        severity_info = self.extract_severities(samples)

        # 3 — Semantic variance
        print("[UncertaintySampler] Computing semantic variance …")
        semantic_variance = self.compute_semantic_variance(samples, embedder)

        # 4 — Human-review flag
        needs_human_review = (
            severity_info["entropy"] > 0.6 or
            severity_info["confidence"] < 0.5
        )

        return {
            "samples": samples,
            "severity_votes": severity_info["votes"],
            "majority_severity": severity_info["majority"],
            "entropy": severity_info["entropy"],
            "confidence": severity_info["confidence"],
            "semantic_variance": semantic_variance,
            "needs_human_review": needs_human_review,
        }
