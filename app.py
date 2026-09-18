"""
OncoAI - FastAPI Application Entrypoint
Provides health check and /infer endpoints with strict validation and audit logging.
"""

from fastapi import FastAPI, HTTPException
from models import ClinicalQueryRequest
from processor import OncologyPipelineProcessor

app = FastAPI(
    title="OncoAI Clinical Decision Support API",
    version="1.0",
    description="Secure AI-driven oncology decision support and 21 CFR Part 11 audit pipeline."
)

@app.get("/")
def health_check():
    """Service health check endpoint."""
    return {
        "status": "healthy",
        "service": "OncoAI Clinical Decision Support"
    }

@app.post("/infer")
def infer_case(payload: ClinicalQueryRequest):
    """
    Core clinical evaluation endpoint. 
    Automatically validates payload via Pydantic and triggers the processing pipeline.
    """
    try:
        # Run processing pipeline logic
        result = OncologyPipelineProcessor.evaluate_case(payload)
        return {
            "message": "Clinical evaluation processed successfully.",
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
