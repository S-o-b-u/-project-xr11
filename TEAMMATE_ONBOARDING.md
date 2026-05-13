# Project XR11 v2 — Teammate Onboarding Guide
### Distributed Multi-Agent Medical Report Generation System

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
7. [Running the Backend API](#7-running-the-backend-api)
8. [Running the Frontend](#8-running-the-frontend)
9. [Module Reference — What Each File Does](#9-module-reference--what-each-file-does)
10. [AI Agent Context Block](#10-ai-agent-context-block)

---

## 1. Project Overview & Context

**Project XR11 v2** is a highly advanced, enterprise-grade **Distributed Multi-Agent Radiology AI System**. It takes a chest X-ray image as input and automatically generates a structured clinical radiology report.

### The 12-Step Architecture

XR11 v2 has moved away from simple "send to LLM" wrappers. It uses a **12-step orchestration pipeline** combining localized medical models and Groq-powered multi-agent reasoning:

1. **Preprocessing (`EnhancedImageProcessor`)**: Normalizes images.
2. **Pathology Detection (`PathologyDetector`)**: Uses local `TorchXRayVision` to detect abnormalities natively without LLMs.
3. **Multimodal Embeddings (`EmbeddingEngine`)**: Uses `MedCLIP` to build visual representations.
4. **Concept Extraction**: Maps local CV results to standardized medical terms.
5. **Knowledge Graph (`ClinicalGraphBuilder`)**: Builds a dynamic network of related diagnoses using `networkx`.
6. **Hybrid Retrieval**: Queries FAISS using visual + semantic embeddings to find historical cases.
7. **Agentic Framing**: Three distinct agents (`AnatomyAgent`, `DiseaseAgent`, `RetrievalAgent`) analyze the data concurrently.
8. **Synthesis (`SynthesisAgent`)**: Uses Groq to synthesize all agent findings into a final clinical report.
9. **Logical Consistency (`ConsistencyAgent`)**: Ensures findings match impressions.
10. **Adaptive Uncertainty (`MCDropoutEstimator`)**: Uses Monte-Carlo dropout sampling on the TorchXRayVision model for confidence scoring (skipped if image is highly normal).
11. **Hallucination Verification (`CrossModalChecker`)**: Verifies LLM text against visual MedCLIP embeddings.
12. **Payload Delivery**: Delivers a highly structured payload to the Next.js frontend.

---

## 2. Tech Stack

| Layer | Technology |
|---|---|
| **Backend language** | Python 3.11 |
| **Backend framework** | FastAPI + Uvicorn |
| **Synthesis AI** | Groq API (Primary) + Gemini (Fallback) |
| **Local Medical AI** | `TorchXRayVision`, `MedCLIP`, `BioBERT`, `MiniLM-NLI` |
| **Vector search** | FAISS (`faiss-cpu`) |
| **Graphing** | `networkx` |
| **Frontend** | Next.js 16 + React 19 + TypeScript + TailwindCSS |
| **UI/UX** | "Kinetic Studio" Aesthetic, Framer Motion, Lenis Smooth Scroll |

---

## 3. Full Folder Structure

```
-project-xr11/
├── backend/
│   ├── .env                          <- API keys (NOT in repo)
│   ├── requirements.txt
│   ├── main.py                       <- FastAPI entry point
│   ├── data/
│   │   ├── raw/                      <- Images and datasets (NOT in repo)
│   │   └── processed/                <- dataset.json, visual_index.npy, faiss_index.bin
│   ├── src/
│   │   ├── agents/                   <- Anatomy, Disease, Retrieval, Synthesis, Consistency
│   │   ├── concepts/                 <- Concept extraction and clinical mapping
│   │   ├── evaluation/               <- BLEU/ROUGE scoring
│   │   ├── graph/                    <- Clinical knowledge graph builder
│   │   ├── medical_models/           <- Weights and local models
│   │   ├── model/                    <- report_generator.py (The 12-step orchestrator)
│   │   ├── preprocessing/            <- Image processors
│   │   ├── rag/                      <- FAISS Hybrid Retriever
│   │   ├── report/                   <- Structured report parsers
│   │   ├── uncertainty/              <- MCDropoutEstimator
│   │   ├── verification/             <- CrossModalChecker
│   │   └── vision/                   <- PathologyDetector (TorchXRayVision) & MedCLIP
│   └── venv/                         <- Python virtual environment
│
└── frontend/
    ├── src/
    │   ├── app/                      <- Next.js Pages (page.tsx, report/page.tsx)
    │   ├── components/               <- RetrievedCases, SmoothScroll, etc.
    ├── package.json
    └── tailwind.config.ts
```

---

## 4. What IS in the Repo vs What Is NOT

### In the Repo (you get this after `git clone`)
- All Python source code under `backend/src/` and `backend/main.py`.
- All frontend code under `frontend/`.

### NOT in the Repo (you must set up manually)
- `backend/.env` (Contains your Groq & Gemini API keys).
- `backend/data/raw/images/` (~7,470 IU X-ray PNGs).
- `backend/data/processed/dataset.json` and FAISS/MedCLIP indices.
- `backend/venv/` (Python virtual environment).

---

## 5. Step-by-Step Setup

1. **Clone the repository**
2. **Setup Backend Environment**:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # (Windows: venv\Scripts\activate)
   pip install -r requirements.txt
   ```
3. **Create the `.env` file** in `backend/`:
   ```
   GROQ_API_KEY=your_groq_key_here
   GEMINI_API_KEY=your_gemini_key_here
   ```
4. **Setup Frontend Environment**:
   ```bash
   cd ../frontend
   npm install
   ```

---

## 6. Data Setup (Manual — Not in Repo)

You will need the Indiana University (IU) Chest X-Ray Dataset indices and images.
Since they are large (~2GB), they must be manually placed or generated.

Ensure you have:
- `backend/data/processed/dataset.json`
- `backend/data/processed/faiss_index.bin`
- `backend/data/processed/visual_index.npy`

Without these files, the FAISS indices and Hybrid Retriever will fail to initialize.

---

## 7. Running the Backend API

```bash
cd backend
# Make sure venv is active
uvicorn main:app --reload --port 8000
```

> **Note**: The first startup triggers a lazy initialization thread. It loads TorchXRayVision, MedCLIP, FAISS, and the NetworkX graph. The API binds immediately, but processing your first request will wait until the models are loaded.

---

## 8. Running the Frontend

```bash
cd frontend
npm run dev
```
Available at: `http://localhost:3000`

---

## 9. Module Reference — What Each File Does

### `src/model/report_generator.py`
The absolute core of XR11 v2. Contains `XR11ReportGenerator.generate_report(image_path)`. It calls 12 separate modules sequentially, using adaptive routing to skip expensive tasks (like Monte-Carlo sampling) on healthy images.

### `src/vision/pathology_detector.py`
Uses local `TorchXRayVision` to output raw pathology presence probabilities (e.g., Cardiomegaly: 0.85). No LLM used here.

### `src/vision/embedding_engine.py`
Uses `MedCLIP` to encode the X-ray image into a dense semantic vector for similarity searches and hallucination checking.

### `src/graph/graph_builder.py`
Uses `networkx` to map the detected concepts into a clinical knowledge graph. Finds 2-hop logical relationships (e.g. *Opacity -> Consolidation -> Pneumonia*).

### `src/agents/synthesis_agent.py`
Takes all the data from the vision models, the RAG retrieved cases, and the graph context, and uses the **Groq API** to synthesize the final medical report at massive speed.

### `src/uncertainty/mc_dropout.py`
`MCDropoutEstimator`: Passes the image through the TorchXRayVision model multiple times with active dropout to measure variance and assign a strict `confidence` score.

### `src/verification/cross_modal_checker.py`
Embeds the generated text report and computes cosine similarity against the original image's `MedCLIP` embedding to mathematically prove the LLM isn't hallucinating.

---

## 10. AI Agent Context Block

**Copy and paste this entire block** into your AI assistant's system prompt to give it full project context before working on XR11 v2.

```text
PROJECT CONTEXT: XR11 v2 — Distributed Multi-Agent Radiology AI

TECH STACK:
- Backend: Python 3.11, FastAPI
- Primary Synthesis API: Groq API
- Fallback API: Gemini
- Local Models: TorchXRayVision (Pathology), MedCLIP (Vision Embeddings), BioBERT/MiniLM (Text/NLI)
- Graphing: NetworkX
- Vector Store: FAISS
- Frontend: Next.js 16, TypeScript, TailwindCSS, Lenis Smooth Scroll ("Kinetic Studio" Aesthetic)

ARCHITECTURE LOGIC (12-Step Pipeline found in src/model/report_generator.py):
1. Preprocessing (EnhancedImageProcessor)
2. Pathology Detection (TorchXRayVision) -> CV, NO LLM.
3. Multimodal Embedding (MedCLIP)
4. Concept Extraction & Mapping
5. Knowledge Graph Construction (NetworkX)
6. Hybrid Retrieval (FAISS + Visual Indices)
7. Concurrent Agentic Framing (Anatomy, Disease, Retrieval Agents)
8. Multi-Agent Synthesis (SynthesisAgent via Groq)
9. Logical Consistency Checking
10. Adaptive Uncertainty Quantification (MCDropoutEstimator) -> Skips if image is healthy.
11. Cross-Modal Hallucination Verification (MedCLIP Text-to-Image match)
12. Payload Delivery to Frontend

KEY DIRECTORIES:
- backend/src/model/report_generator.py (The Orchestrator)
- backend/src/agents/ (The LLM Agents)
- backend/src/vision/ (TorchXRayVision + MedCLIP)
- backend/src/graph/ (NetworkX)
- backend/src/uncertainty/ (MC Dropout)

FRONTEND LOGIC:
- app/page.tsx: Homepage, Light Theme (#F0EFED), uses mix-blend-mode "multiply" and filter "invert(1)" to make hero.png perfectly transparent.
- app/report/page.tsx: 3-column Bento Dashboard consuming the massive JSON payload generated by the 12-step pipeline.

IMPORTANT: The pipeline is highly modular and utilizes adaptive routing. Unrecoverable errors drop to a absolute legacy fallback in report_generator.py.
```
