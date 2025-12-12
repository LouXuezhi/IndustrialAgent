from __future__ import annotations

import datetime as dt
import uuid
from typing import Any

import jwt
import redis.asyncio as redis
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings, Settings
from app.db.models import User
from app.deps import get_db_session, get_redis

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
bearer_scheme = HTTPBearer(auto_error=False)
TOKEN_BLACKLIST_PREFIX = "jwt:blacklist:"


def get_api_key(
    api_key: str | None = Security(api_key_header), settings: Settings = Depends(get_settings)
) -> str:
    if not api_key or api_key != settings.api_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    return api_key


def create_access_token(
    user_id: str,
    settings: Settings,
    expires_minutes: int | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    expire = dt.datetime.utcnow() + dt.timedelta(
        minutes=expires_minutes or settings.access_token_expires_minutes
    )
    jti = str(uuid.uuid4())
    payload: dict[str, Any] = {"sub": user_id, "exp": expire, "jti": jti}
    if extra_claims:
        payload.update(extra_claims)
    token = jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)
    return token


async def revoke_token(redis_client: redis.Redis, jti: str, exp_ts: int | None) -> None:
    """Add token jti to blacklist until its expiry."""
    ttl_seconds = max(exp_ts - int(dt.datetime.utcnow().timestamp()), 1) if exp_ts else 3600
    key = f"{TOKEN_BLACKLIST_PREFIX}{jti}"
    await redis_client.set(key, "revoked", ex=ttl_seconds)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    session: AsyncSession = Depends(get_db_session),
    redis_client: redis.Redis = Depends(get_redis),
    settings: Settings = Depends(get_settings),
) -> User:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        user_id: str | None = payload.get("sub")
        jti: str | None = payload.get("jti")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    if jti:
        key = f"{TOKEN_BLACKLIST_PREFIX}{jti}"
        try:
            exists = await redis_client.exists(key)
            if exists:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token revoked")
        except Exception:
            # On Redis error, fail safe by allowing; could be tightened if desired.
            pass

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return user

