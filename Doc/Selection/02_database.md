# 数据库选型：SQLAlchemy + 关系数据库

> 创建时间: 2025-12-07  
> 决策状态: ✅ 已确定

## 选型结果

**ORM框架**: SQLAlchemy (异步)  
**主数据库**: MySQL (生产) / SQLite (开发)  
**缓存数据库**: Redis  
**迁移工具**: Alembic  
**版本**: SQLAlchemy >= 2.0.30

## 技术特性

### SQLAlchemy特性

- **成熟稳定**: 20+年历史，大量生产案例
- **异步支持**: SQLAlchemy 2.0原生异步支持
- **灵活性**: 支持Core API、ORM、Raw SQL多种查询方式
- **类型安全**: 完整的Python类型系统支持
- **数据库无关**: 支持MySQL、SQLite等多种数据库后端

### 异步使用示例

```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# MySQL连接
engine = create_async_engine("mysql+aiomysql://user:pass@localhost/dbname?charset=utf8mb4")
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with async_session() as session:
        yield session
```

### 模型定义示例

```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(unique=True)
    email: Mapped[str | None] = mapped_column(default=None)
```

## 数据库选择

### 主数据库：MySQL (生产) / SQLite (开发)

#### MySQL (生产环境)

##### 优势
- ✅ **性能优异**: 支持高并发和大数据量
- ✅ **成熟稳定**: 久经考验，大量生产案例
- ✅ **ACID保证**: 完整的事务支持
- ✅ **扩展性**: 支持主从复制、读写分离、分库分表
- ✅ **生态完善**: 丰富的工具和运维经验
- ✅ **成本低**: 开源免费，运维成本低

##### 配置
```python
# .env (生产)
DATABASE_URL=mysql+aiomysql://user:pass@localhost/dbname?charset=utf8mb4
```

##### 连接配置
```python
engine = create_async_engine(
    "mysql+aiomysql://user:pass@localhost/dbname?charset=utf8mb4",
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600
)
```

#### SQLite (开发环境)

##### 优势
- ✅ **零配置**: 无需安装数据库服务
- ✅ **快速开发**: 文件数据库，即开即用
- ✅ **轻量级**: 适合开发和测试

##### 配置
```python
# .env (开发)
DATABASE_URL=sqlite+aiosqlite:///./industrial_qa.db
```

### 缓存数据库：Redis

#### 优势
- ✅ **高性能**: 内存存储，读写速度极快
- ✅ **丰富数据结构**: String、Hash、List、Set、Sorted Set
- ✅ **持久化**: 支持RDB和AOF持久化
- ✅ **高可用**: 支持主从复制、哨兵、集群
- ✅ **广泛应用**: 缓存、会话存储、消息队列等

#### 使用场景

1. **查询结果缓存**
   ```python
   # 缓存问答结果
   cache_key = f"qa:{query_hash}"
   cached_result = await redis.get(cache_key)
   if cached_result:
       return json.loads(cached_result)
   ```

2. **会话存储**
   ```python
   # 存储用户会话
   session_key = f"session:{user_id}"
   await redis.setex(session_key, 3600, session_data)
   ```

3. **频率限制**
   ```python
   # API限流
   rate_limit_key = f"rate_limit:{user_id}:{endpoint}"
   count = await redis.incr(rate_limit_key)
   if count == 1:
       await redis.expire(rate_limit_key, 60)
   ```

4. **热点数据缓存**
   ```python
   # 缓存热门文档库信息
   library_cache_key = f"library:{library_id}"
   await redis.setex(library_cache_key, 3600, library_info)
   ```

#### 配置
```python
# .env
REDIS_URL=redis://localhost:6379/0
REDIS_PASSWORD=  # 可选
REDIS_MAX_CONNECTIONS=50
```

#### Redis客户端实现
```python
# app/core/cache.py
import redis.asyncio as redis
from typing import Optional
import json

class RedisCache:
    def __init__(self, redis_url: str):
        self.client = redis.from_url(redis_url, decode_responses=True)
    
    async def get(self, key: str) -> Optional[dict]:
        """获取缓存"""
        value = await self.client.get(key)
        if value:
            return json.loads(value)
        return None
    
    async def set(self, key: str, value: dict, expire: int = 3600):
        """设置缓存"""
        await self.client.setex(
            key,
            expire,
            json.dumps(value, ensure_ascii=False)
        )
    
    async def delete(self, key: str):
        """删除缓存"""
        await self.client.delete(key)
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        return await self.client.exists(key) > 0
```

## 项目中的实现

### 1. 数据库会话管理

```python
# app/db/session.py
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

def create_async_engine_from_url(url: str):
    """创建异步数据库引擎"""
    # MySQL特定配置
    if url.startswith("mysql"):
        return create_async_engine(
            url,
            echo=False,  # 生产环境设为False
            future=True,
            pool_pre_ping=True,  # 连接健康检查
            pool_size=10,
            max_overflow=20,
            pool_recycle=3600,  # 连接回收时间
            pool_reset_on_return='commit'  # MySQL特定配置
        )
    else:
        # SQLite或其他数据库
        return create_async_engine(
            url,
            echo=False,
            future=True,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20
        )

def create_session_maker(engine):
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
```

### 2. 模型定义

```python
# app/db/models.py
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
import uuid

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(unique=True, index=True)
    email: Mapped[str] = mapped_column(unique=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    
    # 关系
    libraries: Mapped[list["DocumentLibrary"]] = relationship(back_populates="owner")
```

### 3. CRUD操作

```python
# app/db/crud.py
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

async def create_user(session: AsyncSession, username: str, email: str) -> User:
    user = User(username=username, email=email)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user

async def get_user_by_id(session: AsyncSession, user_id: uuid.UUID) -> User | None:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()
```

### 4. 依赖注入

```python
# app/deps.py
from app.db.session import async_session_maker

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

## 数据库迁移（Alembic）

### 初始化

```bash
alembic init alembic
```

### 创建迁移

```bash
alembic revision --autogenerate -m "create users table"
```

### 执行迁移

```bash
# 升级
alembic upgrade head

# 降级
alembic downgrade -1
```

### 迁移文件示例

```python
# alembic/versions/xxx_create_users.py
def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

def downgrade():
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_table('users')
```

## 性能优化

### 1. 连接池配置

```python
engine = create_async_engine(
    database_url,
    pool_size=10,        # 连接池大小
    max_overflow=20,     # 最大溢出连接
    pool_pre_ping=True,  # 连接健康检查
    pool_recycle=3600    # 连接回收时间（秒）
)
```

### 2. 查询优化

```python
# 使用selectinload避免N+1查询
from sqlalchemy.orm import selectinload

result = await session.execute(
    select(User)
    .options(selectinload(User.libraries))
    .where(User.id == user_id)
)
user = result.scalar_one()
# 访问user.libraries不会触发额外查询
```

### 3. 批量操作

```python
# 批量插入
users = [User(username=f"user{i}") for i in range(100)]
session.add_all(users)
await session.commit()
```

## 最佳实践

1. **使用异步**: 所有数据库操作使用async/await
2. **事务管理**: 合理使用事务，避免长事务
3. **索引优化**: 为常用查询字段添加索引
4. **连接池**: 合理配置连接池大小
5. **迁移管理**: 使用Alembic管理数据库迁移
6. **错误处理**: 正确处理数据库异常

## 缓存策略

### 缓存层级

1. **L1缓存（应用层）**: 内存缓存（LRU Cache）
2. **L2缓存（Redis）**: 分布式缓存
3. **L3缓存（数据库）**: 持久化存储

### 缓存更新策略

1. **Cache-Aside**: 应用层管理缓存
2. **Write-Through**: 写入时同时更新缓存
3. **TTL过期**: 设置合理的过期时间

### 缓存失效策略

```python
# 示例：文档更新时清除相关缓存
async def invalidate_cache_on_doc_update(library_id: str, doc_id: str):
    # 清除文档缓存
    await redis.delete(f"doc:{doc_id}")
    # 清除文档库缓存
    await redis.delete(f"library:{library_id}")
    # 清除相关查询缓存
    await redis.delete(f"query:*:{library_id}")
```

## 总结

SQLAlchemy + MySQL + Redis是工业问答系统的最佳选择：
- ✅ **MySQL**: 成熟稳定，性能优异，适合生产环境
- ✅ **Redis**: 高性能缓存，提升系统响应速度
- ✅ **异步支持**: SQLAlchemy原生异步，性能优异
- ✅ **灵活强大**: 支持复杂查询和多种数据库
- ✅ **类型安全**: 良好的类型系统支持
- ✅ **生态完善**: 丰富的工具和社区支持

## 参考资源

- [SQLAlchemy文档](https://docs.sqlalchemy.org/)
- [Alembic文档](https://alembic.sqlalchemy.org/)
- [PostgreSQL文档](https://www.postgresql.org/docs/)

