from __future__ import annotations

import bcrypt
import uuid
from datetime import datetime

import jwt
from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.response import StandardResponse
from app.core.security import (
    bearer_scheme,
    create_access_token,
    get_current_user,
    revoke_token,
)
from app.deps import get_db_session, get_redis
from app.db.models import User, DocumentLibrary

router = APIRouter(tags=["auth"])


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    username: str | None = None
    full_name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str
    is_verified: bool


class VerifyEmailRequest(BaseModel):
    token: str


class ResendRequest(BaseModel):
    email: EmailStr


def _personal_library_name(user: User) -> str:
    """Construct a default personal library name."""
    base = user.full_name or user.username or user.email.split("@")[0]
    return f"{base}的个人库"


@router.post("/register")
async def register(
    payload: RegisterRequest,
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> StandardResponse[dict]:
    # Check if email already exists
    email_result = await session.execute(select(User).where(User.email == payload.email))
    if email_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    
    # Check if username already exists
    username_result = await session.execute(select(User).where(User.username == payload.username))
    if username_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")

    user = User(
        email=payload.email,
        username=payload.username,
        full_name=payload.full_name,
        password_hash=_hash_password(payload.password),
        role="operator",
        is_verified=True,  # 邮箱验证可选，注册即标记为已验证
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    # Create a personal default library for the user
    personal_library = DocumentLibrary(
        name=_personal_library_name(user),
        description="个人默认文档库",
        owner_id=user.id,
        owner_type="user",
        is_default=True,  # 标记为默认库，不允许删除
        # vector_collection_name will be set after library.id is generated
    )
    session.add(personal_library)
    await session.flush()  # Flush to get library.id
    personal_library.vector_collection_name = f"library_{personal_library.id}"  # Use library.id, not user.id
    await session.commit()
    await session.refresh(personal_library)

    return StandardResponse(
        data={
            "user_id": str(user.id),
            "is_verified": True,
            "default_library_id": str(personal_library.id),
        }
    )


@router.post("/login")
async def login(
    payload: LoginRequest,
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> StandardResponse[TokenResponse]:
    result = await session.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid credentials")
    if not _verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid credentials")

    user.last_login_at = datetime.utcnow()  # type: ignore[name-defined]
    await session.commit()

    expires_minutes = settings.access_token_expires_minutes
    access_token = create_access_token(
        user_id=str(user.id),
        settings=settings,
        expires_minutes=expires_minutes,
        extra_claims={"email": user.email, "role": user.role},
    )

    return StandardResponse(
        data=TokenResponse(
            access_token=access_token,
            expires_in=expires_minutes * 60,
            user_id=str(user.id),
            is_verified=user.is_verified,
        )
    )


@router.post("/verify-email")
async def verify_email(
    payload: VerifyEmailRequest,
) -> StandardResponse[dict]:
    # Email verification temporarily disabled
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Email verification disabled")


@router.post("/resend-verification")
async def resend_verification(
    payload: ResendRequest,
) -> StandardResponse[dict]:
    # Email verification temporarily disabled
    raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Email verification disabled")


@router.post("/refresh")
async def refresh_token(
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> StandardResponse[TokenResponse]:
    expires_minutes = settings.access_token_expires_minutes
    access_token = create_access_token(
        user_id=str(current_user.id),
        settings=settings,
        expires_minutes=expires_minutes,
        extra_claims={"email": current_user.email, "role": current_user.role},
    )
    return StandardResponse(
        data=TokenResponse(
            access_token=access_token,
            expires_in=expires_minutes * 60,
            user_id=str(current_user.id),
            is_verified=current_user.is_verified,
        )
    )


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
    redis_client=Depends(get_redis),
) -> StandardResponse[dict]:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    token = credentials.credentials
    try:
        payload = jwt.decode(token, (get_settings()).jwt_secret, algorithms=[(get_settings()).jwt_algorithm])
        jti = payload.get("jti")
        exp = payload.get("exp")
        if jti:
            await revoke_token(redis_client, jti, exp)
    except jwt.InvalidTokenError:
        pass

    return StandardResponse(data={"message": "logged out"})

