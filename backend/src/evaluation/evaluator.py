"""
evaluator.py
────────────
Computes evaluation metrics (BLEU, ROUGE, etc.) for generated
radiology reports against gold-standard references.

(Stub — will need nltk / rouge-score when implemented.)
"""

from __future__ import annotations


class Evaluator:
    """Evaluate generated reports against gold-standard text."""

    def evaluate_single(self, generated: str, gold: str) -> dict:
        """Return a dict of metric scores comparing *generated* to *gold*.

        Expected keys: bleu, rouge1, rouge2, rougeL
        """
        raise NotImplementedError(
            "Evaluator not yet implemented. "
            "Install nltk / rouge-score and implement scoring."
        )

    def evaluate_batch(
        self,
        generated_list: list[str],
        gold_list: list[str],
    ) -> dict:
        """Compute aggregate metrics over a batch of report pairs."""
        raise NotImplementedError("Batch evaluation not yet implemented.")
