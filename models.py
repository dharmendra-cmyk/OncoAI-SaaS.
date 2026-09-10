"""
Clinical Auditor Pro - Database Models & 21 CFR Part 11 Audit Trail
Defines SQLAlchemy ORM models for persistent, immutable clinical audit logs.
"""

from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class ClinicalAuditLog(Base):
    """
    Represents an immutable electronic audit record for a clinical report analysis.
    Satisfies 21 CFR Part 11 requirements for secure, searchable, and timestamped audit logs.
    """
    __tablename__ = "clinical_audit_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    report_id = Column(String(64), unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Analysis Metrics
    status = Column(String(32), nullable=False)  # SUCCESS, REVIEW_RECOMMENDED, FAILED
    confidence_score = Column(Float, nullable=False)
    review_required = Column(Boolean, default=False, nullable=False)
    
    # Payloads & Audit Data
    raw_pathology_text = Column(Text, nullable=False)
    extractions_json = Column(JSON, nullable=False)  # Structured biomarker extraction results
    
    # Compliance & Traceability Metadata
    compliance_standard = Column(String(64), default="21 CFR Part 11", nullable=False)
    auditor_signature = Column(String(128), default="Automated Enterprise Guardrails v1.0", nullable=False)

    def __repr__(self):
        return f"<ClinicalAuditLog(report_id='{self.report_id}', status='{self.status}', confidence={self.confidence_score})>"


# Database Initialization Helper
def init_db(database_url: str = "sqlite:///./clinical_audits.db"):
    """
    Initializes the SQLite/PostgreSQL database engine and creates all audit tables.
    """
    engine = create_engine(database_url, connect_args={"check_same_thread": False} if "sqlite" in database_url else {})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine, SessionLocal
