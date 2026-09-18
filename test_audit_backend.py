import pytest
from fastapi.testclient import TestClient
from app import app
from models import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Setup local test database for validation
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_audit.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

client = TestClient(app)

def test_health_check():
    """Verify service health endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_infer_endpoint_compliance():
    """Verify that /infer validates input and generates a 21 CFR Part 11 audit trail."""
    payload = {
        "patient_age": 65,
        "psa_level": 12.5,
        "gleason_score": 7,
        "clinical_notes": "Intermediate risk prostate findings.",
        "user_identifier": "dr_ahluwalia"
    }
    
    response = client.post("/infer", json=payload)
    
    # Assert successful clinical response and audit trail generation
    assert response.status_code == 200
    data = response.json()
    
    assert "report_id" in data
    assert "audit_hash" in data
    assert data["status"] == "success"
    assert data["user_identifier"] == "dr_ahluwalia"
