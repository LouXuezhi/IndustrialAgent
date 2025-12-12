from dataclasses import dataclass
from typing import Any
from uuid import UUID
import asyncio

from langchain_community.vectorstores import Chroma
from chromadb.utils import embedding_functions
import chromadb
import numpy as np

from app.core.config import get_settings, Settings
from app.rag.ingestion import _resolve_chroma_path


@dataclass
class RetrievedChunk:
    document_id: str
    text: str
    score: float
    metadata: dict[str, Any]


def _build_embedding_fn(settings: Settings):
    # Prefer configured embedding provider; fallback to default.
    if settings.llm_provider == "dashscope" and (
        settings.dashscope_embedding_api_key or settings.dashscope_api_key
    ):
        # DashScope provides an OpenAI-compatible endpoint; use api_base to direct traffic.
        return embedding_functions.OpenAIEmbeddingFunction(
            api_key=settings.dashscope_embedding_api_key or settings.dashscope_api_key,
            model_name=settings.embedding_model,
            api_base=settings.dashscope_embedding_base_url or settings.dashscope_base_url,
        )
    if settings.llm_provider == "openai" and settings.openai_api_key:
        return embedding_functions.OpenAIEmbeddingFunction(
            api_key=settings.openai_api_key,
            model_name=settings.embedding_model,
        )
    return embedding_functions.DefaultEmbeddingFunction()


class LangchainRetriever:
    """LangChain-based Chroma retriever with library scoping."""

    def __init__(self, vector_uri: str, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.chroma_path = _resolve_chroma_path(vector_uri)
        self.embedding_fn = _build_embedding_fn(self.settings)

    def _collection_name(self, library_id: UUID | None) -> str:
        return f"library_{library_id}" if library_id else "library_default"

    def _get_vectorstore(self, library_id: UUID | None) -> Chroma:
        return Chroma(
            collection_name=self._collection_name(library_id),
            embedding_function=self.embedding_fn,
            persist_directory=self.chroma_path,
        )
    
    def _get_chroma_collection(self, library_id: UUID | None):
        """Get ChromaDB collection directly (bypassing LangChain).
        
        Uses the collection's existing embedding function if available,
        otherwise uses the configured embedding function.
        """
        client = chromadb.PersistentClient(path=self.chroma_path)
        collection_name = self._collection_name(library_id)
        try:
            # Try to get existing collection (will use its original embedding function)
            collection = client.get_collection(name=collection_name)
            # If collection exists, it will use its original embedding function
            # We need to ensure we use the same one for queries
            return collection
        except Exception:
            # Collection doesn't exist, create with configured embedding function
            return client.get_collection(
                name=collection_name,
                embedding_function=self.embedding_fn,
            )

    async def search(
        self,
        query: str,
        top_k: int = 5,
        library_ids: list[UUID] | None = None
    ) -> list[RetrievedChunk]:
        library_ids_to_search = library_ids if library_ids else [None]
        results: list[RetrievedChunk] = []

        async def _search_collection(lib_id: UUID | None):
            try:
                import logging
                logger = logging.getLogger(__name__)
                logger.debug(f"Searching collection for library_id: {lib_id}")
                
                # Use ChromaDB directly to avoid LangChain embedding format issues
                collection = self._get_chroma_collection(lib_id)
                
                # Query using ChromaDB's native API
                query_results = await asyncio.to_thread(
                    collection.query,
                    query_texts=[query],
                    n_results=top_k
                )
                
                if not query_results or not query_results.get('ids') or not query_results['ids'][0]:
                    logger.warning(f"No documents found in collection for library_id: {lib_id}")
                    return
                
                # Extract results
                ids = query_results['ids'][0]
                documents = query_results['documents'][0]
                metadatas = query_results['metadatas'][0] if query_results.get('metadatas') else [{}] * len(ids)
                distances = query_results['distances'][0] if query_results.get('distances') else [0.0] * len(ids)
                
                logger.debug(f"Found {len(ids)} documents in collection for library_id: {lib_id}")
                
                for i, (doc_id, doc_text, meta, distance) in enumerate(zip(ids, documents, metadatas, distances)):
                    # Convert distance to similarity (lower distance = higher similarity)
                    similarity = 1.0 / (1.0 + abs(distance)) if distance != 0 else 1.0
                    
                    results.append(
                        RetrievedChunk(
                            document_id=str(meta.get("document_id", doc_id)),
                            text=doc_text,
                            score=similarity,
                            metadata=meta,
                        )
                    )
            except Exception as e:
                # Log error but continue to allow partial results from other stores
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error searching vector store for library_id {lib_id}: {e}", exc_info=True)
                return

        await asyncio.gather(*[_search_collection(lib_id) for lib_id in library_ids_to_search])
        
        if not results:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"No results found for query: {query}, library_ids: {library_ids}")
            return []
        
        # Sort by similarity (descending)
        results.sort(key=lambda c: c.score, reverse=True)
        return results[:top_k]

