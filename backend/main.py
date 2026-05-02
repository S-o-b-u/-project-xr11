"""
main.py
────────
FastAPI application for the XR11 Multimodal Medical Report Generation system.

All heavy components (ReportGenerator, Evaluator) are initialised ONCE at
server startup as module-level singletons so per-request latency is minimal.

Endpoints
---------
GET  /                    → status + version
GET  /health              → alive check
GET  /api/stats           → dataset + index sizes
POST /api/generate-report → full 6-step AI pipeline
POST /api/evaluate        → BLEU + ROUGE scorer
"""

import json
import logging
import os
import shutil
import time
import uuid
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
log = logging.getLogger("xr11.api")

# ── Paths ──────────────────────────────────────────────────────────────────────
_BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
_DATASET_PATH  = os.path.join(_BASE_DIR, "data", "processed", "dataset.json")
_INDEX_PATH    = os.path.join(_BASE_DIR, "data", "processed", "faiss_index.bin")
_TEMP_DIR      = os.path.join(_BASE_DIR, "temp_uploads")
os.makedirs(_TEMP_DIR, exist_ok=True)

# ── Pydantic schemas ───────────────────────────────────────────────────────────

class FinalReport(BaseModel):
    findings:   str = ""
    impression: str = ""
    severity:   str = "UNKNOWN"
    follow_up:  str = ""
    deviations: str = ""


class RetrievedCase(BaseModel):
    id:               str   = ""
    gold_findings:    str   = ""
    gold_impression:  str   = ""
    similarity_score: float = 0.0


class UncertaintyMetrics(BaseModel):
    majority_severity:  Optional[str]   = None
    entropy:            Optional[float] = None
    confidence:         Optional[float] = None
    semantic_variance:  Optional[float] = None
    needs_human_review: Optional[bool]  = None


class NLIResult(BaseModel):
    nli_result:        str   = "NEUTRAL"
    severity_check:    str   = "APPROPRIATE"
    contradictions:    str   = ""
    consistency_score: float = 0.5


class KGResult(BaseModel):
    terms_found:          List[str]      = []
    radlex_matches:       List[Dict]     = []
    unmatched_terms:      List[str]      = []
    icd10_codes:          List[Dict]     = []
    standardization_rate: float         = 0.0


class HallucinationResult(BaseModel):
    claim_verifications: List[Dict] = []
    overall_risk:        str        = "MEDIUM"
    hallucination_score: float      = 0.5
    uncertainty_score:   float      = 0.5
    safe_to_use:         bool       = False


class GenerateReportResponse(BaseModel):
    status: str
    data:   Dict[str, Any]


class EvaluateRequest(BaseModel):
    generated: Dict[str, Any]
    gold:      Dict[str, str]


class RougeScores(BaseModel):
    rouge1: float
    rouge2: float
    rougeL: float


class SectionScores(BaseModel):
    bleu:   float
    rouge1: float
    rouge2: float
    rougeL: float


class EvaluateResponse(BaseModel):
    status:  str
    scores:  Dict[str, SectionScores]


class StatsResponse(BaseModel):
    dataset_size: int
    index_size:   int


# ── Request logging middleware ─────────────────────────────────────────────────

class RequestLogMiddleware(BaseHTTPMiddleware):
    """Logs every request: method, path, status code, and elapsed time."""

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed = time.perf_counter() - start
        log.info(
            "%s %s → %d in %.1fs",
            request.method,
            request.url.path,
            response.status_code,
            elapsed,
        )
        return response


# ── App & middleware setup ─────────────────────────────────────────────────────

app = FastAPI(
    title="XR11 — Medical Report Generation API",
    description="Multimodal AI pipeline for automated radiology report generation.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLogMiddleware)


# ── Singleton components (initialised at startup) ──────────────────────────────

generator = None
evaluator = None


@app.on_event("startup")
async def startup_event():
    """Initialise all heavy components once so requests are fast."""
    global generator, evaluator

    log.info("=== XR11 API starting up ===")

    # Import here to keep module-level import errors out of the startup path
    from src.model.report_generator import ReportGenerator
    from src.evaluation.evaluator import Evaluator

    log.info("Loading ReportGenerator (embedding model + FAISS index) …")
    generator = ReportGenerator()   # loads embedder, FAISS, NLI, KG, HallucinationDetector

    log.info("Loading Evaluator …")
    evaluator = Evaluator()

    log.info("=== XR11 API ready ===")


# ── Utility ────────────────────────────────────────────────────────────────────

def _require_ready():
    """Raise 503 if startup hasn't completed yet."""
    if generator is None or evaluator is None:
        raise HTTPException(status_code=503, detail="Service is still initialising. Try again shortly.")


# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.get("/", summary="Root")
def root():
    return {"status": "running", "version": "1.0.0"}


@app.get("/health", summary="Health check")
def health():
    return {"status": "ok"}


@app.get(
    "/api/stats",
    response_model=StatsResponse,
    summary="Dataset and index statistics",
)
def get_stats():
    """Returns the number of entries in dataset.json and vectors in the FAISS index."""
    _require_ready()

    dataset_size = 0
    if os.path.isfile(_DATASET_PATH):
        try:
            with open(_DATASET_PATH, "r", encoding="utf-8") as fp:
                dataset_size = len(json.load(fp))
        except Exception:
            pass

    index_size = 0
    try:
        index_size = generator.vector_store._index.ntotal
    except Exception:
        pass

    return StatsResponse(dataset_size=dataset_size, index_size=index_size)


@app.post(
    "/api/generate-report",
    response_model=GenerateReportResponse,
    summary="Generate a structured radiology report from a chest X-ray image",
)
async def generate_report(file: UploadFile = File(...)):
    """
    Accepts a PNG or JPG chest X-ray image and runs the full 6-step pipeline:

    1. RAG retrieval (3 similar historical cases)
    2. Monte-Carlo uncertainty quantification (5 samples)
    3. Round 1 generation (RAG-grounded, T=0.3)
    4. Round 2 refinement (T=0.2)
    5. Verification: NLI check + KG grounding + Hallucination detection
    6. Return assembled result

    Returns structured findings, impression, severity, follow-up,
    uncertainty metrics, and verification scores.
    """
    _require_ready()

    # ── Validate file type ────────────────────────────────────────────────────
    allowed = {"image/png", "image/jpeg", "image/jpg"}
    if file.content_type not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{file.content_type}'. Only PNG/JPG images are accepted.",
        )

    temp_path = os.path.join(_TEMP_DIR, f"{uuid.uuid4()}.png")

    try:
        # ── Save uploaded file ────────────────────────────────────────────────
        with open(temp_path, "wb") as buf:
            shutil.copyfileobj(file.file, buf)

        # ── Run full pipeline (Steps 1-6 are all inside generate_report) ─────
        result = generator.generate_report(temp_path)

        verification = result.get("verification", {})

        return GenerateReportResponse(
            status="success",
            data={
                "final_report":    result.get("final_report",    {}),
                "round1_raw":      result.get("round1_raw",      ""),
                "round2_raw":      result.get("round2_raw",      ""),
                "retrieved_cases": result.get("retrieved_cases", []),
                "uncertainty":     result.get("uncertainty",     {}),
                "nli_check":       verification.get("nli_results",           {}),
                "knowledge_graph": verification.get("kg_results",            {}),
                "hallucination":   verification.get("hallucination_results", {}),
            },
        )

    except HTTPException:
        raise
    except Exception as exc:
        log.error("generate_report endpoint failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@app.post(
    "/api/evaluate",
    response_model=EvaluateResponse,
    summary="Compute BLEU and ROUGE scores for a generated report",
)
def evaluate_report(payload: EvaluateRequest):
    """
    Accepts a generated report dict and a gold (reference) dict and returns
    BLEU + ROUGE-1/2/L scores for the findings and impression fields.

    Body example:
    ```json
    {
      "generated": {"findings": "...", "impression": "..."},
      "gold":      {"gold_findings": "...", "gold_impression": "..."}
    }
    ```
    """
    _require_ready()

    try:
        scores = evaluator.evaluate_single(
            generated_report = payload.generated,
            gold_findings    = payload.gold.get("gold_findings",  ""),
            gold_impression  = payload.gold.get("gold_impression", ""),
        )
        return EvaluateResponse(status="success", scores=scores)
    except Exception as exc:
        log.error("evaluate endpoint failed: %s", exc, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))