from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import admin, docs, qa
from app.api.v1 import auth
from app.core.config import settings
from app.core.logging import configure_logging

configure_logging()

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Industrial QA agent backend built on FastAPI + RAG",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin.router, prefix="/api/v1")
app.include_router(docs.router, prefix="/api/v1")
app.include_router(qa.router, prefix="/api/v1/qa")
app.include_router(auth.router, prefix="/api/v1")


@app.get("/")
async def readiness_probe() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}

