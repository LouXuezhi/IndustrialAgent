import time
from fastapi import APIRouter

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "healthy", "timestamp": str(time.time())}


@router.get("/ping")
async def ping() -> dict[str, str]:
    return {"message": "pong"}

