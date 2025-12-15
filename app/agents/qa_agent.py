from dataclasses import dataclass
from typing import Any
from uuid import UUID

from app.rag.pipeline import PipelineResult, RAGPipeline


@dataclass
class QAAgent:
    pipeline: RAGPipeline

    async def run(
        self,
        query: str,
        top_k: int = 5,
        library_ids: list[str] | None = None,
        role: str | None = None,
    ) -> dict[str, Any]:
        # Convert string IDs to UUIDs if provided
        library_uuids: list[UUID] | None = None
        if library_ids:
            library_uuids = [UUID(lib_id) for lib_id in library_ids]

        result: PipelineResult = await self.pipeline.run(
            query=query,
            top_k=top_k,
            library_ids=library_uuids,
            role=role,
        )
        return {
            "answer": result.answer,
            "references": result.references,
            "latency_ms": result.latency_ms,
        }

