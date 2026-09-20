from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.triage import router as triage_router
from app.core.config import settings

app = FastAPI(
    title="TickTalk API",
    description="Image-first Lyme disease TRIAGE (not diagnosis) API.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(triage_router, prefix="/api")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
