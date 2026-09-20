from fastapi import FastAPI, UploadFile, File, HTTPException
import pandas as pd
import io

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
            
    # Phase 2: Biomarker Trend & Anomaly Analysis
    analyzed_records = []
    anomalies_detected = 0
    
    for _, row in df.iterrows():
        biomarker = str(row["biomarker"]).strip()
        value = float(row["value"])
        threshold = BENCHMARK_THRESHOLDS.get(biomarker, 10.0) # Default fallback
        
        status = "Normal"
        if value > threshold:
            status = "Elevated/Anomalous"
            anomalies_detected += 1
            
        analyzed_records.append({
            "patient_id": row["patient_id"],
            "biomarker": biomarker,
            "value": value,
            "date": row["date"],
            "status": status,
            "threshold_limit": threshold
        })
            
    return {
        "status": "success",
        "rows_processed": len(df),
        "anomalies_flagged": anomalies_detected,
        "analysis_results": analyzed_records
    }
