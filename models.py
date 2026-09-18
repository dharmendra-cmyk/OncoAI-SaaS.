class ClinicalQueryRequest(BaseModel):
    patient_age: int = Field(..., description="Patient age in years")
    psa_level: float = Field(..., description="PSA level ng/mL")
    gleason_score: int = Field(..., description="Gleason score")
    clinical_notes: str = Field(..., description="Clinical findings or notes")
    user_identifier: str = Field(..., description="Physician identifier")
