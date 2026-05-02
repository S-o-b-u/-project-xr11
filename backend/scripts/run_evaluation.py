"""
run_evaluation.py
─────────────────
Runs the full AI pipeline on the first 10 dataset entries, computes BLEU
and ROUGE scores for Round 1 vs Round 2, and saves results to
backend/results/evaluation_scores.json.

IMPORTANT — Rate-limit safety:
  A 65-second sleep is inserted after every iteration to stay within
  Google Gemini free-tier quota limits (each iteration makes ~7 API calls).

Run from the backend/ directory:
    python scripts/run_evaluation.py
"""

import json
import os
import sys
import time

# Allow imports from backend/src/ when invoked directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.model.report_generator import ReportGenerator
from src.evaluation.evaluator import Evaluator

# ── Config ────────────────────────────────────────────────────────────────────
DATASET_PATH  = os.path.join("data", "processed", "dataset.json")
OUTPUT_PATH   = os.path.join("results", "evaluation_scores.json")
N_ENTRIES     = 10          # keep small to respect free-tier quota
SLEEP_SECONDS = 65          # pause between iterations (~7 API calls each)


def parse_raw_to_dict(raw_text: str) -> dict:
    """Convert round1_raw (unstructured string) into a findings/impression dict."""
    import re
    findings_m   = re.search(r"FINDINGS:\s*(.*?)(?:\nIMPRESSION:|\nSEVERITY:|$)",
                              raw_text, re.IGNORECASE | re.DOTALL)
    impression_m = re.search(r"IMPRESSION:\s*(.*?)(?:\nSEVERITY:|\nFOLLOW_UP:|$)",
                              raw_text, re.IGNORECASE | re.DOTALL)
    return {
        "findings":   findings_m.group(1).strip()   if findings_m   else "",
        "impression": impression_m.group(1).strip() if impression_m else "",
    }


def print_summary(r1_avg: dict, r2_avg: dict) -> None:
    """Print a formatted comparison table to stdout."""
    metrics = ["bleu", "rouge1", "rouge2", "rougeL"]
    header  = f"{'Metric':<12} {'Round 1':>10} {'Round 2':>10} {'Δ Improvement':>14}"
    sep     = "─" * len(header)

    print(f"\n{'═'*len(header)}")
    print("  EVALUATION SUMMARY  (Round 1 vs Round 2) — Overall averages")
    print(f"{'═'*len(header)}")
    print(header)
    print(sep)

    for m in metrics:
        r1_val = r1_avg["overall"].get(m, 0.0)
        r2_val = r2_avg["overall"].get(m, 0.0)
        delta  = r2_val - r1_val
        pct    = (delta / r1_val * 100) if r1_val > 0 else 0.0
        sign   = "+" if delta >= 0 else ""
        print(f"  {m.upper():<10} {r1_val:>10.4f} {r2_val:>10.4f} {sign}{pct:>12.1f}%")

    print(sep)
    print()


def main() -> None:
    # ── Load dataset ──────────────────────────────────────────────────────────
    if not os.path.isfile(DATASET_PATH):
        print(f"[ERROR] Dataset not found: {DATASET_PATH}")
        print("        Run scripts/build_dataset.py first.")
        sys.exit(1)

    with open(DATASET_PATH, "r", encoding="utf-8") as fp:
        dataset = json.load(fp)

    entries = dataset[:N_ENTRIES]
    print(f"[run_evaluation] Loaded dataset. Evaluating first {len(entries)} entries.")
    print(f"[run_evaluation] Estimated time: ~{len(entries) * SLEEP_SECONDS // 60} minutes "
          f"({SLEEP_SECONDS}s sleep per iteration to avoid rate limits)\n")

    # ── Initialise pipeline components ────────────────────────────────────────
    print("[run_evaluation] Initialising ReportGenerator …")
    generator = ReportGenerator()
    evaluator = Evaluator()

    r1_scores: list[dict] = []
    r2_scores: list[dict] = []
    all_results: list[dict] = []

    # ── Main evaluation loop ──────────────────────────────────────────────────
    for i, entry in enumerate(entries, start=1):
        image_path     = entry["image_path"]
        gold_findings  = entry["gold_findings"]
        gold_impression = entry["gold_impression"]

        print(f"\n{'─'*60}")
        print(f"[{i}/{len(entries)}] ID: {entry['id']}  |  {os.path.basename(image_path)}")
        print(f"  Gold impression: {gold_impression[:80]}…")

        result: dict = {}

        try:
            result = generator.generate_report(image_path)
        except Exception as exc:
            print(f"  [ERROR] generate_report failed: {exc}")

        # ── Score Round 1 ─────────────────────────────────────────────────────
        r1_dict  = parse_raw_to_dict(result.get("round1_raw", ""))
        r1_score = evaluator.evaluate_single(r1_dict, gold_findings, gold_impression)
        r1_scores.append(r1_score)

        print(f"  Round 1 → BLEU: {r1_score['overall']['bleu']:.4f} | "
              f"ROUGE-L: {r1_score['overall']['rougeL']:.4f}")

        # ── Score Round 2 (final report) ──────────────────────────────────────
        r2_score = evaluator.evaluate_single(
            result.get("final_report", {}), gold_findings, gold_impression
        )
        r2_scores.append(r2_score)

        print(f"  Round 2 → BLEU: {r2_score['overall']['bleu']:.4f} | "
              f"ROUGE-L: {r2_score['overall']['rougeL']:.4f}")

        # ── Store full record ─────────────────────────────────────────────────
        all_results.append({
            "id":               entry["id"],
            "image_path":       image_path,
            "gold_findings":    gold_findings,
            "gold_impression":  gold_impression,
            "round1_raw":       result.get("round1_raw",   ""),
            "round2_raw":       result.get("round2_raw",   ""),
            "final_report":     result.get("final_report", {}),
            "uncertainty":      result.get("uncertainty",  {}),
            "round1_scores":    r1_score,
            "round2_scores":    r2_score,
        })

        # ── Rate-limit sleep (skip after final iteration) ─────────────────────
        if i < len(entries):
            print(f"  [Rate-limit] Sleeping {SLEEP_SECONDS}s before next call …")
            time.sleep(SLEEP_SECONDS)

    # ── Aggregate averages ────────────────────────────────────────────────────
    r1_avg = evaluator.evaluate_dataset(r1_scores)
    r2_avg = evaluator.evaluate_dataset(r2_scores)

    # ── Save results ──────────────────────────────────────────────────────────
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    output = {
        "config": {
            "n_entries":     len(entries),
            "sleep_seconds": SLEEP_SECONDS,
        },
        "round1_average": r1_avg,
        "round2_average": r2_avg,
        "per_entry":       all_results,
    }
    with open(OUTPUT_PATH, "w", encoding="utf-8") as fp:
        json.dump(output, fp, indent=2, ensure_ascii=False)

    print(f"\n[run_evaluation] Results saved → {OUTPUT_PATH}")

    # ── Print summary table ───────────────────────────────────────────────────
    print_summary(r1_avg, r2_avg)


if __name__ == "__main__":
    main()
