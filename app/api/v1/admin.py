import time
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.response import StandardResponse
from app.core.security import require_admin
from app.db.models import User, DocumentLibrary
from app.deps import get_db_session

router = APIRouter(prefix="/admin", tags=["admin"])


class UserResponse(BaseModel):
    id: str
    email: str
    username: str | None = None
    full_name: str | None = None
    role: str
    is_active: bool
    is_verified: bool
    created_at: str
    last_login_at: str | None = None


class CreateUserRequest(BaseModel):
    """管理员创建用户请求"""
    email: EmailStr
    password: str = Field(min_length=6, description="密码，至少6位")
    username: str | None = Field(default=None, description="用户名（可选）")
    full_name: str | None = Field(default=None, description="全名（可选）")
    role: str = Field(
        default="operator",
        description="用户角色，可选值: operator, maintenance, manager, admin"
    )
    is_active: bool = Field(default=True, description="是否激活")
    is_verified: bool = Field(default=True, description="是否已验证（管理员创建的用户默认已验证）")


class UpdateUserRequest(BaseModel):
    """管理员更新用户请求"""
    username: str | None = None
    full_name: str | None = None
    role: str | None = None
    is_active: bool | None = None
    is_verified: bool | None = None
    password: str | None = Field(default=None, min_length=6, description="新密码（可选）")


@router.get("/healthz")
async def healthz() -> dict[str, str]:
    return {"status": "healthy", "timestamp": str(time.time())}


@router.get("/ping")
async def ping() -> dict[str, str]:
    return {"message": "pong"}


@router.get("/users", response_model=StandardResponse[list[UserResponse]])
async def list_all_users(
    limit: int = Query(default=50, ge=1, le=200, description="每页数量"),
    offset: int = Query(default=0, ge=0, description="偏移量"),
    role: str | None = Query(default=None, description="按角色过滤"),
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_admin),
) -> StandardResponse[list[UserResponse]]:
    """
    列出所有已注册用户。仅管理员可访问。
    
    支持分页和按角色过滤。
    """
    # 构建查询
    query = select(User)
    
    # 按角色过滤
    if role:
        query = query.where(User.role == role)
    
    # 排序和分页
    query = query.order_by(User.created_at.desc()).limit(limit).offset(offset)
    
    # 执行查询
    result = await session.execute(query)
    users = result.scalars().all()
    
    # 构建响应
    data = [
        UserResponse(
            id=str(user.id),
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at.isoformat() if user.created_at else "",
            last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
        )
        for user in users
    ]
    
    return StandardResponse(data=data)


@router.get("/users/stats", response_model=StandardResponse[dict])
async def get_user_stats(
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_admin),
) -> StandardResponse[dict]:
    """
    获取用户统计信息。仅管理员可访问。
    """
    # 总用户数
    total_result = await session.execute(select(func.count(User.id)))
    total_users = total_result.scalar() or 0
    
    # 按角色统计
    role_stats_result = await session.execute(
        select(User.role, func.count(User.id))
        .group_by(User.role)
    )
    role_stats = {role: count for role, count in role_stats_result.all()}
    
    # 活跃用户数
    active_result = await session.execute(
        select(func.count(User.id)).where(User.is_active == True)
    )
    active_users = active_result.scalar() or 0
    
    # 已验证用户数
    verified_result = await session.execute(
        select(func.count(User.id)).where(User.is_verified == True)
    )
    verified_users = verified_result.scalar() or 0
    
    data = {
        "total_users": total_users,
        "active_users": active_users,
        "verified_users": verified_users,
        "role_distribution": role_stats,
    }
    
    return StandardResponse(data=data)


def _hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    import bcrypt
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def _personal_library_name(user: User) -> str:
    """Construct a default personal library name."""
    base = user.full_name or user.username or user.email.split("@")[0]
    return f"{base}的个人库"


@router.post("/users", response_model=StandardResponse[UserResponse])
async def create_user(
    payload: CreateUserRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_admin),
) -> StandardResponse[UserResponse]:
    """
    创建新用户（包括管理员账号）。仅管理员可访问。
    
    管理员可以创建任何角色的用户，包括其他管理员。
    """
    # 检查邮箱是否已存在
    email_result = await session.execute(select(User).where(User.email == payload.email))
    if email_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # 检查用户名是否已存在（如果提供了用户名）
    if payload.username:
        username_result = await session.execute(
            select(User).where(User.username == payload.username)
        )
        if username_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
    
    # 验证角色
    valid_roles = {"operator", "maintenance", "manager", "admin"}
    if payload.role.lower() not in valid_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Allowed roles: {', '.join(valid_roles)}"
        )
    
    # 创建用户
    user = User(
        email=payload.email,
        username=payload.username,
        full_name=payload.full_name,
        password_hash=_hash_password(payload.password),
        role=payload.role.lower(),
        is_active=payload.is_active,
        is_verified=payload.is_verified,
    )
    session.add(user)
    await session.flush()  # 获取 user.id
    
    # 创建个人默认文档库
    personal_library = DocumentLibrary(
        name=_personal_library_name(user),
        description="个人默认文档库",
        owner_id=user.id,
        owner_type="user",
        is_default=True,
    )
    session.add(personal_library)
    await session.flush()
    personal_library.vector_collection_name = f"library_{personal_library.id}"
    
    await session.commit()
    await session.refresh(user)
    
    return StandardResponse(
        data=UserResponse(
            id=str(user.id),
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at.isoformat() if user.created_at else "",
            last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
        )
    )


@router.put("/users/{user_id}", response_model=StandardResponse[UserResponse])
async def update_user(
    user_id: uuid.UUID,
    payload: UpdateUserRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_admin),
) -> StandardResponse[UserResponse]:
    """
    更新用户信息。仅管理员可访问。
    
    管理员可以更新任何用户的信息，包括角色、密码等。
    """
    # 获取用户
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # 检查用户名冲突（如果更新用户名）
    if payload.username and payload.username != user.username:
        username_result = await session.execute(
            select(User).where(User.username == payload.username)
        )
        if username_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        user.username = payload.username
    
    # 更新字段
    if payload.full_name is not None:
        user.full_name = payload.full_name
    if payload.role is not None:
        valid_roles = {"operator", "maintenance", "manager", "admin"}
        if payload.role.lower() not in valid_roles:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role. Allowed roles: {', '.join(valid_roles)}"
            )
        user.role = payload.role.lower()
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.is_verified is not None:
        user.is_verified = payload.is_verified
    if payload.password:
        user.password_hash = _hash_password(payload.password)
    
    await session.commit()
    await session.refresh(user)
    
    return StandardResponse(
        data=UserResponse(
            id=str(user.id),
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            is_verified=user.is_verified,
            created_at=user.created_at.isoformat() if user.created_at else "",
            last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
        )
    )


@router.delete("/users/{user_id}", response_model=StandardResponse[dict])
async def delete_user(
    user_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(require_admin),
) -> StandardResponse[dict]:
    """
    删除用户。仅管理员可访问。
    
    注意：删除用户会同时删除其个人文档库和相关数据。
    不能删除自己。
    """
    # 获取用户
    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # 防止删除自己
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete yourself"
        )
    
    # 删除用户（级联删除会处理相关数据）
    await session.delete(user)
    await session.commit()
    
    return StandardResponse(data={"deleted": True, "user_id": str(user_id)})

