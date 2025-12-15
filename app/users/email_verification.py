"""Email verification service."""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta

import redis.asyncio as redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.email import EmailService
from app.db.models import User


class EmailVerificationService:
    """Handles email verification code generation and validation."""

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
        self.code_expire_minutes = 5  # 验证码5分钟有效
        self.resend_cooldown_seconds = 300  # 重发邮件冷却时间：5分钟（300秒）

    async def send_verification_code(self, user_id: uuid.UUID) -> str:
        """Generate verification code, store in Redis, and send email."""
        result = await self.session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("User not found")
        if user.is_verified:
            raise ValueError("Email already verified")

        # 检查是否在冷却期内（5分钟内）
        cooldown_key = f"email_verification_cooldown:{user.email}"
        last_sent_time_bytes = await self.redis.get(cooldown_key)
        if last_sent_time_bytes:
            last_sent_time = int(last_sent_time_bytes.decode() if isinstance(last_sent_time_bytes, bytes) else last_sent_time_bytes)
            current_time = int(datetime.now().timestamp())
            elapsed_seconds = current_time - last_sent_time
            remaining_seconds = self.resend_cooldown_seconds - elapsed_seconds
            
            if remaining_seconds > 0:
                raise ValueError(f"Please wait {remaining_seconds} seconds before requesting another verification code")

        # 生成6位数字验证码
        code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        key = f"email_verification_code:{user.email}"
        
        # 存储验证码，5分钟有效
        await self.redis.setex(key, self.code_expire_minutes * 60, code)
        
        # 同时存储用户ID，用于验证时查找用户
        user_id_key = f"email_verification_user:{user.email}"
        await self.redis.setex(user_id_key, self.code_expire_minutes * 60, str(user_id))
        
        # 记录发送时间，设置5分钟冷却期
        current_time = int(datetime.now().timestamp())
        await self.redis.setex(cooldown_key, self.resend_cooldown_seconds, str(current_time))

        # 发送验证码邮件
        await self.email_service.send_verification_code(
            to_email=user.email,
            code=code,
            username=user.username or user.full_name,
        )
        return code

    async def verify_email(self, email: str, code: str) -> bool:
        """Validate verification code and mark user as verified."""
        key = f"email_verification_code:{email}"
        stored_code_bytes = await self.redis.get(key)
        if not stored_code_bytes:
            return False
        
        stored_code = stored_code_bytes.decode() if isinstance(stored_code_bytes, bytes) else stored_code_bytes
        if stored_code != code:
            return False

        # 获取用户ID
        user_id_key = f"email_verification_user:{email}"
        user_id_bytes = await self.redis.get(user_id_key)
        if not user_id_bytes:
            return False
        
        user_id = uuid.UUID(user_id_bytes.decode() if isinstance(user_id_bytes, bytes) else user_id_bytes)
        result = await self.session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            # 清理 Redis
            await self.redis.delete(key)
            await self.redis.delete(user_id_key)
            return False
        
        if user.is_verified:
            # 已经验证过，清理 Redis
            await self.redis.delete(key)
            await self.redis.delete(user_id_key)
            return True

        # 标记为已验证
        user.is_verified = True
        user.verification_token = None
        user.verification_token_expires_at = None
        await self.session.commit()
        
        # 清理 Redis
        await self.redis.delete(key)
        await self.redis.delete(user_id_key)
        return True



