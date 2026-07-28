from fastapi import FastAPI

app = FastAPI(
    title="StudentOS",
    version="0.0.1"
)

@app.get("/")
def root():
    return{
        "message": "StudentOS backend running"
    }

@app.get("/health")
def health():
    return{
        "status": "healthy",
        "version": "0.0.1"
    }