from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .oncoai_guardrails import process_and_guardrail_extraction

app = FastAPI(
    title="OncoAI Pathology Processor",
    description="API for processing and running guardrails on pathology extractions.",
    version="0.1.0"
)

class PathologyRequest(BaseModel):
    extraction_data: str

@app.get("/")
def read_root():
    return {"status": "online", "service": "OncoAI Pathology Processor"}

@app.post("/process")
def process_pathology(payload: PathologyRequest):
    try:
        result = process_and_guardrail_extraction(payload.extraction_data)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
