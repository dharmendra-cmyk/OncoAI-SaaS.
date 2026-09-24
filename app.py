from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "success", "message": "OncoAI Clinical Decision Support API is Live and Operational"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}
