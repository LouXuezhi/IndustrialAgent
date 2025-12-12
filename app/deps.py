from collections.abc import AsyncGenerator

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings, Settings
from app.core.email import EmailService
from app.db.session import async_session
from app.rag.pipeline import RAGPipeline
from app.rag.retriever import LangchainRetriever


def get_app_settings() -> Settings:
    return get_settings()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session as a dependency."""
    async with async_session() as session:
        yield session


def get_retriever(settings: Settings | None = None) -> LangchainRetriever:
    settings = settings or get_settings()
    return LangchainRetriever(
        vector_uri=settings.vector_db_uri,
        settings=settings,
    )


def get_pipeline() -> RAGPipeline:
    """Get RAG pipeline instance."""
    retriever = get_retriever()
    settings = get_settings()
    return RAGPipeline(retriever=retriever, settings=settings)


def get_email_service(settings: Settings | None = None) -> EmailService:
    settings = settings or get_settings()
    return EmailService(settings)


def get_redis(settings: Settings | None = None) -> redis.Redis:
    settings = settings or get_settings()
    return redis.from_url(settings.redis_url, decode_responses=False)

