"""
evaluator.py
────────────
Computes BLEU and ROUGE scores to evaluate generated radiology reports
against gold-standard references from the IU X-ray dataset.
"""

import logging
from typing import Any

import nltk
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from rouge_score import rouge_scorer

log = logging.getLogger(__name__)

# Download required NLTK data (safe to call repeatedly — skips if present)
try:
    nltk.data.find("tokenizers/punkt_tab")
except LookupError:
    nltk.download("punkt_tab", quiet=True)

try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt", quiet=True)


class Evaluator:
    """BLEU + ROUGE evaluator for radiology report quality assessment."""

    def __init__(self) -> None:
        self._rouge = rouge_scorer.RougeScorer(
            ["rouge1", "rouge2", "rougeL"], use_stemmer=True
        )
        self._smooth = SmoothingFunction().method4

    # ── Core metrics ──────────────────────────────────────────────────────────

    def compute_rouge(self, hypothesis: str, reference: str) -> dict:
        """Compute ROUGE-1, ROUGE-2, and ROUGE-L F1 scores.

        Parameters
        ----------
        hypothesis : str
            Generated text to evaluate.
        reference : str
            Gold-standard reference text.

        Returns
        -------
        dict
            ``{rouge1, rouge2, rougeL}`` — all F-measure floats in [0, 1].
        """
        if not hypothesis or not reference:
            return {"rouge1": 0.0, "rouge2": 0.0, "rougeL": 0.0}

        scores = self._rouge.score(reference, hypothesis)
        return {
            "rouge1": round(scores["rouge1"].fmeasure, 4),
            "rouge2": round(scores["rouge2"].fmeasure, 4),
            "rougeL": round(scores["rougeL"].fmeasure, 4),
        }

    def compute_bleu(self, hypothesis: str, reference: str) -> float:
        """Compute sentence-level BLEU-4 with smoothing.

        Parameters
        ----------
        hypothesis : str
            Generated text to evaluate.
        reference : str
            Gold-standard reference text.

        Returns
        -------
        float
            BLEU score in [0, 1].
        """
        if not hypothesis or not reference:
            return 0.0

        ref_tokens  = nltk.word_tokenize(reference.lower())
        hyp_tokens  = nltk.word_tokenize(hypothesis.lower())

        if not ref_tokens or not hyp_tokens:
            return 0.0

        score = sentence_bleu(
            [ref_tokens], hyp_tokens,
            smoothing_function=self._smooth,
        )
        return round(score, 4)

    # ── Single report evaluation ──────────────────────────────────────────────

    def evaluate_single(
        self,
        generated_report: dict,
        gold_findings:    str,
        gold_impression:  str,
    ) -> dict:
        """Score one generated report against its gold standard.

        Evaluates both the FINDINGS and IMPRESSION fields independently,
        then computes an overall average across all metrics.

        Parameters
        ----------
        generated_report : dict
            Parsed report dict with 'findings' and 'impression' keys.
        gold_findings : str
            Reference findings text from the dataset.
        gold_impression : str
            Reference impression text from the dataset.

        Returns
        -------
        dict
            Per-section and overall BLEU + ROUGE scores.
        """
        gen_findings   = generated_report.get("findings",   "")
        gen_impression = generated_report.get("impression", "")

        findings_rouge  = self.compute_rouge(gen_findings,   gold_findings)
        impression_rouge = self.compute_rouge(gen_impression, gold_impression)
        findings_bleu   = self.compute_bleu(gen_findings,   gold_findings)
        impression_bleu = self.compute_bleu(gen_impression, gold_impression)

        # Overall averages (findings + impression equally weighted)
        avg_bleu   = round((findings_bleu   + impression_bleu)   / 2, 4)
        avg_rouge1 = round((findings_rouge["rouge1"] + impression_rouge["rouge1"]) / 2, 4)
        avg_rouge2 = round((findings_rouge["rouge2"] + impression_rouge["rouge2"]) / 2, 4)
        avg_rougeL = round((findings_rouge["rougeL"] + impression_rouge["rougeL"]) / 2, 4)

        return {
            "findings": {
                "bleu":   findings_bleu,
                "rouge1": findings_rouge["rouge1"],
                "rouge2": findings_rouge["rouge2"],
                "rougeL": findings_rouge["rougeL"],
            },
            "impression": {
                "bleu":   impression_bleu,
                "rouge1": impression_rouge["rouge1"],
                "rouge2": impression_rouge["rouge2"],
                "rougeL": impression_rouge["rougeL"],
            },
            "overall": {
                "bleu":   avg_bleu,
                "rouge1": avg_rouge1,
                "rouge2": avg_rouge2,
                "rougeL": avg_rougeL,
            },
        }

    # ── Dataset-level evaluation ──────────────────────────────────────────────

    def evaluate_dataset(self, results_list: list[dict]) -> dict:
        """Compute mean scores across a list of single-report evaluations.

        Parameters
        ----------
        results_list : list[dict]
            Each element is the output of :meth:`evaluate_single`.

        Returns
        -------
        dict
            Average ``{bleu, rouge1, rouge2, rougeL}`` for findings,
            impression, and overall.
        """
        if not results_list:
            empty = {"bleu": 0.0, "rouge1": 0.0, "rouge2": 0.0, "rougeL": 0.0}
            return {"findings": empty, "impression": empty, "overall": empty}

        n = len(results_list)

        def _avg(section: str, metric: str) -> float:
            return round(
                sum(r[section][metric] for r in results_list if section in r) / n, 4
            )

        return {
            "findings": {
                "bleu":   _avg("findings",   "bleu"),
                "rouge1": _avg("findings",   "rouge1"),
                "rouge2": _avg("findings",   "rouge2"),
                "rougeL": _avg("findings",   "rougeL"),
            },
            "impression": {
                "bleu":   _avg("impression", "bleu"),
                "rouge1": _avg("impression", "rouge1"),
                "rouge2": _avg("impression", "rouge2"),
                "rougeL": _avg("impression", "rougeL"),
            },
            "overall": {
                "bleu":   _avg("overall",   "bleu"),
                "rouge1": _avg("overall",   "rouge1"),
                "rouge2": _avg("overall",   "rouge2"),
                "rougeL": _avg("overall",   "rougeL"),
            },
        }
