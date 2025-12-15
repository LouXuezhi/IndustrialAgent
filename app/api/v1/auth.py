from __future__ import annotations

import bcrypt
import secrets
import uuid
from datetime import datetime

import jwt
from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.email import EmailService
from app.core.response import StandardResponse
from app.core.security import (
    bearer_scheme,
    create_access_token,
    get_current_user,
    revoke_token,
)
from app.deps import get_db_session, get_redis
from app.db.models import User, DocumentLibrary, Document, Chunk
from app.users.email_verification import EmailVerificationService

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
    role: str | None = Field(
        default=None,
        description="用户角色，可选值: operator, maintenance, manager。不能设置为 admin"
    )


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
    email: EmailStr
    code: str = Field(min_length=6, max_length=6, description="6位数字验证码")


class ResendRequest(BaseModel):
    email: EmailStr


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirmRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=6, description="新密码，至少6位")


def _personal_library_name(user: User) -> str:
    """Construct a default personal library name."""
    base = user.full_name or user.username or user.email.split("@")[0]
    return f"{base}的个人库"


# 允许注册的角色列表（不包括 admin）
ALLOWED_REGISTER_ROLES = {"operator", "maintenance", "manager"}


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

    # 验证和设置角色
    if payload.role:
        # 禁止注册为管理员
        if payload.role.lower() == "admin":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot register as admin. Admin role must be assigned by existing administrators."
            )
        # 验证角色是否在允许列表中
        if payload.role.lower() not in ALLOWED_REGISTER_ROLES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role. Allowed roles: {', '.join(ALLOWED_REGISTER_ROLES)}"
            )
        user_role = payload.role.lower()
    else:
        # 默认角色为 operator
        user_role = "operator"

    # 检查是否启用邮箱验证（如果配置了 SMTP 密码，则启用邮箱验证）
    enable_email_verification = bool(settings.aliyun_smtp_password)
    
    user = User(
        email=payload.email,
        username=payload.username,
        full_name=payload.full_name,
        password_hash=_hash_password(payload.password),
        role=user_role,
        is_verified=not enable_email_verification,  # 如果启用邮箱验证，初始为未验证
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    
    # 如果启用了邮箱验证，发送验证邮件
    if enable_email_verification:
        try:
            import logging
            logger = logging.getLogger(__name__)
            # 直接创建 Redis 客户端用于发送邮件（不通过依赖注入）
            import redis.asyncio as redis
            redis_client = redis.from_url(settings.redis_url, decode_responses=False)
            try:
                email_service = EmailService(settings)
                verification_service = EmailVerificationService(
                    session=session,
                    settings=settings,
                    email_service=email_service,
                    redis_client=redis_client,
                )
                await verification_service.send_verification_code(user.id)
            finally:
                await redis_client.aclose()
        except Exception as e:
            # 记录错误但不影响注册流程
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to send verification email to {payload.email}: {e}")

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
            "is_verified": user.is_verified,  # 返回实际的验证状态
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
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
    redis_client=Depends(get_redis),
) -> StandardResponse[dict]:
    """
    验证邮箱。
    
    使用注册或重新发送验证邮件时收到的6位数字验证码来验证邮箱。
    验证码5分钟内有效。
    """
    # 检查邮箱服务是否配置
    if not settings.aliyun_smtp_password:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email service is not configured"
        )
    
    email_service = EmailService(settings)
    verification_service = EmailVerificationService(
        session=session,
        settings=settings,
        email_service=email_service,
        redis_client=redis_client,
    )
    
    success = await verification_service.verify_email(payload.email, payload.code)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code"
        )
    
    return StandardResponse(data={"verified": True, "message": "Email verified successfully"})


@router.post("/resend-verification")
async def resend_verification(
    payload: ResendRequest,
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
    redis_client=Depends(get_redis),
) -> StandardResponse[dict]:
    """
    重新发送验证码邮件。
    
    如果用户没有收到验证码或验证码已过期，可以使用此接口重新发送。
    验证码5分钟内有效。
    """
    # 检查邮箱服务是否配置
    if not settings.aliyun_smtp_password:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email service is not configured"
        )
    
    result = await session.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if not user:
        # 为了安全，即使用户不存在也返回成功（防止邮箱枚举）
        return StandardResponse(
            data={"message": "If the email exists and is not verified, a verification code has been sent"}
        )
    
    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    email_service = EmailService(settings)
    verification_service = EmailVerificationService(
        session=session,
        settings=settings,
        email_service=email_service,
        redis_client=redis_client,
    )
    
    try:
        await verification_service.send_verification_code(user.id)
        return StandardResponse(
            data={"message": "If the email exists and is not verified, a verification code has been sent"}
        )
    except ValueError as e:
        # 处理冷却期限制
        error_msg = str(e)
        if "wait" in error_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=error_msg
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send verification email: {str(e)}"
        )


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


@router.post("/forgot-password")
async def forgot_password(
    payload: PasswordResetRequest,
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
    redis_client=Depends(get_redis),
) -> StandardResponse[dict]:
    """
    发送密码重置邮件。
    
    用户忘记密码时，可以通过此接口发送密码重置链接到注册邮箱。
    """
    # 检查邮箱服务是否配置
    if not settings.aliyun_smtp_password:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email service is not configured"
        )
    
    result = await session.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()
    if not user:
        # 为了安全，即使用户不存在也返回成功（防止邮箱枚举）
        return StandardResponse(
            data={"message": "If the email exists, a password reset link has been sent"}
        )
    
    # 生成重置令牌
    token = secrets.token_urlsafe(32)
    key = f"password_reset:{token}"
    await redis_client.setex(key, 3600, str(user.id))  # 1小时有效
    
    # 发送重置邮件
    reset_url = f"{settings.frontend_url}/reset-password?token={token}"
    email_service = EmailService(settings)
    
    try:
        success = await email_service.send_password_reset_email(
            to_email=user.email,
            reset_url=reset_url,
            username=user.username or user.full_name,
        )
        if not success:
            await redis_client.delete(key)  # 发送失败，删除令牌
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send password reset email"
            )
    except Exception as e:
        await redis_client.delete(key)  # 发送失败，删除令牌
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send password reset email: {str(e)}"
        )
    
    return StandardResponse(
        data={"message": "If the email exists, a password reset link has been sent"}
    )


@router.post("/reset-password")
async def reset_password(
    payload: PasswordResetConfirmRequest,
    session: AsyncSession = Depends(get_db_session),
    redis_client=Depends(get_redis),
) -> StandardResponse[dict]:
    """
    重置密码。
    
    使用忘记密码接口收到的 token 来重置密码。
    """
    key = f"password_reset:{payload.token}"
    user_id_bytes = await redis_client.get(key)
    if not user_id_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    user_id = uuid.UUID(user_id_bytes.decode() if isinstance(user_id_bytes, bytes) else user_id_bytes)
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        await redis_client.delete(key)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # 更新密码
    user.password_hash = _hash_password(payload.new_password)
    await session.commit()
    await redis_client.delete(key)
    
    return StandardResponse(data={"message": "Password reset successfully"})


class AccountInfoResponse(BaseModel):
    """账号信息响应"""
    id: str
    email: str
    username: str | None = None
    full_name: str | None = None
    role: str
    is_active: bool
    is_verified: bool
    created_at: str
    last_login_at: str | None = None
    # 统计信息
    library_count: int = 0
    document_count: int = 0
    group_count: int = 0


@router.get("/account", response_model=StandardResponse[AccountInfoResponse])
async def get_account_info(
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[AccountInfoResponse]:
    """
    获取当前登录用户的账号信息。
    
    返回用户基本信息、状态和统计数据（文档库数量、文档数量、群组数量等）。
    """
    from sqlalchemy import select, func
    from app.db.models import DocumentLibrary, Document, GroupMember
    
    # 统计用户拥有的文档库数量
    libraries_count_result = await session.execute(
        select(func.count(DocumentLibrary.id)).where(
            DocumentLibrary.owner_type == "user",
            DocumentLibrary.owner_id == current_user.id
        )
    )
    library_count = libraries_count_result.scalar() or 0
    
    # 统计用户拥有的文档数量（通过文档库）
    library_ids_result = await session.execute(
        select(DocumentLibrary.id).where(
            DocumentLibrary.owner_type == "user",
            DocumentLibrary.owner_id == current_user.id
        )
    )
    library_ids = [lib_id for lib_id in library_ids_result.scalars().all()]
    
    document_count = 0
    if library_ids:
        documents_count_result = await session.execute(
            select(func.count(Document.id)).where(Document.library_id.in_(library_ids))
        )
        document_count = documents_count_result.scalar() or 0
    
    # 统计用户加入的群组数量
    groups_count_result = await session.execute(
        select(func.count(GroupMember.id)).where(GroupMember.user_id == current_user.id)
    )
    group_count = groups_count_result.scalar() or 0
    
    return StandardResponse(
        data=AccountInfoResponse(
            id=str(current_user.id),
            email=current_user.email,
            username=current_user.username,
            full_name=current_user.full_name,
            role=current_user.role,
            is_active=current_user.is_active,
            is_verified=current_user.is_verified,
            created_at=current_user.created_at.isoformat() if current_user.created_at else "",
            last_login_at=current_user.last_login_at.isoformat() if current_user.last_login_at else None,
            library_count=library_count,
            document_count=document_count,
            group_count=group_count,
        )
    )


@router.delete("/account", response_model=StandardResponse[dict])
async def delete_own_account(
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
    redis_client=Depends(get_redis),
) -> StandardResponse[dict]:
    """
    删除自己的账号。
    
    此操作会永久删除：
    - 用户账号
    - 用户拥有的所有文档库
    - 文档库中的所有文档和文件
    - 向量数据库中的相关集合
    - 文件系统中的所有文件
    - 用户的群组成员关系
    - 用户的反馈记录
    - Redis 中的相关缓存
    
    此操作不可恢复，请谨慎使用。
    """
    import logging
    import shutil
    from pathlib import Path
    from sqlalchemy import select, delete
    
    logger = logging.getLogger(__name__)
    user_id = current_user.id
    
    try:
        # 1. 获取用户拥有的所有文档库
        libraries_result = await session.execute(
            select(DocumentLibrary).where(
                DocumentLibrary.owner_type == "user",
                DocumentLibrary.owner_id == user_id
            )
        )
        libraries = libraries_result.scalars().all()
        library_ids = [lib.id for lib in libraries]
        
        # 2. 获取这些库中的所有文档
        documents_result = await session.execute(
            select(Document).where(Document.library_id.in_(library_ids))
        )
        documents = documents_result.scalars().all()
        document_ids = [doc.id for doc in documents]
        
        # 3. 收集所有需要删除的文件路径
        file_paths = []
        for doc in documents:
            if doc.source_path:
                file_paths.append(Path(doc.source_path))
        
        # 4. 删除向量数据库中的集合
        try:
            from app.rag.ingestion import DocumentIngestor
            ingestor = DocumentIngestor(settings=settings)
            for library in libraries:
                if library.vector_collection_name:
                    try:
                        ingestor._client.delete_collection(name=library.vector_collection_name)
                        logger.info(f"Deleted vector collection: {library.vector_collection_name}")
                    except Exception as e:
                        logger.warning(f"Failed to delete vector collection {library.vector_collection_name}: {e}")
        except Exception as e:
            logger.warning(f"Failed to delete vector collections: {e}")
        
        # 5. 删除文件系统中的文件
        deleted_files = 0
        for file_path in file_paths:
            try:
                if file_path.exists():
                    file_path.unlink()
                    deleted_files += 1
                    logger.info(f"Deleted file: {file_path}")
            except Exception as e:
                logger.warning(f"Failed to delete file {file_path}: {e}")
        
        # 6. 删除数据库记录（级联删除会处理相关数据）
        # 先删除 chunks
        if document_ids:
            await session.execute(
                delete(Chunk).where(Chunk.document_id.in_(document_ids))
            )
        
        # 删除 documents
        if document_ids:
            await session.execute(
                delete(Document).where(Document.id.in_(document_ids))
            )
        
        # 删除 libraries
        if library_ids:
            await session.execute(
                delete(DocumentLibrary).where(DocumentLibrary.id.in_(library_ids))
            )
        
        # 删除群组成员关系
        from app.db.models import GroupMember
        await session.execute(
            delete(GroupMember).where(GroupMember.user_id == user_id)
        )
        
        # 删除反馈记录
        from app.db.models import Feedback
        await session.execute(
            delete(Feedback).where(Feedback.user_id == user_id)
        )
        
        # 7. 清理 Redis 缓存
        try:
            # 清理搜索缓存
            from app.core.cache import invalidate_search_cache
            for library_id in library_ids:
                try:
                    await invalidate_search_cache(redis_client, library_id=str(library_id))
                except Exception as e:
                    logger.warning(f"Failed to invalidate cache for library {library_id}: {e}")
            
            # 清理用户相关的验证码和token
            user_email = current_user.email
            # 删除邮箱验证码
            await redis_client.delete(f"email_verification_code:{user_email}")
            await redis_client.delete(f"email_verification_user:{user_email}")
            
            # 删除密码重置token（使用 SCAN 查找匹配的键）
            async for key in redis_client.scan_iter(match="password_reset:*"):
                # 检查 token 对应的用户ID是否匹配
                user_id_bytes = await redis_client.get(key)
                if user_id_bytes:
                    stored_user_id = user_id_bytes.decode() if isinstance(user_id_bytes, bytes) else user_id_bytes
                    if stored_user_id == str(user_id):
                        await redis_client.delete(key)
            
            # 清理 JWT 黑名单（如果有）
            # JWT 黑名单通常使用 jti，这里我们清理所有可能相关的键
            # 实际实现中，JWT 黑名单会在 token 过期后自动清理，这里不需要特别处理
        except Exception as e:
            logger.warning(f"Failed to clean Redis cache: {e}")
        
        # 8. 删除用户记录
        await session.delete(current_user)
        await session.commit()
        
        logger.info(f"User account deleted: {user_id}, deleted {len(libraries)} libraries, {len(documents)} documents, {deleted_files} files")
        
        return StandardResponse(
            data={
                "deleted": True,
                "user_id": str(user_id),
                "libraries_deleted": len(libraries),
                "documents_deleted": len(documents),
                "files_deleted": deleted_files,
            }
        )
    except Exception as e:
        await session.rollback()
        logger.error(f"Failed to delete user account {user_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete account: {str(e)}"
        )

