# Project XR11 v2 — Complete System Context

This document serves as the master architectural and contextual reference for **Project XR11 v2**, a highly advanced, enterprise-grade Distributed Multi-Agent Radiology AI System. It replaces the legacy VLM-only pipeline with a sophisticated 12-step orchestration workflow incorporating local medical models, dynamic knowledge graphs, and multi-agent synthesis.

---

## 1. Core Architecture & Tech Stack

### Backend: Distributed Multi-Agent Pipeline
- **Language**: Python 3.11
- **Framework**: FastAPI + Uvicorn
- **Orchestration**: Custom 12-step multi-agent orchestrator (`XR11ReportGenerator`)
- **Synthesis API**: Groq API (Primary fast synthesis) + Gemini (Fallback)
- **Local Medical Models**: 
  - **Pathology**: `TorchXRayVision`
  - **Embeddings**: `MedCLIP` (multimodal embedding)
  - **NLP/NLI**: `BioBERT` / `MiniLM-NLI`
- **Knowledge Graph**: `networkx` (Clinical nodes, relations, and paths)
- **Vector Search (RAG)**: `FAISS` with `IndexFlatIP` + `visual_index.npy` + `dataset.json`

### Frontend: Kinetic Studio
- **Framework**: Next.js 16 (App Router) + React 19
- **Language**: TypeScript + TailwindCSS + Framer Motion
- **Scroll Engine**: Lenis (Smooth hardware-accelerated scrolling)
- **Design Language**: "Kinetic Studio"
  - Light theme homepage (`#F0EFED`) with massive display typography ("REDEFINE IMAGING.") and inverted CSS trick for perfectly transparent 3D assets.
  - "Bento Grid" dashboard on the report page to visualize extreme data density.
  - Smooth, scale-less micro-interactions for buttons and hovers.

---

## 2. The 12-Step Multi-Agent Orchestration Workflow

When an image is uploaded (`POST /api/generate-report`), `report_generator.py` executes a dynamic 12-step pipeline with adaptive routing:

1. **Preprocessing (`EnhancedImageProcessor`)**
   - Normalizes and standardizes the input radiograph.
2. **Pathology Detection (`PathologyDetector` via TorchXRayVision)**
   - Runs a local computer vision pass to extract raw abnormality scores and positive pathology flags before any LLM is involved.
3. **Multimodal Embedding (`EmbeddingEngine` via MedCLIP)**
   - Generates a dense vector representation of the radiograph for cross-modal similarity search.
4. **Concept Extraction & Clinical Mapping (`ConceptExtractor` & `ClinicalMapper`)**
   - Maps the raw CV outputs to standardized clinical concepts and severity mappings.
5. **Dynamic Knowledge Graph (`ClinicalGraphBuilder` via NetworkX)**
   - Instantiates a localized subgraph of related medical terms based on the positive concepts found.
   - Retrieves multihop "diagnosis hints" (`GraphRetriever`).
6. **Hybrid Retrieval (`HybridClinicalRetriever`)**
   - Uses MedCLIP embeddings and text concepts to search FAISS and visual indices for the top 3 most similar historical cases from the IU Chest X-Ray dataset.
7. **Multi-Agent Framing (`AnatomyAgent`, `DiseaseAgent`, `RetrievalAgent`)**
   - Concurrent agentic reasoning. Each agent receives specialized context (e.g., AnatomyAgent maps findings to lung lobes, DiseaseAgent evaluates severity).
8. **Multi-Agent Synthesis (`SynthesisAgent` via Groq)**
   - Synthesizes the specialized agent outputs, hybrid retrieval data, and pathology scores into a cohesive, clinical-grade radiology report (Findings, Impression, Recommendations).
9. **Logical Consistency (`ConsistencyAgent`)**
   - Evaluates the synthesized text against the extracted medical concepts to ensure no contradictions exist.
10. **Adaptive Uncertainty Quantification (`MCDropoutEstimator`)**
   - **Adaptive Routing**: If the image is highly normal (`overall_abnormality_score < 0.2`), this heavy step is skipped.
   - If abnormal, runs Monte Carlo dropout sampling on the TorchXRayVision model to compute prediction variance and confidence levels.
11. **Cross-Modal Hallucination Verification (`CrossModalChecker`)**
   - Compares the MedCLIP embedding of the image against the text embedding of the generated report to detect visual-semantic hallucinations.
12. **Payload Structuring**
   - Assembles a massive JSON payload mapping `pathology`, `uncertainty`, `verification`, `retrieval`, and `agents` data for the frontend bento grid.

---

## 3. Key Upgrades from XR11 v1 to v2

1. **Agentic over Monolithic**: v1 relied entirely on Gemini 2.5 Flash to "look and write". v2 splits perception (TorchXRayVision) from reasoning (Anatomy/Disease Agents) and synthesis (Groq).
2. **MedCLIP over Sentence-Transformers**: v1 embedded text only. v2 natively embeds images using MedCLIP for true cross-modal RAG and hallucination checking.
3. **Graph Retrieval**: Added a `networkx` knowledge graph to trace relationships (e.g., *atelectasis* -> *left_lower_lobe*).
4. **Adaptive Routing**: The pipeline is smart enough to skip expensive MC Dropout steps on healthy patients, drastically reducing latency.

---

## 4. System Execution & Data Requirements

### Required Data (Not in Repo)
- `backend/data/processed/dataset.json` (3,955 cases)
- `backend/data/processed/faiss_index.bin` (FAISS vector store)
- `backend/data/processed/visual_index.npy` (MedCLIP visual index)
- `.env` containing `GROQ_API_KEY` and `GEMINI_API_KEY`

### Backend (`localhost:8000`)
```bash
cd backend
python -m venv venv
source venv/bin/activate  # (or venv\Scripts\activate on Windows)
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend (`localhost:3000`)
```bash
cd frontend
npm install
npm run dev
```
