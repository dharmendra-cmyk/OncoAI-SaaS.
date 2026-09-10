"""
Clinical Auditor Pro - Database Models & Initialization
Supports both SQLite (local development) and PostgreSQL (Render production) 
with immutable 21 CFR Part 11 audit logging fields.
"""

import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class ClinicalAuditLog(Base):
    __tablename__ = "clinical_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(String(64), unique=True, index=True, nullable=False)
    status = Column(String(32), nullable=False)
    confidence_score = Column(Float, nullable=False)
    review_required = Column(Boolean, default=False)
    raw_pathology_text = Column(Text, nullable=False)
    extractions_json = Column(Text, nullable=False)  # Stored as serialized JSON string or JSON
    compliance_standard = Column(String(64), default="21 CFR Part 11")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


def init_db():
    """
    Initializes the database engine. Automatically detects Render's PostgreSQL 
    DATABASE_URL environment variable, normalized for SQLAlchemy compatibility.
    """
    database_url = os.getenv("DATABASE_URL")
    
    if database_url:
        # Render sometimes provides 'postgres://' which SQLAlchemy requires as 'postgresql://'
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        engine = create_engine(database_url, pool_pre_ping=True)
    else:
        # Fallback local SQLite engine for development
        sqlite_path = "sqlite:///./clinical_audits.db"
        engine = create_engine(sqlite_path, connect_args={"check_same_thread": False})

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create tables if they do not exist
    Base.metadata.create_all(bind=engine)
    
    return engine, SessionLocal
