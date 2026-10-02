from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from diagnostic_module import DiagnosticPredictor

app = FastAPI(title="OncoAI API", version="1.0")

predictor = DiagnosticPredictor()

class BiopsyType(str, Enum):
    LIQUID = "liquid"
    SOLID = "solid"
    COMBINED = "combined"

class SomaticMutation(BaseModel):
    gene: str = Field(..., description="Target gene symbol")
    variant_allele_frequency: float = Field(..., ge=0.0, le=1.0)
    depth_of_coverage: int = Field(..., gt=0)

class LiquidBiopsyData(BaseModel):
    cfdna_concentration_ng_ml: float = Field(..., ge=0.0)
    fragmentomics_score: float = Field(..., ge=0.0, le=1.0)
    methylation_signature_score: float = Field(..., ge=0.0, le=1.0)
    mutations: List[SomaticMutation] = Field(default_factory=list)

class SolidBiopsyData(BaseModel):
    histopathology_grade: str
    immunohistochemistry_markers: Dict[str, float] = Field(default_factory=dict)
    cellularity_percentage: float = Field(..., ge=0.0, le=100.0)

class DiagnosticCasePayload(BaseModel):
    case_id: str
    biopsy_type: BiopsyType
    liquid_data: Optional[LiquidBiopsyData] = None
    solid_data: Optional[SolidBiopsyData] = None
    clinical_covariates: Dict[str, Any] = Field(default_factory=dict)

@app.get("/")
def read_root():
    return {"status": "success", "message": "OncoAI Clinical Decision Support API is live and Operational"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.post("/api/v1/diagnostic/infer")
async def diagnostic_infer(payload: DiagnosticCasePayload):
    try:
        payload_dict = payload.model_dump()
        result = predictor.compute_risk_score(payload_dict)
        return {
            "case_id": payload.case_id,
            "biopsy_type": payload.biopsy_type,
            "prediction": result,
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
