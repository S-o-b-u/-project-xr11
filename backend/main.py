from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import uuid
from src.model.report_generator import ReportGenerator

app = FastAPI(title="Medical Report Generation API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

generator = ReportGenerator()

TEMP_DIR = "temp_uploads"
os.makedirs(TEMP_DIR, exist_ok=True)


@app.get("/")
def root():
    return {"status": "Medical Report API is running"}


@app.post("/api/generate-report")
async def generate_report(file: UploadFile = File(...)):
    # Validate file type
    if file.content_type not in ["image/png", "image/jpeg", "image/jpg"]:
        raise HTTPException(status_code=400, detail="Only PNG/JPG images allowed")

    temp_path = os.path.join(TEMP_DIR, f"{uuid.uuid4()}.png")

    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        result = generator.generate_report(temp_path)

        return {
            "status": "success",
            "data": {
                "final_report": result["final_report"],
                "round1_raw": result["round1_raw"],
                "round2_raw": result["round2_raw"],
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@app.post("/api/evaluate")
async def evaluate_report(payload: dict):
    """
    Accepts generated report + gold report and returns BLEU/ROUGE scores
    """
    from src.evaluation.evaluator import Evaluator
    evaluator = Evaluator()

    scores = evaluator.evaluate_single(
        generated=payload["generated"],
        gold=payload["gold"]
    )
    return {"status": "success", "scores": scores}


@app.get("/health")
def health():
    return {"status": "ok"}