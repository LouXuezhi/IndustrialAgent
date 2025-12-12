"""Email verification service."""

from __future__ import annotations

import secrets
import uuid
from datetime import datetime, timedelta

import redis.asyncio as redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.email import EmailService
from app.db.models import User


class EmailVerificationService:
    """Handles email verification token generation and validation."""

    def __init__(
        self,
        session: AsyncSession,
        settings: Settings,
        email_service: EmailService,
        redis_client: redis.Redis,
    ):
        self.session = session
        self.settings = settings
        self.email_service = email_service
        self.redis = redis_client
        self.expire_hours = 24

    async def send_verification_email(self, user_id: uuid.UUID) -> str:
        """Generate token, store in Redis, and send email."""
        result = await self.session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("User not found")
        if user.is_verified:
            raise ValueError("Email already verified")

        token = secrets.token_urlsafe(32)
        key = f"email_verification:{token}"
        await self.redis.setex(key, self.expire_hours * 3600, str(user_id))

        verification_url = f"{self.settings.frontend_url}/verify-email?token={token}"
        await self.email_service.send_verification_email(
            to_email=user.email,
            verification_url=verification_url,
            username=user.username or user.full_name,
        )
        return token

    async def verify_email(self, token: str) -> bool:
        """Validate token and mark user as verified."""
        key = f"email_verification:{token}"
        user_id_bytes = await self.redis.get(key)
        if not user_id_bytes:
            return False

        user_id = uuid.UUID(user_id_bytes.decode() if isinstance(user_id_bytes, bytes) else user_id_bytes)
        result = await self.session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            return False
        if user.is_verified:
            await self.redis.delete(key)
            return True

        user.is_verified = True
        user.verification_token = None
        user.verification_token_expires_at = None
        await self.session.commit()
        await self.redis.delete(key)
        return True



