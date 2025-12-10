from dataclasses import dataclass
from typing import Any

from app.rag.pipeline import PipelineResult, RAGPipeline


@dataclass
class QAAgent:
    pipeline: RAGPipeline

    async def run(self, query: str, top_k: int = 5, tenant_id: str | None = None) -> dict[str, Any]:
        _ = tenant_id
        result: PipelineResult = await self.pipeline.run(query=query, top_k=top_k)
        return {
            "answer": result.answer,
            "references": result.references,
            "latency_ms": result.latency_ms,
        }

