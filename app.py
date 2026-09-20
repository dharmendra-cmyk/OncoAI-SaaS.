from fastapi import FastAPI, UploadFile, File, HTTPException
import pandas as pd
import io

app = FastAPI(title="OncoAI-Saas", version="0.1.0")

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
            
    return {
        "status": "success",
        "rows_processed": len(df),
        "preview": df.head(3).to_dict(orient="records")
    }
