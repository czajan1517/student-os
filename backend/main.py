from fastapi import FastAPI

from backend.api.tasks import router as task_router
from backend.api.calendar import router as event_router

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="StudentOS",
    version="0.0.1",
    description="AI powered intent=based productivity operating system"
)
## TODO: to be changed 
origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

app.include_router(task_router)
app.include_router(event_router)
