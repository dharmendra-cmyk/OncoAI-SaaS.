import os
import json
import datetime
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship
from google import genai
from google.genai import types
from oncoai_guardrails import process_and_guardrail_extraction

# Vercel requires writing SQLite to the ephemeral /tmp directory
DATABASE_URL = "sqlite:////tmp/oncoai_audit.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class PathologyReportDB(Base):
    __tablename__ = "pathology_reports"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    report_text = Column(Text, nullable=False)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="OncoAI Pathology Processor")

app.add_middleware(
    CORSWorkflowMiddleware if 'CORSWorkflowMiddleware' in globals() else CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "healthy", "service": "OncoAI Pathology Processor API"}

@app.get("/docs-check")
def docs_check():
    return {"database": "connected", "path": "/tmp/oncoai_audit.db"}
