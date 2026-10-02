from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from diagnostic_module import DiagnosticPredictor

app = FastAPI(
    title="OncoAI Clinical Decision Support API",
    description="Multi-omic diagnostic risk scoring and clinical decision support system",
    version="1.0.0"
)

predictor = DiagnosticPredictor()

class BiopsyType(str, Enum):
    LIQUID = "liquid"
    SOLID = "solid"
    COMBINED = "combined"

class SomaticMutation(BaseModel):
    gene: str = Field(..., description="Target gene symbol")
    variant_allele_frequency: float = Field(..., ge=0.0, le=1.0, description="Variant allele frequency")
    depth_of_coverage: int = Field(..., gt=0, description="Sequencing depth of coverage")

class LiquidBiopsyData(BaseModel):
    cfdna_concentration_ng_ml: float = Field(..., ge=0.0, description="Cell-free DNA concentration in ng/mL")
    fragmentomics_score: float = Field(..., ge=0.0, le=1.0, description="Fragmentomics score")
    methylation_signature_score: float = Field(..., ge=0.0, le=1.0, description="Methylation signature score")
    mutations: List[SomaticMutation] = Field(default_factory=list, description="List of detected somatic mutations")

class SolidBiopsyData(BaseModel):
    histopathology_grade: str = Field(..., description="Histopathology grade")
    immunohistochemistry_markers: Dict[str, float] = Field(default_factory=dict, description="IHC marker expression levels")
    cellularity_percentage: float = Field(..., ge=0.0, le=100.0, description="Tumor cellularity percentage")

class DiagnosticCasePayload(BaseModel):
    case_id: str = Field(..., description="Unique clinical case identifier")
    biopsy_type: BiopsyType = Field(..., description="Type of biopsy performed")
    liquid_data: Optional[LiquidBiopsyData] = Field(None, description="Liquid biopsy multi-omic data")
    solid_data: Optional[SolidBiopsyData] = Field(None, description="Solid biopsy histopathology data")
    clinical_covariates: Dict[str, Any] = Field(default_factory=dict, description="Patient clinical covariates and metadata")

@app.get("/", tags=["System"])
def read_root():
    return {
        "status": "success",
        "service": "OncoAI Clinical Decision Support",
        "message": "API is live and operational"
    }

@app.get("/health", tags=["System"])
def health_check():
    return {"status": "healthy"}

@app.post("/api/v1/diagnostic/infer", tags=["Diagnostic Inference"])
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
