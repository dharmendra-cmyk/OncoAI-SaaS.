from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse
import io
import csv
import os

app = FastAPI(title="OncoAI-Saas", version="0.1.0")

BENCHMARK_THRESHOLDS = {
    "CEA": 5.0,
    "CA19-9": 37.0,
    "PSA": 4.0
}

@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    return "<h3>OncoAI-Saas Dashboard UI</h3>"

@app.post("/api/v1/ingest-pathology")
async def ingest_pathology_batch(file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Invalid file format. CSV required.")
    
    contents = await file.read()
    lines = contents.decode('utf-8').splitlines()
    reader = csv.DictReader(lines)
    
    required_columns = ["patient_id", "biomarker", "value", "date"]
    if not reader.fieldnames or not all(col in reader.fieldnames for col in required_columns):
        raise HTTPException(status_code=400, detail="Missing required columns in CSV.")

    analyzed_records = []
    anomalies_count = 0

    for row in reader:
        biomarker = str(row.get("biomarker", "")).strip()
        try:
            value = float(row.get("value", 0))
        except ValueError:
            continue
            
        threshold = BENCHMARK_THRESHOLDS.get(biomarker, 10.0)
        status = "Elevated/Anomalous" if value > threshold else "Normal"
        if status == "Elevated/Anomalous":
            anomalies_count += 1
            
        analyzed_records.append({
            "patient_id": row.get("patient_id"),
            "biomarker": biomarker,
            "value": value,
            "threshold_limit": threshold,
            "date": row.get("date"),
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
    lines = contents.decode('utf-8').splitlines()
    reader = csv.DictReader(lines)
    
    output = io.StringIO()
    fieldnames = ["patient_id", "biomarker", "value", "date", "status", "threshold_limit"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    
    for row in reader:
        biomarker = str(row.get("biomarker", "")).strip()
        try:
            value = float(row.get("value", 0))
        except ValueError:
            continue
        threshold = BENCHMARK_THRESHOLDS.get(biomarker, 10.0)
        status = "Elevated/Anomalous" if value > threshold else "Normal"
        
        writer.writerow({
            "patient_id": row.get("patient_id"),
            "biomarker": biomarker,
            "value": value,
            "date": row.get("date"),
            "status": status,
            "threshold_limit": threshold
        })
            
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=clinical_audit_report.csv"}
    )
