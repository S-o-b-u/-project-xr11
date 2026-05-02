"""
build_index.py
──────────────
Standalone script: embed all reports in dataset.json and save
the FAISS index + metadata to disk.

Run from the backend/ directory:
    python scripts/build_index.py
"""

import json
import os
import sys

# Allow imports from backend/src/ when run directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.rag.embedder import ReportEmbedder
from src.rag.vector_store import VectorStore

DATASET_PATH   = os.path.join("data", "processed", "dataset.json")
INDEX_PATH     = os.path.join("data", "processed", "faiss_index.bin")
METADATA_PATH  = os.path.join("data", "processed", "faiss_metadata.pkl")


def main() -> None:
    # ── Load dataset ─────────────────────────────────────────────────────────
    if not os.path.isfile(DATASET_PATH):
        print(f"[ERROR] Dataset not found: {DATASET_PATH}")
        print("        Run scripts/build_dataset.py first.")
        sys.exit(1)

    with open(DATASET_PATH, "r", encoding="utf-8") as fp:
        dataset = json.load(fp)

    if not dataset:
        print("[ERROR] Dataset is empty – nothing to index.")
        sys.exit(1)

    print(f"[build_index] Loaded {len(dataset)} reports from {DATASET_PATH}")

    # ── Build embedder + store ────────────────────────────────────────────────
    embedder = ReportEmbedder()
    store    = VectorStore(dimension=ReportEmbedder.DIM)

    store.add_reports(dataset, embedder)

    # ── Persist ───────────────────────────────────────────────────────────────
    os.makedirs(os.path.dirname(INDEX_PATH), exist_ok=True)
    store.save(INDEX_PATH, METADATA_PATH)

    print(f"\nIndex built: {store._index.ntotal} vectors stored")
    print(f"  Index    → {INDEX_PATH}")
    print(f"  Metadata → {METADATA_PATH}")


if __name__ == "__main__":
    main()
