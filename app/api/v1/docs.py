from pathlib import Path

from fastapi import APIRouter, Depends, UploadFile, File
from pydantic import BaseModel

from app.core.security import get_api_key
from app.db.session import async_session
from app.rag.ingestion import DocumentIngestor


class IngestResponse(BaseModel):
    document_id: str
    chunks: int


router = APIRouter(prefix="/docs", tags=["docs"], dependencies=[Depends(get_api_key)])


@router.post("/ingest", response_model=IngestResponse)
async def ingest_document(file: UploadFile = File(...)) -> IngestResponse:
    temp_path = Path("tmp") / file.filename
    temp_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path.write_bytes(await file.read())

    ingestor = DocumentIngestor()
    async with async_session() as session:
        chunks = await ingestor.ingest_file(temp_path, session=session)

    temp_path.unlink(missing_ok=True)
    return IngestResponse(document_id=str(chunks.document_id), chunks=chunks.chunk_count)


@router.post("/reindex")
async def reindex_corpus() -> dict[str, str]:
    # Hook for kicking off an offline rebuild job (Celery, Prefect, etc.)
    return {"status": "queued"}

