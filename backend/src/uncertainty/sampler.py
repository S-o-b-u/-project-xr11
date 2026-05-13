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
    """Estimates model uncertainty based on provided text samples."""

    def __init__(self):
        pass

    # ── Severity vote analysis ────────────────────────────────────────────────

    def extract_severities(self, samples: list[str]) -> dict:
        """Extract SEVERITY fields from all samples and compute vote statistics."""
        votes = {label: 0 for label in _SEVERITY_LABELS}

        for text in samples:
            match = _SEVERITY_PATTERN.search(text)
            if match:
                label = match.group(1).upper()
                votes[label] = votes.get(label, 0) + 1

        total_votes = sum(votes.values())
        if total_votes == 0:
            majority = "UNKNOWN"
            entropy = 1.0
        else:
            majority = max(votes, key=lambda k: votes[k])
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
        """Measure how semantically spread the sampled reports are."""
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

    def calculate_metrics(self, samples: list[str], embedder) -> dict:
        """Run the complete uncertainty estimation pipeline on pre-generated samples."""
        print(f"[UncertaintySampler] Calculating metrics on {len(samples)} samples...")

        # 1 — Severity vote statistics
        severity_info = self.extract_severities(samples)

        # 2 — Semantic variance
        semantic_variance = self.compute_semantic_variance(samples, embedder)

        # 3 — Human-review flag
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
