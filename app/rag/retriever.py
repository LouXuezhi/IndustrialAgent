from dataclasses import dataclass
from typing import Any


@dataclass
class RetrievedChunk:
    document_id: str
    text: str
    score: float
    metadata: dict[str, Any]


class HybridRetriever:
    """Simple vector + BM25 hybrid retriever placeholder."""

    def __init__(self, vector_uri: str, embedding_model: str) -> None:
        self.vector_uri = vector_uri
        self.embedding_model = embedding_model

    async def search(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        # Production implementation would call vector DB + BM25 re-ranker
        return [
            RetrievedChunk(
                document_id="demo-doc",
                text="Demo paragraph explaining the system pipeline.",
                score=0.9,
                metadata={"source": "demo"},
            )
            for _ in range(top_k)
        ]

