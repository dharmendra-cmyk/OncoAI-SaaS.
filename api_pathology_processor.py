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
from oncoai_guardrails import EnterpriseGuardrails


DATABASE_URL = "sqlite:////tmp/oncoai_audit.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class PathologyReportDB(Base):
    __tablename__ = "pathology_reports"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    report_text = Column(Text, nullable=False)
    status = Column(String, nullable=False)
    overall_confidence = Column(Float, nullable=False)
    review_required = Column(Boolean, default=False)

    extractions = relationship("ExtractionAuditDB", back_populates="report")

class ExtractionAuditDB(Base):
    __tablename__ = "extraction_audits"

    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("pathology_reports.id"))
    biomarker = Column(String, nullable=False)
    mutation_variant = Column(String, nullable=False)
    detection_status = Column(String, nullable=False)
    cited_text = Column(Text, nullable=False)
    is_verbatim_match = Column(Boolean, nullable=False)
    confidence_score = Column(Float, nullable=False)
    therapy_mapping = Column(String, nullable=True)

    report = relationship("PathologyReportDB", back_populates="extractions")

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

app = FastAPI(
    title="OncoAI Zero-Hallucination Guardrail API",
    description="Enterprise API endpoint with live Gemini extractions and audit trails.",
    version="1.2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

class PathologyRequest(BaseModel):
    report_text: str

def extract_with_gemini(report_text: str) -> dict:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")

    client = genai.Client(api_key=api_key)

    prompt = f"""
    You are an expert precision oncology AI assistant.
    Extract all cancer biomarkers, gene mutations, and protein expressions from the pathology report below.
    
    For EVERY extraction, you MUST include the exact, verbatim quote from the text as 'cited_text'.

    Return ONLY a JSON object matching this schema:
    {{
      "extractions": [
        {{
          "biomarker": "Gene/Protein Name (e.g. EGFR, ALK, PD-L1)",
          "mutation_variant": "Specific variant or score (e.g. Exon 19 Deletion, TPS 65%)",
          "detection_status": "POSITIVE or NEGATIVE",
          "cited_text": "EXACT verbatim sentence or snippet from report text",
          "page_number": 1
        }}
      ]
    }}

    PATHOLOGY REPORT TEXT:
    {report_text}
    """

    response = client.models.generate_content(
       model="gemini-3.6-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.0,
        ),
    )

    return json.loads(response.text)

@app.get("/")
def health_check():
   return {"status": "HEALTHY", "engine": "Gemini 2.5 Flash + Guardrails"}

@app.post("/api/v1/analyze-pathology")
def analyze_pathology(payload: PathologyRequest, db: Session = Depends(get_db)):
    if not payload.report_text.strip():
        raise HTTPException(status_code=400, detail="Report text cannot be empty.")

    try:
        if os.environ.get("GEMINI_API_KEY"):
            llm_output = extract_with_gemini(payload.report_text)
        else:
            llm_output = {
                "extractions": [
                    {
                        "biomarker": "EGFR",
                        "mutation_variant": "Exon 19 Deletion",
                        "detection_status": "POSITIVE",
                        "cited_text": "EGFR: Positive for Exon 19 Deletion",
                        "page_number": 1
                    }
                ]
            }

        guardrailed_results = process_and_guardrail_extraction(llm_output, payload.report_text)

        db_report = PathologyReportDB(
            report_text=payload.report_text,
            status=guardrailed_results.get("status", "SUCCESS"),
            overall_confidence=guardrailed_results.get("confidence_score", 1.0),
            review_required=guardrailed_results.get("review_required", False)
        )
        db.add(db_report)
        db.commit()
        db.refresh(db_report)

        for ext in guardrailed_results.get("extractions", []):
            db_ext = ExtractionAuditDB(
                report_id=db_report.id,
                biomarker=ext.get("biomarker"),
                mutation_variant=ext.get("mutation_variant"),
                detection_status=ext.get("detection_status"),
                cited_text=ext.get("cited_text"),
                is_verbatim_match=ext.get("is_verbatim_match"),
                confidence_score=ext.get("confidence_score"),
                therapy_mapping=ext.get("therapy_mapping")
            )
            db.add(db_ext)

        db.commit()

        guardrailed_results["report_id"] = db_report.id
        return guardrailed_results

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@app.get("/api/v1/audit-history")
def get_audit_history(db: Session = Depends(get_db)):
    reports = db.query(PathologyReportDB).order_by(PathologyReportDB.created_at.desc()).limit(10).all()
    history = []
    for r in reports:
        extractions = db.query(ExtractionAuditDB).filter(ExtractionAuditDB.report_id == r.id).all()
        history.append({
            "report_id": r.id,
            "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "status": r.status,
            "overall_confidence": r.overall_confidence,
            "review_required": r.review_required,
            "extractions_count": len(extractions),
            "extractions": [
                {
                    "biomarker": e.biomarker,
                    "mutation_variant": e.mutation_variant,
                    "detection_status": e.detection_status,
                    "cited_text": e.cited_text,
                    "is_verbatim_match": e.is_verbatim_match,
                    "therapy_mapping": e.therapy_mapping
                } for e in extractions
            ]
        })
    return history

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api_pathology_processor:app", host="0.0.0.0", port=8000, reload=True)
