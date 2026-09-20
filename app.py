from fastapi.responses import StreamingResponse
import csv

@app.post("/api/v1/export-audit-report")
async def export_audit_report(file: UploadFile = File(...)):
    # Reuse our ingestion and analysis logic for export
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
