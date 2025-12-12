# 用户管理模块文档

## 概述
用户管理模块负责用户认证、授权、角色管理和权限控制。支持基于角色的访问控制（RBAC），角色不仅影响权限，还影响Agent的prompt选择。

## 模块结构

```
app/users/
├── models.py          # 用户、群组、权限数据模型
├── auth.py            # 认证服务（JWT、API Key）
├── email_verification.py  # 邮箱验证服务
├── permissions.py     # 权限检查服务（RBAC）
├── roles.py           # 角色定义和管理
└── crud.py            # 用户相关CRUD操作
```

## 1. 数据模型 (`models.py`)

### User（用户表，扩展）

**表名**: `users`

**字段**:
- `id` (UUID, Primary Key): 用户唯一标识
- `email` (String(255), Unique): 用户邮箱（唯一，用于登录）
- `username` (String(64), Unique): 用户名（可选）
- `password_hash` (String(255)): 密码哈希（bcrypt）
- `role` (Enum): 用户角色（`operator` | `maintenance` | `manager` | `admin`）
- `full_name` (String(255), Optional): 全名
- `is_active` (Boolean): 是否激活（默认True）
- `is_verified` (Boolean): 邮箱是否验证（默认False）
- `metadata` (JSON): 扩展元数据（部门、职位等）
- `created_at` (DateTime): 创建时间
- `last_login_at` (DateTime, Optional): 最后登录时间

**关系**:
- `owned_libraries`: 一对多关系，用户拥有的文档库
- `group_memberships`: 一对多关系，用户加入的群组
- `feedback`: 一对多关系，用户反馈记录

### Group（群组表）

**表名**: `groups`

**字段**:
- `id` (UUID, Primary Key): 群组唯一标识
- `name` (String(255)): 群组名称
- `description` (Text, Optional): 描述信息
- `owner_id` (UUID, Foreign Key): 群组所有者（管理员）
- `type` (Enum): 群组类型（`department` | `project` | `team` | `custom`）
- `metadata` (JSON): 扩展元数据
- `created_at` (DateTime): 创建时间
- `updated_at` (DateTime): 更新时间

**关系**:
- `members`: 一对多关系，群组成员
- `libraries`: 一对多关系，群组关联的文档库

### GroupMember（群组成员表）

**表名**: `group_members`

**字段**:
- `id` (UUID, Primary Key)
- `group_id` (UUID, Foreign Key): 群组ID
- `user_id` (UUID, Foreign Key): 用户ID
- `role` (Enum): 成员角色（`member` | `admin`）
- `joined_at` (DateTime): 加入时间

**唯一约束**: `(group_id, user_id)`

**关系**:
- `group`: 多对一关系，关联到Group表
- `user`: 多对一关系，关联到User表

### RolePermission（角色权限关联表）

**表名**: `role_permissions`

**字段**:
- `id` (UUID, Primary Key)
- `role` (Enum): 角色名称
- `permission` (String(64)): 权限名称
- `resource_type` (String(64), Optional): 资源类型（`library` | `group` | `document`）
- `created_at` (DateTime): 创建时间

**唯一约束**: `(role, permission, resource_type)`

### 数据模型定义示例

```python
from enum import Enum
from sqlalchemy import Boolean, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

class UserRole(str, Enum):
    OPERATOR = "operator"
    MAINTENANCE = "maintenance"
    MANAGER = "manager"
    ADMIN = "admin"

class GroupType(str, Enum):
    DEPARTMENT = "department"
    PROJECT = "project"
    TEAM = "team"
    CUSTOM = "custom"

class MemberRole(str, Enum):
    MEMBER = "member"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), default=UserRole.OPERATOR)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
    last_login_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    
    # 关系
    owned_libraries: Mapped[list["DocumentLibrary"]] = relationship(back_populates="owner")
    group_memberships: Mapped[list["GroupMember"]] = relationship(back_populates="user")
    feedback: Mapped[list["Feedback"]] = relationship(back_populates="user")

class Group(Base):
    __tablename__ = "groups"
    
    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("users.id"), nullable=False)
    type: Mapped[GroupType] = mapped_column(SQLEnum(GroupType), default=GroupType.CUSTOM)
    metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow)
    
    # 关系
    members: Mapped[list["GroupMember"]] = relationship(back_populates="group")
    libraries: Mapped[list["GroupLibrary"]] = relationship(back_populates="group")

class GroupMember(Base):
    __tablename__ = "group_members"
    
    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    group_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("groups.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("users.id"), nullable=False)
    role: Mapped[MemberRole] = mapped_column(SQLEnum(MemberRole), default=MemberRole.MEMBER)
    joined_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
    
    # 关系
    group: Mapped["Group"] = relationship(back_populates="members")
    user: Mapped["User"] = relationship(back_populates="group_memberships")
    
    __table_args__ = (
        UniqueConstraint("group_id", "user_id", name="uq_group_member"),
        Index("idx_group_member_user", "user_id"),
    )
```

## 2. 角色定义 (`roles.py`)

### 角色系统

角色不仅定义权限，还影响Agent的prompt选择和行为。

### 角色定义

```python
from dataclasses import dataclass
from typing import Final

@dataclass
class RoleDefinition:
    name: str
    display_name: str
    description: str
    permissions: list[str]  # 权限列表
    prompt_style: str  # Prompt风格描述
    default_prompt_template: str  # 默认prompt模板名称

# 角色定义
ROLES: Final[dict[str, RoleDefinition]] = {
    "operator": RoleDefinition(
        name="operator",
        display_name="运维技术人员",
        description="负责日常设备运维和技术操作",
        permissions=[
            "library:read",
            "document:read",
            "group:read",
        ],
        prompt_style="技术细节、操作步骤、故障排查",
        default_prompt_template="operator"
    ),
    "maintenance": RoleDefinition(
        name="maintenance",
        display_name="维护工程师",
        description="负责设备维护和故障处理",
        permissions=[
            "library:read",
            "library:write",
            "document:read",
            "document:write",
            "group:read",
            "group:write",
        ],
        prompt_style="维护流程、故障排查、预防性维护",
        default_prompt_template="maintenance"
    ),
    "manager": RoleDefinition(
        name="manager",
        display_name="工厂管理者",
        description="负责生产管理和决策支持",
        permissions=[
            "library:read",
            "library:write",
            "library:manage",
            "document:read",
            "document:write",
            "group:read",
            "group:write",
            "group:manage",
        ],
        prompt_style="决策支持、数据分析、战略规划",
        default_prompt_template="manager"
    ),
    "admin": RoleDefinition(
        name="admin",
        display_name="系统管理员",
        description="系统管理和配置",
        permissions=[
            "*",  # 所有权限
        ],
        prompt_style="系统管理、配置优化",
        default_prompt_template="admin"
    ),
}

def get_role_definition(role_name: str) -> RoleDefinition | None:
    """获取角色定义"""
    return ROLES.get(role_name)

def get_role_permissions(role_name: str) -> list[str]:
    """获取角色的权限列表"""
    role = get_role_definition(role_name)
    return role.permissions if role else []

def has_permission(role_name: str, permission: str) -> bool:
    """检查角色是否有特定权限"""
    permissions = get_role_permissions(role_name)
    if "*" in permissions:
        return True
    return permission in permissions
```

### 权限定义

```python
# 权限常量定义
PERMISSIONS = {
    # 文档库权限
    "library:read": "读取文档库",
    "library:write": "写入文档库",
    "library:delete": "删除文档库",
    "library:manage": "管理文档库（添加成员等）",
    
    # 文档权限
    "document:read": "读取文档",
    "document:write": "写入文档",
    "document:delete": "删除文档",
    
    # 群组权限
    "group:read": "读取群组信息",
    "group:write": "写入群组内容",
    "group:manage": "管理群组（添加成员等）",
    "group:create": "创建群组",
    
    # 系统权限
    "system:admin": "系统管理",
    "system:config": "系统配置",
}
```

## 3. 认证服务 (`auth.py`)

### AuthService类

**职责**: 处理用户认证（登录、注册、JWT令牌管理）

### 方法列表

#### 1. `async def register(email: str, password: str, role: str = "operator", **kwargs) -> User`
**描述**: 用户注册

**参数**:
- `email`: 邮箱
- `password`: 密码（明文）
- `role`: 角色（默认operator）
- `kwargs`: 其他用户信息（full_name等）

**返回**: User实例

**实现**:
```python
import bcrypt
from jose import jwt
from datetime import datetime, timedelta

class AuthService:
    def __init__(self, session: AsyncSession, settings: Settings):
        self.session = session
        self.settings = settings
        self.secret_key = settings.jwt_secret
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
    
    async def register(
        self,
        email: str,
        password: str,
        role: str = "operator",
        **kwargs
    ) -> User:
        # 1. 检查邮箱是否已存在
        existing = await self.session.execute(
            select(User).where(User.email == email)
        )
        if existing.scalar_one_or_none():
            raise ValueError("Email already registered")
        
        # 2. 哈希密码
        password_hash = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")
        
        # 3. 创建用户
        user = User(
            email=email,
            password_hash=password_hash,
            role=UserRole(role),
            **kwargs
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        
        return user
```

#### 2. `async def authenticate(email: str, password: str) -> User | None`
**描述**: 用户认证（登录）

**参数**:
- `email`: 邮箱
- `password`: 密码（明文）

**返回**: User实例（成功）或None（失败）

**实现**:
```python
async def authenticate(self, email: str, password: str) -> User | None:
    # 1. 查询用户
    result = await self.session.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        return None
    
    # 2. 验证密码
    if not bcrypt.checkpw(
        password.encode("utf-8"),
        user.password_hash.encode("utf-8")
    ):
        return None
    
    # 3. 更新最后登录时间
    user.last_login_at = datetime.utcnow()
    await self.session.commit()
    
    return user
```

#### 3. `def create_access_token(user: User) -> str`
**描述**: 创建JWT访问令牌

**参数**:
- `user`: User实例

**返回**: JWT令牌字符串

**实现**:
```python
def create_access_token(self, user: User) -> str:
    expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
    payload = {
        "sub": str(user.id),  # subject (user ID)
        "email": user.email,
        "role": user.role.value,
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    return token
```

#### 4. `async def verify_token(token: str) -> dict | None`
**描述**: 验证JWT令牌

**参数**:
- `token`: JWT令牌字符串

**返回**: 载荷字典（成功）或None（失败）

## 3.1 邮箱验证服务 (`email_verification.py`)

### EmailVerificationService类

**职责**: 处理邮箱验证流程，包括生成验证令牌、发送验证邮件、验证邮箱

**依赖**: 
- `EmailService` (核心层邮件服务，基于阿里云邮件推送)
- `Redis` (存储验证令牌)

### 方法列表

#### 1. `async def send_verification_email(user_id: uuid.UUID) -> str`
**描述**: 生成验证令牌并发送验证邮件

**参数**:
- `user_id`: 用户ID

**返回**: 验证令牌字符串

**实现流程**:
1. 查询用户信息
2. 检查用户是否已验证
3. 生成安全令牌（secrets.token_urlsafe）
4. 存储到Redis（24小时过期）
5. 生成验证链接（包含前端URL和令牌）
6. 调用EmailService发送验证邮件（使用阿里云邮件推送）

#### 2. `async def verify_email(token: str) -> bool`
**描述**: 验证邮箱地址

**参数**:
- `token`: 验证令牌

**返回**: 是否验证成功

**实现流程**:
1. 从Redis获取用户ID（通过令牌）
2. 查询用户
3. 检查用户状态
4. 更新用户 `is_verified = True`
5. 删除Redis中的令牌

### 实现示例

```python
# app/users/email_verification.py
import secrets
import uuid
from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from app.db.models import User
from app.core.config import Settings
from app.core.email import EmailService

class EmailVerificationService:
    def __init__(
        self,
        session: AsyncSession,
        settings: Settings,
        email_service: EmailService,
        redis_client: redis.Redis
    ):
        self.session = session
        self.settings = settings
        self.email_service = email_service
        self.redis = redis_client
        self.token_expire_hours = 24
    
    async def send_verification_email(self, user_id: uuid.UUID) -> str:
        """生成验证令牌并发送邮件"""
        # 1. 查询用户
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("User not found")
        
        if user.is_verified:
            raise ValueError("Email already verified")
        
        # 2. 生成验证令牌
        token = secrets.token_urlsafe(32)
        
        # 3. 存储到Redis（24小时过期）
        redis_key = f"email_verification:{token}"
        await self.redis.setex(
            redis_key,
            self.token_expire_hours * 3600,
            str(user_id)
        )
        
        # 4. 生成验证链接
        verification_url = f"{self.settings.frontend_url}/verify-email?token={token}"
        
        # 5. 发送验证邮件（使用阿里云邮件推送）
        success = await self.email_service.send_verification_email(
            to_email=user.email,
            verification_url=verification_url,
            username=user.username or user.full_name,
        )
        
        if not success:
            raise ValueError("Failed to send verification email")
        
        return token
    
    async def verify_email(self, token: str) -> bool:
        """验证邮箱"""
        # 1. 从Redis获取用户ID
        redis_key = f"email_verification:{token}"
        user_id_str = await self.redis.get(redis_key)
        
        if not user_id_str:
            return False  # 令牌不存在或已过期
        
        user_id = uuid.UUID(user_id_str.decode())
        
        # 2. 查询用户
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user or user.is_verified:
            return False
        
        # 3. 标记为已验证
        user.is_verified = True
        await self.session.commit()
        
        # 4. 删除Redis中的令牌
        await self.redis.delete(redis_key)
        
        return True
```

### 使用方式

#### 在注册流程中
```python
# app/api/v1/auth.py
from app.users.email_verification import EmailVerificationService
from app.core.email import EmailService
from app.deps import get_email_service

@router.post("/register")
async def register(
    email: str,
    password: str,
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
    email_service: EmailService = Depends(get_email_service),
    redis_client: redis.Redis = Depends(get_redis),
):
    # 1. 创建用户
    auth_service = AuthService(session, settings)
    user = await auth_service.register(email, password)
    
    # 2. 发送验证邮件
    verification_service = EmailVerificationService(
        session, settings, email_service, redis_client
    )
    token = await verification_service.send_verification_email(user.id)
    
    return {"message": "User registered, verification email sent"}
```

#### 验证邮箱
```python
@router.post("/verify-email")
async def verify_email(
    token: str,
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
    email_service: EmailService = Depends(get_email_service),
    redis_client: redis.Redis = Depends(get_redis),
):
    verification_service = EmailVerificationService(
        session, settings, email_service, redis_client
    )
    success = await verification_service.verify_email(token)
    
    if not success:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    
    return {"message": "Email verified successfully"}
```

### 邮件服务说明

邮箱验证使用**阿里云邮件推送**服务发送验证邮件：
- **服务商**: 阿里云
- **免费额度**: 每天200封（需实名认证）
- **超出费用**: 约 ¥0.01/封
- **详细说明**: 参见 [核心层文档 - 邮件发送服务](../05_core_layer.md#4-邮件发送服务-emailpy)

## 4. 权限检查服务 (`permissions.py`)

### PermissionChecker类

**职责**: 提供权限检查的便捷方法

### 方法列表

#### 1. `async def check_permission(user_id: uuid.UUID, permission: str, resource_id: uuid.UUID | None = None, resource_type: str | None = None) -> bool`
**描述**: 检查用户是否有特定权限

**参数**:
- `user_id`: 用户ID
- `permission`: 权限名称
- `resource_id`: 资源ID（可选，用于资源级权限）
- `resource_type`: 资源类型（可选）

**返回**: 是否有权限

**实现**:
```python
class PermissionChecker:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def check_permission(
        self,
        user_id: uuid.UUID,
        permission: str,
        resource_id: uuid.UUID | None = None,
        resource_type: str | None = None
    ) -> bool:
        # 1. 获取用户
        user = await self.session.get(User, user_id)
        if not user or not user.is_active:
            return False
        
        # 2. 检查角色权限
        if has_permission(user.role.value, permission):
            return True
        
        # 3. 检查资源级权限（如果指定了资源）
        if resource_id and resource_type:
            return await self._check_resource_permission(
                user_id, permission, resource_id, resource_type
            )
        
        return False
    
    async def _check_resource_permission(
        self,
        user_id: uuid.UUID,
        permission: str,
        resource_id: uuid.UUID,
        resource_type: str
    ) -> bool:
        if resource_type == "library":
            # 检查文档库权限
            library = await self.session.get(DocumentLibrary, resource_id)
            if library.type == LibraryType.PRIVATE:
                return library.owner_id == user_id
            elif library.type == LibraryType.GROUP:
                # 检查是否是群组成员
                member = await self.session.execute(
                    select(GroupMember)
                    .where(
                        GroupMember.group_id == library.owner_id,
                        GroupMember.user_id == user_id
                    )
                )
                return member.scalar_one_or_none() is not None
        
        return False
```

#### 2. `async def get_user_context(user_id: uuid.UUID) -> UserContext`
**描述**: 获取用户上下文（角色、权限、可访问的文档库）

**返回**: UserContext数据类

**UserContext定义**:
```python
from dataclasses import dataclass

@dataclass
class UserContext:
    user_id: uuid.UUID
    email: str
    role: str
    permissions: list[str]
    accessible_library_ids: list[uuid.UUID]
    group_ids: list[uuid.UUID]
    
    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions or "*" in self.permissions
    
    def can_access_library(self, library_id: uuid.UUID) -> bool:
        return library_id in self.accessible_library_ids
```

## 5. CRUD操作 (`crud.py`)

### 用户相关CRUD函数

#### 1. `async def create_user(session: AsyncSession, **kwargs) -> User`
**描述**: 创建用户

#### 2. `async def get_user_by_email(session: AsyncSession, email: str) -> User | None`
**描述**: 根据邮箱查询用户

#### 3. `async def update_user_role(session: AsyncSession, user_id: uuid.UUID, new_role: str) -> User`
**描述**: 更新用户角色

#### 4. `async def add_user_to_group(session: AsyncSession, user_id: uuid.UUID, group_id: uuid.UUID, role: str = "member") -> GroupMember`
**描述**: 将用户添加到群组

#### 5. `async def remove_user_from_group(session: AsyncSession, user_id: uuid.UUID, group_id: uuid.UUID) -> bool`
**描述**: 从群组移除用户

## 与Agent模块集成

### 用户上下文传递

```python
# 在Agent中
class QAAgent:
    def __init__(self, pipeline: RAGPipeline, user_context: UserContext):
        self.pipeline = pipeline
        self.user_context = user_context
    
    async def run(self, query: str, library_ids: list[uuid.UUID] | None = None, top_k: int = 5):
        # 1. 根据用户角色选择prompt模板
        role = self.user_context.role
        
        # 2. 如果没有指定library_ids，使用用户可访问的所有文档库
        if library_ids is None:
            library_ids = self.user_context.accessible_library_ids
        else:
            # 过滤：只保留用户有权限访问的文档库
            library_ids = [
                lib_id for lib_id in library_ids
                if self.user_context.can_access_library(lib_id)
            ]
        
        # 3. 调用RAG Pipeline（传递角色和文档库范围）
        result = await self.pipeline.run(
            query=query,
            library_ids=library_ids,
            top_k=top_k,
            role=role,  # 用于选择prompt模板
            user_permissions=self.user_context.permissions  # 用于权限过滤
        )
        
        return result
```

## API端点示例

### 用户注册
```python
@router.post("/users/register")
async def register_user(
    email: str,
    password: str,
    role: str = "operator",
    session: AsyncSession = Depends(get_db_session)
):
    auth_service = AuthService(session, settings)
    user = await auth_service.register(email, password, role)
    return {"user_id": str(user.id), "email": user.email}
```

### 用户登录
```python
@router.post("/users/login")
async def login(
    email: str,
    password: str,
    session: AsyncSession = Depends(get_db_session)
):
    auth_service = AuthService(session, settings)
    user = await auth_service.authenticate(email, password)
    if not user:
        raise HTTPException(401, "Invalid credentials")
    
    token = auth_service.create_access_token(user)
    return {"access_token": token, "token_type": "bearer"}
```

### 获取当前用户信息
```python
@router.get("/users/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    permission_checker = PermissionChecker(session)
    context = await permission_checker.get_user_context(current_user.id)
    return {
        "user_id": str(context.user_id),
        "email": context.email,
        "role": context.role,
        "permissions": context.permissions,
        "accessible_libraries": len(context.accessible_library_ids),
        "groups": len(context.group_ids)
    }
```

