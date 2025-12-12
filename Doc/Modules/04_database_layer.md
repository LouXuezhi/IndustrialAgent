# 数据库层模块文档

## 概述
数据库层使用 SQLAlchemy 异步栈，当前默认对接 MySQL（兼容 PostgreSQL）。存储文档/库元数据、用户、群组、反馈等实体，并为向量化提供库/文档/块的结构化信息。

## 模块结构

```
app/db/
├── base.py        # SQLAlchemy基类
├── models.py      # 数据模型定义
├── crud.py        # CRUD操作封装
└── session.py     # 数据库会话管理
```

## 1. 基类定义 (`base.py`)

### 功能
定义SQLAlchemy的声明式基类，所有模型继承此类。

### 实现

```python
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
```

### 说明
- 使用SQLAlchemy 2.0的声明式API
- 所有模型类继承 `Base`，自动获得ORM能力

## 2. 数据模型 (`models.py`)

### 功能
定义数据库表结构和关系映射。包括用户、群组、文档库、文档等核心实体。

### 模型列表

#### 1. User（用户表）

**表名**: `users`

**字段**:
- `id` (UUID, Primary Key): 用户唯一标识
- `email` (String(255), Unique): 用户邮箱（唯一，用于登录）
- `username` (String(64), Unique): 用户名（可选）
- `password_hash` (String(255)): 密码哈希（bcrypt）
- `role` (Enum): 用户角色（`operator` | `maintenance` | `manager` | `admin`）
- `full_name` (String(255), Optional): 全名
- `is_active` (Boolean): 是否激活
- `is_verified` (Boolean): 邮箱是否验证
- `metadata` (JSON): 扩展元数据
- `created_at` (DateTime): 创建时间
- `last_login_at` (DateTime, Optional): 最后登录时间

**关系**:
- `owned_libraries`: 一对多关系，用户拥有的文档库
- `group_memberships`: 一对多关系，用户加入的群组
- `feedback`: 一对多关系，用户反馈记录

#### 2. Group（群组表）

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

#### 3. GroupMember（群组成员表）

**表名**: `group_members`

**字段**:
- `id` (UUID, Primary Key)
- `group_id` (UUID, Foreign Key): 群组ID
- `user_id` (UUID, Foreign Key): 用户ID
- `role` (Enum): 成员角色（`member` | `admin`）
- `joined_at` (DateTime): 加入时间

**唯一约束**: `(group_id, user_id)`

#### 4. DocumentLibrary（文档库表）

**表名**: `document_libraries`

**字段（当前实现）**:
- `id` (UUID, PK)
- `name` (String)
- `description` (Text, 可空)
- `owner_id` (UUID, 非空): 拥有者ID
- `owner_type` (String): `"user"` 或 `"group"`，与 `owner_id` 组合区分私库/群库
- `vector_collection_name` (String, 可空): 对应向量库集合名
- `meta` (JSON, 列名仍为 `metadata`): 扩展元数据
- `created_at` (DateTime)

**关系**:
- `documents`: 一对多，库下文档
- `group`: 多对一，仅当 `owner_type='group'` 时指向 `Group`，显式 `primaryjoin` + `foreign_keys` 适配多态 owner

#### 5. Document（文档表）

**表名**: `documents`

**字段（当前实现）**:
- `id` (UUID, PK)
- `title` (String)
- `source_path` (String): 持久化文件路径
- `library_id` (UUID, FK，可空): 所属文档库
- `meta` (JSON, 列名仍为 `metadata`): 包含文件类型、大小、向量化状态等
- `created_at` (DateTime)

**关系**:
- `library`: 多对一，指向 `DocumentLibrary`
- `chunks`: 一对多，指向 `Chunk`

**说明**:
- 上传仅保存原文件与元数据（`vectorized=False`），向量化需显式触发。
- `meta["vectorized"]` 反映是否写入向量库。

#### 2. Chunk（文档块表）

**表名**: `chunks`

**字段（当前实现）**:
- `id` (UUID, PK)
- `document_id` (UUID, FK)
- `content` (Text)
- `meta` (JSON, 列名仍为 `metadata`): 位置信息、offset/length 等

**关系**:
- `document`: 多对一，指向 `Document`

**说明**:
- 向量化时会清理旧块并重建，再写入向量库；失败则 `document.meta["vectorized"]=False`。

#### 3. User（用户表）

**表名**: `users`

**字段**:
- `id` (UUID, Primary Key): 用户唯一标识
- `email` (String(255), Unique): 用户邮箱（唯一）
- `role` (String(64)): 用户角色（operator/maintenance/manager，默认operator）
- `created_at` (DateTime): 创建时间

**用途**: 存储用户信息和角色，用于个性化服务和权限控制

**示例**:
```python
user = User(
    email="operator@example.com",
    role="operator"
)
```

#### 4. Feedback（反馈表）

**表名**: `feedback`

**字段**:
- `id` (UUID, Primary Key): 反馈唯一标识
- `user_id` (UUID, Foreign Key): 用户ID
- `question` (Text): 用户问题
- `answer` (Text): 系统返回的答案
- `rating` (Integer): 评分（通常1-5）
- `metadata` (JSON): 额外元数据（会话ID、时间戳等）
- `created_at` (DateTime): 创建时间

**关系**:
- `user`: 多对一关系，关联到User表（当前未显式定义）

**用途**: 收集用户反馈，用于模型优化和评估

**示例**:
```python
feedback = Feedback(
    user_id=user.id,
    question="如何维护设备？",
    answer="定期检查...",
    rating=5,
    metadata={"session_id": "abc123"}
)
```

### 数据库兼容性

代码使用 `UUIDType` 处理不同数据库的UUID支持：
- PostgreSQL: 使用原生UUID类型
- SQLite: 使用String类型存储UUID字符串

```python
UUIDType = UUID(as_uuid=True) if UUID else String
```

## 3. CRUD操作 (`crud.py`)

### 功能
封装常用的数据库操作，提供类型安全的CRUD函数。

### 函数列表

#### 1. `async def create_document(...) -> models.Document`
**描述**: 创建文档记录

**参数**:
- `session`: 数据库会话
- `title`: 文档标题
- `source_path`: 源文件路径
- `metadata`: 元数据字典（可选）

**返回**: Document模型实例

**示例**:
```python
document = await create_document(
    session,
    title="手册.pdf",
    source_path="/path/to/file.pdf",
    metadata={"size": 1024}
)
```

#### 2. `async def list_documents(session: AsyncSession, limit: int = 50) -> Sequence[models.Document]`
**描述**: 列出文档（分页）

**参数**:
- `session`: 数据库会话
- `limit`: 返回数量限制（默认50）

**返回**: Document模型实例列表

**示例**:
```python
documents = await list_documents(session, limit=10)
```

#### 3. `async def store_feedback(...) -> models.Feedback`
**描述**: 存储用户反馈

**参数**:
- `session`: 数据库会话
- `user_id`: 用户ID
- `question`: 用户问题
- `answer`: 系统答案
- `rating`: 评分（整数）
- `metadata`: 元数据字典（可选）

**返回**: Feedback模型实例

**示例**:
```python
feedback = await store_feedback(
    session,
    user_id=user.id,
    question="如何操作？",
    answer="按照步骤...",
    rating=4,
    metadata={"source": "web"}
)
```

### CRUD扩展建议

可以添加更多CRUD函数：

```python
# 查询单个文档
async def get_document(session: AsyncSession, document_id: uuid.UUID) -> models.Document | None:
    result = await session.execute(
        select(models.Document).where(models.Document.id == document_id)
    )
    return result.scalar_one_or_none()

# 更新文档
async def update_document(
    session: AsyncSession,
    document_id: uuid.UUID,
    **updates
) -> models.Document:
    document = await get_document(session, document_id)
    if document:
        for key, value in updates.items():
            setattr(document, key, value)
        await session.commit()
        await session.refresh(document)
    return document

# 删除文档
async def delete_document(session: AsyncSession, document_id: uuid.UUID) -> bool:
    document = await get_document(session, document_id)
    if document:
        await session.delete(document)
        await session.commit()
        return True
    return False

# 查询文档块
async def get_chunks_by_document(
    session: AsyncSession,
    document_id: uuid.UUID
) -> Sequence[models.Chunk]:
    result = await session.execute(
        select(models.Chunk).where(models.Chunk.document_id == document_id)
    )
    return result.scalars().all()

# 查询用户反馈
async def list_feedback(
    session: AsyncSession,
    user_id: uuid.UUID | None = None,
    limit: int = 50
) -> Sequence[models.Feedback]:
    query = select(models.Feedback)
    if user_id:
        query = query.where(models.Feedback.user_id == user_id)
    query = query.order_by(models.Feedback.created_at.desc()).limit(limit)
    result = await session.execute(query)
    return result.scalars().all()
```

## 4. 会话管理 (`session.py`)

### 功能
管理数据库连接和异步会话生命周期。

### 实现

```python
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# 创建异步引擎
engine = create_async_engine(
    settings.database_url,
    echo=False,        # 是否打印SQL（开发时可设为True）
    future=True        # 使用2.0风格API
)

# 创建会话工厂
async_session = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,  # 提交后不使对象过期
    class_=AsyncSession
)

# 便捷函数
async def get_db() -> AsyncSession:
    async with async_session() as session:
        yield session
```

### 配置说明

**database_url格式**:
- SQLite: `sqlite+aiosqlite:///./industrial_qa.db`
- PostgreSQL: `postgresql+asyncpg://user:password@localhost/dbname`
- MySQL: `mysql+aiomysql://user:password@localhost/dbname`

### 会话使用模式

#### 模式1: 上下文管理器（推荐）
```python
async with async_session() as session:
    document = await create_document(session, ...)
    # 自动提交和关闭
```

#### 模式2: 依赖注入（FastAPI）
```python
from app.deps import get_db_session

@router.post("/docs")
async def create_doc(session: AsyncSession = Depends(get_db_session)):
    document = await create_document(session, ...)
    # 依赖注入自动管理会话生命周期
```

#### 模式3: 手动管理
```python
session = async_session()
try:
    document = await create_document(session, ...)
    await session.commit()
except Exception:
    await session.rollback()
    raise
finally:
    await session.close()
```

## 数据库迁移

### Alembic配置

项目使用Alembic进行数据库迁移管理。

**初始化**:
```bash
alembic init alembic
```

**创建迁移**:
```bash
alembic revision --autogenerate -m "Initial schema"
```

**应用迁移**:
```bash
alembic upgrade head
```

**回滚迁移**:
```bash
alembic downgrade -1
```

### 迁移文件示例

```python
# alembic/versions/001_initial_schema.py
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    op.create_table(
        'documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('source_path', sa.String(512), nullable=False),
        sa.Column('metadata', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
    )
    # ... 其他表

def downgrade():
    op.drop_table('documents')
    # ... 其他表
```

## 性能优化建议

1. **索引优化**:
   - 在 `email` 字段创建唯一索引（已通过unique约束实现）
   - 在 `document_id` 外键字段创建索引
   - 在 `created_at` 字段创建索引（用于时间范围查询）

2. **连接池配置**:
```python
engine = create_async_engine(
    settings.database_url,
    pool_size=20,           # 连接池大小
    max_overflow=10,        # 最大溢出连接数
    pool_pre_ping=True,     # 连接前ping检查
    pool_recycle=3600       # 连接回收时间（秒）
)
```

3. **查询优化**:
   - 使用 `select_related` 或 `joinedload` 避免N+1查询
   - 使用分页避免一次性加载大量数据
   - 使用批量操作（bulk insert/update）

4. **异步优化**:
   - 确保所有数据库操作使用异步方法
   - 避免在异步上下文中使用同步操作
   - 使用 `asyncio.gather` 并行执行多个查询

## 数据一致性

### 事务管理
- 使用 `session.commit()` 提交事务
- 使用 `session.rollback()` 回滚事务
- 在异常处理中确保回滚

### 向量库与关系库同步
- 文档摄取时同时写入向量库和关系库
- 删除文档时同时清理两个库
- 使用事务确保一致性（如果向量库支持）

## 测试建议

1. **单元测试**: 测试CRUD函数的正确性
2. **集成测试**: 测试数据库连接和会话管理
3. **迁移测试**: 测试Alembic迁移脚本
4. **性能测试**: 测试大量数据下的查询性能

