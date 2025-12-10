import uuid
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import models


async def create_document(
    session: AsyncSession, *, title: str, source_path: str, metadata: dict | None = None
) -> models.Document:
    document = models.Document(title=title, source_path=source_path, metadata=metadata or {})
    session.add(document)
    await session.commit()
    await session.refresh(document)
    return document


async def list_documents(session: AsyncSession, limit: int = 50) -> Sequence[models.Document]:
    result = await session.execute(select(models.Document).limit(limit))
    return result.scalars().all()


async def store_feedback(
    session: AsyncSession,
    *,
    user_id: uuid.UUID,
    question: str,
    answer: str,
    rating: int,
    metadata: dict | None = None,
) -> models.Feedback:
    feedback = models.Feedback(
        user_id=user_id,
        question=question,
        answer=answer,
        rating=rating,
        metadata=metadata or {},
    )
    session.add(feedback)
    await session.commit()
    await session.refresh(feedback)
    return feedback

