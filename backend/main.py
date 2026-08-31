import logging
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from backend.api.ai import router as ai_router
from backend.api.calendar import router as event_router
from backend.api.schedule import router as schedule_router
from backend.api.tasks import router as task_router
from backend.logging_config import configure_logging


configure_logging()
request_logger = logging.getLogger("studentos.http")

app = FastAPI(
    title="StudentOS",
    version="0.0.1",
    description="AI powered intent-based productivity operating system",
)
# TODO: Restrict this list through deployment configuration.
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_http_request(request: Request, call_next):
    """Record safe request metadata without query strings or request bodies."""

    request_id = uuid4().hex[:12]
    started_at = perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        duration_ms = (perf_counter() - started_at) * 1000
        request_logger.exception(
            "http_request_failed request_id=%s method=%s path=%s "
            "duration_ms=%.2f",
            request_id,
            request.method,
            request.url.path,
            duration_ms,
        )
        raise

    duration_ms = (perf_counter() - started_at) * 1000
    response.headers["X-Request-ID"] = request_id
    request_logger.info(
        "http_request_completed request_id=%s method=%s path=%s "
        "status_code=%s duration_ms=%.2f",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


@app.get("/")
def root():
    return {
        "message": "StudentOS backend running"
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "version": "0.0.1"
    }

app.include_router(task_router)
app.include_router(event_router)
app.include_router(schedule_router)
app.include_router(ai_router)
