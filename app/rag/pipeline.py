import time
from dataclasses import dataclass

from app.rag.prompts import get_prompt
from app.rag.retriever import HybridRetriever


@dataclass
class PipelineResult:
    answer: str
    references: list[dict]
    latency_ms: int


class RAGPipeline:
    def __init__(self, retriever: HybridRetriever) -> None:
        self.retriever = retriever

    async def run(self, query: str, top_k: int = 5, role: str | None = None) -> PipelineResult:
        start = time.perf_counter()
        chunks = await self.retriever.search(query, top_k=top_k)
        context = "\n".join(chunk.text for chunk in chunks)
        prompt = get_prompt(role=role).format(context=context, question=query)

        # Placeholder LLM call
        answer = (
            f"(demo answer) Based on {len(chunks)} retrieved chunks, "
            f"the system would respond to '{query}'.\nPrompt:\n{prompt}"
        )

        latency_ms = int((time.perf_counter() - start) * 1000)
        references = [{"document_id": c.document_id, "score": c.score, "metadata": c.metadata} for c in chunks]

        return PipelineResult(answer=answer, references=references, latency_ms=latency_ms)

