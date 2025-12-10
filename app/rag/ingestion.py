import uuid
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class IngestionReport:
    document_id: uuid.UUID
    chunk_count: int


class DocumentIngestor:
    async def ingest_file(self, path: Path, session: AsyncSession) -> IngestionReport:
        # Simplified placeholder
        _ = session
        document_id = uuid.uuid4()
        text = path.read_text(encoding="utf-8", errors="ignore")
        chunk_count = max(1, len(text) // 500)
        return IngestionReport(document_id=document_id, chunk_count=chunk_count)

