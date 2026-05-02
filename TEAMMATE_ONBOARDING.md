# Project XR11 — Teammate Onboarding Guide
### Multimodal Medical Report Generation System

> **Written for:** New teammates joining the project after cloning the repo.  
> This guide covers everything — including files and data that are **NOT in the GitHub repo** and must be set up manually.

---

## Table of Contents

1. [Project Overview & Context](#1-project-overview--context)
2. [Tech Stack](#2-tech-stack)
3. [Full Folder Structure](#3-full-folder-structure)
4. [What IS in the Repo vs What Is NOT](#4-what-is-in-the-repo-vs-what-is-not)
5. [Step-by-Step Setup](#5-step-by-step-setup)
6. [Data Setup (Manual — Not in Repo)](#6-data-setup-manual--not-in-repo)
7. [Running the Scripts in Order](#7-running-the-scripts-in-order)
8. [Running the Backend API](#8-running-the-backend-api)
9. [Running the Frontend](#9-running-the-frontend)
10. [API Reference](#10-api-reference)
11. [Module Reference — What Each File Does](#11-module-reference--what-each-file-does)
12. [AI Agent Context Block](#12-ai-agent-context-block)

---

## 1. Project Overview & Context

**Project XR11** is an AI-powered **Multimodal Medical Report Generation** system. It takes a chest X-ray image as input and automatically generates a structured clinical radiology report using Google's **Gemini 2.5 Flash** multimodal large language model.

### What makes this system innovative (5 AI innovations)

This is NOT a simple "send image to GPT" wrapper. It has **5 distinct AI innovations** layered together:

| # | Innovation | What it does |
|---|---|---|
| 1 | **Two-Round VLM Generation** | Round 1 gives an initial report; Round 2 re-examines the image + Round 1 output to refine and catch errors |
| 2 | **RAG (Retrieval-Augmented Generation)** | Before generating, retrieves 3 similar historical X-ray reports from a FAISS vector index and injects them as few-shot context |
| 3 | **Monte-Carlo Uncertainty Quantification** | Sends the same prompt 5x at temperature 0.7, measures severity vote entropy and semantic variance to produce a confidence score and a `needs_human_review` flag |
| 4 | **Knowledge Graph Grounding** | Grounds report text against the RadLex radiology ontology (46,900 terms) and maps findings to ICD-10 clinical codes |
| 5 | **Hallucination Detection** | Sends the generated report + original image back to Gemini and asks it to verify each claim is visually supported |

### Dataset

We use the **Indiana University (IU) Chest X-Ray Dataset** — a public radiology dataset with:
- ~3,955 XML report files (findings + impression per patient)
- ~7,470 PNG chest X-ray images
- Images named like: `CXR1_1_IM-0001-3001.png`
- Reports named like: `1.xml`, `2.xml`, etc.
- The XML `<parentImage id="...">` tag links each report to its image

---

## 2. Tech Stack

| Layer | Technology |
|---|---|
| **Backend language** | Python 3.11 |
| **Backend framework** | FastAPI + Uvicorn |
| **AI model** | Google Gemini 2.5 Flash (`google-generativeai`) |
| **Vision/Image** | Pillow (PIL) |
| **Embeddings** | `sentence-transformers` — model `all-MiniLM-L6-v2` (384-dim) |
| **Vector search** | FAISS (`faiss-cpu`) — IndexFlatIP (cosine similarity) |
| **Ontology** | `owlready2` loading RadLex OWL file |
| **ICD-10** | `simple-icd-10` + hardcoded mapping |
| **NLI / Verification** | Gemini text-only calls |
| **Evaluation** | `rouge-score` + `nltk` sentence BLEU |
| **Frontend** | Next.js 16 + React 19 + TypeScript + TailwindCSS |
| **HTTP client (frontend)** | Axios |

---

## 3. Full Folder Structure

```
-project-xr11/
├── backend/
│   ├── .env                          <- API key (NOT in repo — create manually)
│   ├── .gitignore
│   ├── requirements.txt
│   ├── main.py                       <- FastAPI entry point
│   ├── test_full_pipeline.py         <- Quick end-to-end test script
│   │
│   ├── data/
│   │   ├── raw/
│   │   │   ├── images/               <- PNG X-rays (NOT in repo — download manually)
│   │   │   ├── reports/              <- XML reports (NOT in repo — download manually)
│   │   │   └── radlex.owl            <- RadLex ontology (NOT in repo — download manually)
│   │   └── processed/
│   │       ├── dataset.json          <- Built by build_dataset.py
│   │       ├── faiss_index.bin       <- Built by build_index.py
│   │       └── faiss_metadata.pkl    <- Built by build_index.py
│   │
│   ├── results/
│   │   └── evaluation_scores.json    <- Built by run_evaluation.py
│   │
│   ├── temp_uploads/                 <- Temp image storage during API calls
│   │
│   ├── scripts/
│   │   ├── build_dataset.py          <- Parses XMLs -> dataset.json
│   │   ├── build_index.py            <- Embeds dataset -> FAISS index
│   │   └── run_evaluation.py         <- BLEU/ROUGE evaluation on 10 samples
│   │
│   ├── src/
│   │   ├── __init__.py
│   │   ├── preprocessing/
│   │   │   ├── __init__.py
│   │   │   ├── report_parser.py      <- Parses XML, extracts parentImage id
│   │   │   └── image_processor.py    <- Opens + validates PNG images
│   │   ├── model/
│   │   │   ├── __init__.py
│   │   │   ├── vlm_client.py         <- Gemini API wrapper
│   │   │   ├── prompt_builder.py     <- All prompt templates
│   │   │   └── report_generator.py   <- Full 5-step pipeline orchestrator
│   │   ├── rag/
│   │   │   ├── __init__.py
│   │   │   ├── embedder.py           <- sentence-transformers wrapper
│   │   │   ├── vector_store.py       <- FAISS index management
│   │   │   └── retriever.py          <- RAG retriever + context formatter
│   │   ├── uncertainty/
│   │   │   ├── __init__.py
│   │   │   └── sampler.py            <- Monte-Carlo uncertainty sampler
│   │   ├── verification/
│   │   │   ├── __init__.py
│   │   │   ├── nli_checker.py        <- Logical consistency checker
│   │   │   ├── knowledge_graph.py    <- RadLex + ICD-10 grounding
│   │   │   └── hallucination_detector.py <- Claim verification vs image
│   │   └── evaluation/
│   │       ├── __init__.py
│   │       └── evaluator.py          <- BLEU + ROUGE scorer
│   │
│   └── venv/                         <- Python virtual environment (NOT in repo)
│
└── frontend/
    ├── src/                          <- Next.js app (pages, components)
    ├── public/
    ├── package.json
    ├── next.config.ts
    └── tsconfig.json
```

---

## 4. What IS in the Repo vs What Is NOT

### In the Repo (you get this after `git clone`)

- All Python source code under `backend/src/`
- All scripts under `backend/scripts/`
- `backend/main.py`, `backend/requirements.txt`, `backend/.gitignore`
- All frontend source code under `frontend/src/`
- `frontend/package.json` and all config files

### NOT in the Repo (you must set up manually)

| What | Why not in repo | How to get it |
|---|---|---|
| `backend/.env` | Contains secret API key | Create manually (see Step 5.3) |
| `backend/venv/` | Python environment | `python -m venv venv` |
| `backend/data/raw/images/` (~7,470 PNGs, ~2GB) | Too large for git | Download IU X-ray dataset (Section 6) |
| `backend/data/raw/reports/` (~3,955 XMLs) | Gitignored | Download IU X-ray dataset (Section 6) |
| `backend/data/raw/radlex.owl` (~65MB) | Too large for git | Download from radlex.org (Section 6) |
| `backend/data/processed/dataset.json` | Generated file | Run `build_dataset.py` |
| `backend/data/processed/faiss_index.bin` | Generated file | Run `build_index.py` |
| `backend/data/processed/faiss_metadata.pkl` | Generated file | Run `build_index.py` |
| `frontend/node_modules/` | npm packages | `npm install` |

---

## 5. Step-by-Step Setup

### 5.1 — Clone the repository

```bash
git clone <repo-url>
cd -project-xr11
```

### 5.2 — Create Python virtual environment

```bash
cd backend
python -m venv venv
```

Activate it:
- **Windows:** `venv\Scripts\activate`
- **Mac/Linux:** `source venv/bin/activate`

You should see `(venv)` in your terminal prompt.

### 5.3 — Create the `.env` file

Create a file called `.env` inside the `backend/` folder:

```
GEMINI_API_KEY=your_api_key_here
```

Get your API key from https://aistudio.google.com/app/apikey  
The free tier gives 15 requests/minute and 1,500 requests/day.  
Do NOT commit this file — it is already in `.gitignore`.

### 5.4 — Install Python dependencies

```bash
pip install -r requirements.txt
```

This installs all 17 packages including `torch`, `sentence-transformers`, and `faiss-cpu`.

> `torch` is large (~2GB). The first install will take a while on a slow connection.

### 5.5 — Install frontend dependencies

```bash
cd ../frontend
npm install
```

---

## 6. Data Setup (Manual — Not in Repo)

These steps MUST be completed before any scripts will work.

### 6.1 — Download the IU X-Ray Dataset

1. Go to: https://openi.nlm.nih.gov/faq#collection
2. Download the two files:
   - **NLMCXR_png.tgz** — the chest X-ray PNG images (~2GB)
   - **NLMCXR_reports.tgz** — the XML report files
3. Extract them:
   - Place all `.png` files into: `backend/data/raw/images/`
   - Place all `.xml` files into: `backend/data/raw/reports/`

Image naming example: `CXR1_1_IM-0001-3001.png`  
Report naming example: `1.xml`

> The XML contains `<parentImage id="CXR1_1_IM-0001-3001">` which links the report to its image. Our parser uses this id — NOT the XML filename.

### 6.2 — Download RadLex Ontology

1. Go to: https://www.radlex.org/download/
2. Download the **OWL format** file (`radlex.owl`)
3. Place it at: `backend/data/raw/radlex.owl`

> File size is ~65MB. It contains 46,900 radiology concepts used for medical term grounding.

---

## 7. Running the Scripts in Order

All scripts must be run from the `backend/` directory with `(venv)` active.

```bash
cd backend
# make sure (venv) is active
```

### Step 1 — Build the dataset (one-time, ~30 seconds)

```bash
python scripts/build_dataset.py
```

- Reads all XMLs from `data/raw/reports/`
- Extracts `<parentImage id>` to find the matching PNG
- Filters reports with trivial/missing text (< 20 chars, or just "xxxx")
- Saves `data/processed/dataset.json` (3,331 valid entries)
- Prints: `Built dataset: 3331 valid cases from 3955 total XML files`

### Step 2 — Build the FAISS vector index (one-time, ~2 minutes)

```bash
python scripts/build_index.py
```

- Loads `dataset.json`
- Downloads `all-MiniLM-L6-v2` from HuggingFace (first run only, ~80MB)
- Embeds all 3,331 reports into 384-dim vectors
- Saves `data/processed/faiss_index.bin` and `data/processed/faiss_metadata.pkl`
- Prints: `Index built: 3331 vectors stored`

### Step 3 — Quick pipeline test (optional but recommended)

```bash
python test_full_pipeline.py
```

- Grabs the first entry from `dataset.json`
- Runs the full 5-step AI pipeline
- Prints RAG context, uncertainty analysis, and the final structured report
- Makes ~7 Gemini API calls — takes ~30 seconds

### Step 4 — Run the evaluation suite (optional, ~12 minutes total)

```bash
python scripts/run_evaluation.py
```

- Evaluates the first 10 dataset entries
- Computes BLEU + ROUGE scores for Round 1 vs Round 2
- **Sleeps 65 seconds between each iteration** to avoid hitting free-tier rate limits
- Saves results to `results/evaluation_scores.json`
- Prints a comparison table at the end

---

## 8. Running the Backend API

```bash
cd backend
uvicorn main:app --reload --port 8000
```

Available at: http://localhost:8000

Endpoints:
- `GET /` — status check
- `GET /health` — health check
- `POST /api/generate-report` — accepts image file, returns full report
- `POST /api/evaluate` — accepts generated + gold text, returns BLEU/ROUGE

> The first startup takes ~30 seconds because it loads the embedding model and FAISS index into memory.

---

## 9. Running the Frontend

```bash
cd frontend
npm run dev
```

Available at: http://localhost:3000

The frontend calls the backend at `http://localhost:8000`. Make sure the backend is running first.

---

## 10. API Reference

### `POST /api/generate-report`

Upload a chest X-ray image and receive a fully structured medical report.

**Request:** `multipart/form-data` with field `file` (PNG or JPG)

**Response:**
```json
{
  "status": "success",
  "data": {
    "final_report": {
      "findings":   "The cardiomediastinal silhouette is within normal limits...",
      "impression": "No acute cardiopulmonary abnormality.",
      "severity":   "NORMAL",
      "follow_up":  "Routine follow-up.",
      "deviations": "None"
    },
    "round1_raw": "FINDINGS: ...\nIMPRESSION: ...",
    "round2_raw": "FINDINGS: ...\nIMPRESSION: ..."
  }
}
```

---

## 11. Module Reference — What Each File Does

### `src/model/vlm_client.py`
Wraps `google.generativeai`. Two methods:
- `generate(prompt, image_path, temperature=0.3)` — multimodal (image + text)
- `generate_text_only(prompt, temperature=0.3)` — text only (alias: `generate_no_image`)

### `src/model/prompt_builder.py`
All prompt templates in one place:
- `build_round1_prompt(rag_context="")` — initial radiologist prompt with optional RAG block
- `build_round2_prompt(preliminary_report)` — refinement prompt with DEVIATIONS field
- `build_nli_prompt(findings, impression, severity)` — consistency checker
- `build_hallucination_prompt(report_text)` — claim verification

### `src/model/report_generator.py`
Main orchestrator. `generate_report(image_path)` runs the full 5-step pipeline and returns:
```
{final_report, round1_raw, round2_raw, retrieved_cases, uncertainty, rag_context_used}
```

### `src/rag/embedder.py`
`ReportEmbedder` using `all-MiniLM-L6-v2`. L2-normalized 384-dim vectors.  
Methods: `embed_text(text)` -> `(384,)`, `embed_batch(texts)` -> `(N, 384)`

### `src/rag/vector_store.py`
`VectorStore` using `faiss.IndexFlatIP`.  
Methods: `add_reports()`, `save(index_path, meta_path)`, `load(index_path, meta_path)`, `search(query_embedding, k=3)`

### `src/rag/retriever.py`
`RAGRetriever` — high-level wrapper.  
`retrieve(query_text, k=3)` -> list of similar report dicts with similarity_score.  
`format_context(cases)` -> LLM-ready numbered string.

### `src/uncertainty/sampler.py`
`UncertaintySampler` with `n_samples=5`, `temperature=0.7`.  
`full_uncertainty_analysis(prompt, image_path, embedder)` returns:
```
{samples, severity_votes, majority_severity, entropy, confidence, semantic_variance, needs_human_review}
```

### `src/verification/nli_checker.py`
`NLIChecker` — text-only Gemini call to verify logical consistency.  
Returns: `{nli_result, severity_check, contradictions, consistency_score}`

### `src/verification/knowledge_graph.py`
`KnowledgeGraphGrounder` — loads RadLex OWL (46,900 terms) via `owlready2`.  
`ground_report(findings, impression)` returns:
```
{terms_found, radlex_matches, unmatched_terms, icd10_codes, standardization_rate}
```

### `src/verification/hallucination_detector.py`
`HallucinationDetector` — sends report + image back to Gemini for per-claim verification.  
Returns: `{claim_verifications, overall_risk, hallucination_score, uncertainty_score, safe_to_use}`

### `src/evaluation/evaluator.py`
`Evaluator` — BLEU-4 (NLTK, smoothing method4) + ROUGE-1/2/L (rouge-score, stemmed).  
Methods: `compute_bleu()`, `compute_rouge()`, `evaluate_single()`, `evaluate_dataset()`

### `src/preprocessing/report_parser.py`
- `parse_report(xml_path)` — extracts findings, impression, and `image_id` from XML
- `build_dataset(reports_dir, images_dir, output_path)` — builds `dataset.json`

### `src/preprocessing/image_processor.py`
- `preprocess_image(image_path)` — opens PNG, converts to RGB, returns PIL Image at original resolution
- `validate_image(image_path)` — checks file exists and is valid PNG/JPEG

---

## 12. AI Agent Context Block

**Copy and paste this entire block** into your AI assistant's system prompt or first message to give it full project context before working on XR11.

---

```
PROJECT CONTEXT: XR11 — Multimodal Medical Report Generation System

TECH STACK:
- Backend: Python 3.11, FastAPI, Uvicorn
- AI Model: Google Gemini 2.5 Flash (google-generativeai library)
- Embeddings: sentence-transformers, model "all-MiniLM-L6-v2" (384-dim, L2-normalized)
- Vector DB: FAISS IndexFlatIP (faiss-cpu) — inner product = cosine on normalized vectors
- Ontology: owlready2 loading RadLex OWL (46,900 radiology terms)
- ICD-10: simple-icd-10 + hardcoded 30-entry mapping dict in knowledge_graph.py
- Evaluation: rouge-score (ROUGE-1/2/L, stemmed), nltk sentence_bleu (method4 smoothing)
- Frontend: Next.js 16, React 19, TypeScript, TailwindCSS, Axios

DATASET:
- Indiana University (IU) Chest X-Ray dataset
- ~3,331 valid report/image pairs after filtering
- XMLs named: 1.xml, 2.xml, etc.
- PNGs named: CXR1_1_IM-0001-3001.png (does NOT match the XML filename)
- Image matching: extract <parentImage id="..."> attribute from XML, look for {id}.png
- Processed into: backend/data/processed/dataset.json
  Fields per entry: {id, image_path, gold_findings, gold_impression}

KEY ARCHITECTURE DECISIONS:
1. Image matching uses the <parentImage id> XML attribute, NOT the XML filename stem
2. Embeddings are L2-normalized so FAISS inner product equals cosine similarity
3. RadLex OWL is loaded on Windows via:
   get_ontology("http://radlex.org/").load(fileobj=open(radlex_path, "rb"))
   The file:/// URI path does NOT work on Windows — always use fileobj
4. VLMClient has two call types:
   - generate(prompt, image_path, temperature=0.3)      -> multimodal
   - generate_text_only(prompt, temperature=0.3)        -> text only
   - generate_no_image is an alias for generate_text_only

MODULE STRUCTURE (all under backend/src/):
  model/vlm_client.py           Gemini API wrapper
  model/prompt_builder.py       all prompt templates (round1, round2, nli, hallucination)
  model/report_generator.py     5-step pipeline orchestrator
  rag/embedder.py               ReportEmbedder (sentence-transformers)
  rag/vector_store.py           VectorStore (FAISS IndexFlatIP)
  rag/retriever.py              RAGRetriever.retrieve() + format_context()
  uncertainty/sampler.py        UncertaintySampler — Monte-Carlo severity entropy + semantic variance
  verification/nli_checker.py   NLIChecker — logical consistency (text-only Gemini)
  verification/knowledge_graph.py  KnowledgeGraphGrounder — RadLex + ICD-10
  verification/hallucination_detector.py  HallucinationDetector — claim verification vs image
  evaluation/evaluator.py       Evaluator — BLEU + ROUGE
  preprocessing/report_parser.py    parse_report(), build_dataset()
  preprocessing/image_processor.py  preprocess_image(), validate_image()

SCRIPTS (run from backend/ with venv active):
  python scripts/build_dataset.py     creates data/processed/dataset.json
  python scripts/build_index.py       creates faiss_index.bin + faiss_metadata.pkl
  python scripts/run_evaluation.py    evaluates 10 samples (65s sleep between each)
  python test_full_pipeline.py        end-to-end test on first dataset entry

FastAPI ENDPOINTS (localhost:8000):
  POST /api/generate-report   multipart image upload -> full report dict
  POST /api/evaluate          {generated, gold} -> BLEU/ROUGE scores
  GET  /health                health check

PIPELINE FLOW — generate_report(image_path):
  Step 1: RAG — embed "chest x-ray analysis {filename}", retrieve top-3 from FAISS
  Step 2: Uncertainty — 5 Monte-Carlo samples at T=0.7 -> severity entropy + semantic variance
  Step 3: Round 1 — build_round1_prompt(rag_context) -> vlm_client.generate(T=0.3)
  Step 4: Round 2 — build_round2_prompt(round1_raw) -> vlm_client.generate(T=0.2) -> parse
  Step 5: Assemble {final_report, round1_raw, round2_raw, retrieved_cases, uncertainty, rag_context_used}
  Each step has its own try/except — a failure in one step never crashes the pipeline

STRUCTURED OUTPUT FORMAT (LLM output parsed by regex):
  FINDINGS:   [text]
  IMPRESSION: [text]
  SEVERITY:   [NORMAL | MILD | MODERATE | CRITICAL]
  FOLLOW_UP:  [text]
  DEVIATIONS: [text]  (Round 2 only)

FILES NOT IN THE GIT REPO (must be set up manually by each teammate):
  backend/.env                                GEMINI_API_KEY=...
  backend/data/raw/images/*.png               IU X-ray PNGs (~7,470 files, ~2GB)
  backend/data/raw/reports/*.xml              IU X-ray XMLs (~3,955 files)
  backend/data/raw/radlex.owl                 RadLex OWL ontology (~65MB)
  backend/data/processed/dataset.json         generated by build_dataset.py
  backend/data/processed/faiss_index.bin      generated by build_index.py
  backend/data/processed/faiss_metadata.pkl   generated by build_index.py

KNOWN GOTCHAS:
  - google-generativeai shows a FutureWarning — ignore it, library still works
  - RadLex MUST be loaded with fileobj= on Windows, not file:/// URI
  - Gemini free tier: ~15 req/min; run_evaluation.py sleeps 65s between iterations
  - If you change dataset.json, you must rebuild the FAISS index
  - VLMClient uses "gemini-2.5-flash" — do not change to 1.5-flash (deprecated)
  - UncertaintySampler uses n_samples=5 (not 10) to respect rate limits
```

---

*Document written: 2 May 2026. Maintainer: Souvik Rahut.*
