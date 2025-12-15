import os

# 在导入任何 huggingface 相关库之前，先设置镜像（如果配置了）
# 这样可以确保所有 huggingface 库都使用镜像
from app.core.config import get_settings
_settings = get_settings()
if _settings.hf_endpoint:
    os.environ["HF_ENDPOINT"] = _settings.hf_endpoint

# 禁用 tokenizers 并行化警告（避免 fork 后的死锁警告）
# 这在 uvicorn 使用 --reload 时会 fork 进程，导致警告
if "TOKENIZERS_PARALLELISM" not in os.environ:
    os.environ["TOKENIZERS_PARALLELISM"] = "false"

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import admin, docs, qa, groups
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
app.include_router(groups.router, prefix="/api/v1")


@app.get("/")
async def readiness_probe() -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}

