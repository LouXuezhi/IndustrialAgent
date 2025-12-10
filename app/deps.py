from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings, Settings
from app.db.session import async_session
from app.rag.pipeline import RAGPipeline
from app.rag.retriever import HybridRetriever


def get_app_settings() -> Settings:
    return get_settings()


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


def get_retriever(settings: Settings | None = None) -> HybridRetriever:
    settings = settings or get_settings()
    return HybridRetriever(
        vector_uri=settings.vector_db_uri,
        embedding_model=settings.embedding_model,
    )


def get_pipeline(retriever: HybridRetriever | None = None) -> RAGPipeline:
    retriever = retriever or get_retriever()
    return RAGPipeline(retriever=retriever)

