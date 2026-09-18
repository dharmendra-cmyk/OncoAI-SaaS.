"""
OncoAI - Database Models & Pydantic Validation Schemas
Supports SQLite/PostgreSQL with immutable 21 CFR Part 11 audit logging fields 
and strict clinical input validation.
"""

from datetime import datetime
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, Float, Boolean, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class ClinicalAuditLog(Base):
    """21 CFR Part 11 compliant immutable audit trail log table."""
    __tablename__ = "clinical_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(String(64), unique=True, index=True, nullable=False)
    status = Column(String(32), nullable=False)
    confidence_score = Column(Float, nullable=True)
    review_required = Column(Boolean, default=False)
    raw_pathology_text = Column(Text, nullable=False)
    extractions_json = Column(Text, nullable=False)  # Stored as serialized JSON string
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    user_identifier = Column(String(128), nullable=False)
    record_hash = Column(String(128), nullable=False)  # Cryptographic hash for tamper-evidence


# ==========================================
# Pydantic Validation Models (Step 1)
# ==========================================

class ClinicalQueryRequest(BaseModel):
    """Strict validation schema for incoming oncology evaluation payloads."""
    patient_age: int = Field(..., ge=0, le=120, description="Patient age in years (0-120)")
    psa_level: float = Field(..., ge=0.0, description="PSA level in ng/mL (must be non-negative)")
    gleason_score: int = Field(..., ge=6, le=10, description="Gleason score (valid range 6 to 10)")
    clinical_notes: str = Field(..., min_length=5, description="Clinical narrative or pathology details")
    user_identifier: str = Field(..., description="Clinician or system user ID for audit logging")
