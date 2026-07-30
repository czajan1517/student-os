from fastapi import FastAPI
from backend.database.database import create_database

from backend.api.tasks import router as task_router
from backend.api.calendar import router as event_router


app = FastAPI(
    title="StudentOS",
    version="0.0.1",
    description="AI powered intent=based productivity operating system"
)

create_database()

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

app.include_router(task_router)
app.include_router(event_router)
