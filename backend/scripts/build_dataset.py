"""
build_dataset.py
────────────────
Standalone script to build dataset.json from raw IU X-ray data.

Run from the backend/ directory:
    python scripts/build_dataset.py
"""

import json
import os
import sys

# Allow imports from backend/src/ when run directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.preprocessing.report_parser import build_dataset

REPORTS_DIR = os.path.join("data", "raw", "reports")
IMAGES_DIR  = os.path.join("data", "raw", "images")
OUTPUT_PATH = os.path.join("data", "processed", "dataset.json")


def main() -> None:
    # Basic sanity checks
    if not os.path.isdir(REPORTS_DIR):
        print(f"[ERROR] Reports directory not found: {REPORTS_DIR}")
        sys.exit(1)
    if not os.path.isdir(IMAGES_DIR):
        print(f"[ERROR] Images directory not found: {IMAGES_DIR}")
        sys.exit(1)

    dataset = build_dataset(REPORTS_DIR, IMAGES_DIR, OUTPUT_PATH)

    # Preview first 3 entries
    if dataset:
        print("\n--- Preview (first 3 entries) -----------------------------------------")
        preview = dataset[:3]
        print(json.dumps(preview, indent=2, ensure_ascii=False))
    else:
        print("[WARN] Dataset is empty – check your reports and images directories.")


if __name__ == "__main__":
    main()
