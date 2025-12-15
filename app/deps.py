from collections.abc import AsyncGenerator
from functools import lru_cache

import redis.asyncio as redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings, Settings
from app.core.email import EmailService
from app.db.session import async_session
from app.rag.pipeline import RAGPipeline
from app.rag.retriever import LangchainRetriever, HybridRetriever


def get_app_settings() -> Settings:
    return get_settings()


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session as a dependency."""
    async with async_session() as session:
        yield session


# 全局检索器实例（单例模式，用于缓存 BM25 索引）
_global_retriever: HybridRetriever | None = None


def get_retriever(settings: Settings | None = None, use_hybrid: bool = True) -> LangchainRetriever:
    """
    获取检索器实例（单例模式，确保 BM25 缓存共享）。
    
    Args:
        settings: 配置对象
        use_hybrid: 是否使用混合检索（向量 + BM25），默认 True
    
    Returns:
        HybridRetriever 或 LangchainRetriever 实例
    """
    global _global_retriever
    
    settings = settings or get_settings()
    if use_hybrid:
        if _global_retriever is None:
            _global_retriever = HybridRetriever(
                vector_uri=settings.vector_db_uri,
                settings=settings,
                enable_rerank=settings.enable_rerank,
            )
        return _global_retriever
    else:
        return LangchainRetriever(
            vector_uri=settings.vector_db_uri,
            settings=settings,
        )


@lru_cache(maxsize=1)
def get_pipeline() -> RAGPipeline:
    """Get RAG pipeline instance (cached)."""
    retriever = get_retriever()
    settings = get_settings()
    return RAGPipeline(retriever=retriever, settings=settings)


def get_email_service(settings: Settings | None = None) -> EmailService:
    settings = settings or get_settings()
    return EmailService(settings)


async def get_redis(settings: Settings | None = None) -> AsyncGenerator[redis.Redis, None]:
    """Get Redis client as a dependency."""
    settings = settings or get_settings()
    client = redis.from_url(settings.redis_url, decode_responses=False)
    try:
        yield client
    finally:
        await client.aclose()

