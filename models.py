from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class ClinicalAuditLog(Base):
    """21 CFR Part 11 compliant immutable audit trail log table."""
    __tablename__ = "clinical_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(String(64), unique=True, index=True, nullable=False)
    status = Column(String(32), nullable=False)
    confidence_score = Column(Float, nullable=True)
    review_required = Column(Boolean, default=False)
    raw_pathology_text = Column(Text, nullable=True)
    extractions_json = Column(Text, nullable=True)  # Stored as serialized JSON string
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    user_identifier = Column(String(128), nullable=False)
    record_hash = Column(String(128), nullable=False)  # Cryptographic hash for tamper-evidence

class ClinicalQueryRequest(BaseModel):
    patient_age: int = Field(..., ge=0, le=120, description="Patient age in years.")
    psa_level: float = Field(..., ge=0.0, description="PSA biomarker level.")
    gleason_score: int = Field(..., ge=2, le=10, description="Gleason score.")
    clinical_notes: str = Field(..., max_length=1000, description="Clinical pathologist or physician notes.")
    user_identifier: str = Field(..., min_length=2, description="ID of the clinician submitting the case.")
    prompt: Optional[str] = Field(default=None, description="Optional natural language query or analysis focus.")
