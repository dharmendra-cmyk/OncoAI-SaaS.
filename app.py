from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
import pandas as pd
import io
import csv

app = FastAPI(title="OncoAI-Saas", version="0.1.0")

# Benchmark threshold dictionary for clinical oncology tracking
BENCHMARK_THRESHOLDS = {
    "CEA": 5.0,      # ng/mL
    "CA19-9": 37.0,  # U/mL
    "PSA": 4.0       # ng/mL
}

@app.post("/api/v1/ingest-pathology")
async def ingest_pathology_batch(file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Invalid file format. CSV required.")
    
    contents = await file.read()
    df = pd.read_csv(io.BytesIO(contents))
    
    # Required clinical columns check
    required_columns = ["patient_id", "biomarker", "value", "date"]
    for col in required_columns:
        if col not in df.columns:
            raise HTTPException(status_code=400, detail=f"Missing required column: {col}")

    # Biomarker Trend & Anomaly Analysis
    analyzed_records = []
    anomalies_count = 0

    for _, row in df.iterrows():
        biomarker = str(row["biomarker"]).strip()
        value = float(row["value"])
        threshold = BENCHMARK_THRESHOLDS.get(biomarker, 10.0)
        
        status = "Elevated/Anomalous" if value > threshold else "Normal"
        if status == "Elevated/Anomalous":
            anomalies_count += 1
            
        analyzed_records.append({
            "patient_id": row["patient_id"],
            "biomarker": biomarker,
            "value": value,
            "threshold_limit": threshold,
            "date": row["date"],
            "status": status
        })

    return {
        "status": "success",
        "records_processed": len(analyzed_records),
        "anomalies_flagged": anomalies_count,
        "analysis_results": analyzed_records
    }

@app.post("/api/v1/export-audit-report")
async def export_audit_report(file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Invalid file format. CSV required.")
    
    contents = await file.read()
    df = pd.read_csv(io.BytesIO(contents))
    
    required_columns = ["patient_id", "biomarker", "value", "date"]
    for col in required_columns:
        if col not in df.columns:
            raise HTTPException(status_code=400, detail=f"Missing required column: {col}")
            
    analyzed_rows = []
    for _, row in df.iterrows():
        biomarker = str(row["biomarker"]).strip()
        value = float(row["value"])
        threshold = BENCHMARK_THRESHOLDS.get(biomarker, 10.0)
        
        status = "Elevated/Anomalous" if value > threshold else "Normal"
        
        analyzed_rows.append({
            "patient_id": row["patient_id"],
            "biomarker": biomarker,
            "value": value,
            "date": row["date"],
            "status": status,
            "threshold_limit": threshold
        })
    
    # Generate CSV stream for download
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["patient_id", "biomarker", "value", "date", "status", "threshold_limit"])
    writer.writeheader()
    writer.writerows(analyzed_rows)
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=clinical_audit_report.csv"}
    )
