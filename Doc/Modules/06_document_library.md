# 文档库模块文档

## 概述
文档库模块负责管理文档的存储和组织，支持私人文档库和群组文档库两种类型。

## 当前实现（与代码对齐）
- 所有接口采用 JWT 鉴权（`Authorization: Bearer <token>`），依赖 `get_current_user`。
- 文档库模型：`DocumentLibrary(id, name, description, owner_id, owner_type[user|group], vector_collection_name, metadata, created_at)`。
- 文档模型：`Document` 持有 `library_id`（非空），并在摄取时与库关联。
- 向量库：每个库一个 Chroma collection，命名 `library_<library_id>`，默认库为 `library_default`。
- 群组库：已引入 `Group`、`GroupMember(role: owner|admin|member)`，当 `owner_type=group` 时校验成员角色：
  - 创建库：需要 group owner/admin
  - 列表/详情/摄取：允许 owner/admin/member
  - 更新/删除：需要 owner/admin

### 已提供的 API 路由（`/api/v1/docs`）
- `POST /libraries`：创建库。默认归当前用户，`owner_type` 缺省为 `user`。若显式传 `owner_id` 且为 user，需等于当前用户。
- `GET /libraries`：列出库。默认列出当前用户的库；若传 `owner_id` 且 `owner_type=user`，要求与当前用户一致。
- `GET /libraries/{library_id}`：查看库详情，校验所属。
- `PUT /libraries/{library_id}`：更新库名称/描述，校验所属。
- `DELETE /libraries/{library_id}`：删除库并尝试删除对应向量集合（best-effort）。
- `POST /ingest`：上传并摄取文件到库；如传 `library_id`，需有库权限；否则存入默认库。
- `POST /reindex`：占位接口，返回 queued。

### 权限与隔离
- `owner_type=user` 时，仅库所有者可管理/摄取。
- `owner_type=group` 未来扩展；当前代码未校验群组成员关系，需要实现后再开放。
- 向量数据按库隔离：创建/摄取/删除库时对应的 Chroma collection 分别创建/写入/删除（删除为 best-effort）。

### 核心架构原则

1. **两层结构**:
   - **私人库**: User → Library → Document
   - **群组库**: Group → Library → Document
   - 只有两层结构，Library直接包含Document

2. **数据完全隔离**:
   - 不同Library之间的数据完全隔离
   - 不同Group的Library数据不共享
   - 不同User的私人Library数据不共享
   - 向量索引按Library隔离存储

3. **Agent记忆隔离**:
   - 每个Library有独立的Agent记忆上下文
   - 不同Library之间的Agent记忆不共享
   - 会话历史按Library隔离

## 模块结构

```
app/library/
├── models.py          # 文档库数据模型
├── service.py         # 文档库服务（CRUD、权限检查）
├── storage.py         # 文档存储管理（对象存储、元数据）
└── permissions.py     # 文档库权限检查
```

## 1. 数据模型 (`models.py`)

### DocumentLibrary（文档库表）

**表名**: `document_libraries`

**字段**:
- `id` (UUID, Primary Key): 文档库唯一标识
- `name` (String(255)): 文档库名称
- `type` (Enum): 文档库类型（`private` | `group`）
- `owner_id` (UUID, Foreign Key): 
  - 如果`type=private`: 指向User表的用户ID
  - 如果`type=group`: 指向Group表的群组ID
- `description` (Text, Optional): 描述信息
- `metadata` (JSON): 扩展元数据（标签、分类等）
- `vector_collection_name` (String(255)): 向量库集合名称（用于隔离）
- `created_at` (DateTime): 创建时间
- `updated_at` (DateTime): 更新时间

**关系**:
- `documents`: 一对多关系，关联到Document表（Library直接包含Document）
- `owner_user`: 多对一关系，关联到User表（当type=private时）
- `owner_group`: 多对一关系，关联到Group表（当type=group时）

**索引**:
- `(owner_id, type)`: 复合索引，用于快速查询用户的文档库
- `vector_collection_name`: 唯一索引，确保向量库集合名称唯一

**重要说明**:
- Library是数据隔离的基本单位
- 每个Library有独立的向量索引集合（通过`vector_collection_name`标识）
- 不同Library之间的Document完全隔离

### Document（文档表，扩展）

**表名**: `documents`

**新增字段**:
- `library_id` (UUID, Foreign Key): 所属文档库ID（必填）
- `owner_id` (UUID, Foreign Key): 文档所有者ID
- `visibility` (Enum): 可见性（`private` | `library` | `public`）
- `access_count` (Integer): 访问次数
- `last_accessed_at` (DateTime, Optional): 最后访问时间

**关系**:
- `library`: 多对一关系，关联到DocumentLibrary表
- `owner`: 多对一关系，关联到User表

### 数据模型关系说明

**两层结构**:
```
Group/User
  └── Library (DocumentLibrary)
      └── Document
          └── Chunk
```

**不需要GroupLibrary关联表**:
- 群组直接拥有Library（通过DocumentLibrary.owner_id指向Group）
- 用户直接拥有Library（通过DocumentLibrary.owner_id指向User）
- Library直接包含Document（通过Document.library_id指向Library）

### 数据模型定义示例

```python
from enum import Enum
from sqlalchemy import Enum as SQLEnum, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

class LibraryType(str, Enum):
    PRIVATE = "private"
    GROUP = "group"

class VisibilityLevel(str, Enum):
    PRIVATE = "private"      # 仅所有者可见
    LIBRARY = "library"      # 文档库成员可见
    PUBLIC = "public"         # 所有人可见（未来扩展）

class PermissionLevel(str, Enum):
    READ = "read"
    WRITE = "write"
    MANAGE = "manage"

class DocumentLibrary(Base):
    __tablename__ = "document_libraries"
    
    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[LibraryType] = mapped_column(SQLEnum(LibraryType), nullable=False)
    # owner_id根据type指向不同表：
    # - type=PRIVATE: 指向users.id
    # - type=GROUP: 指向groups.id
    # 注意：SQLAlchemy不支持多态外键，需要在应用层处理
    owner_id: Mapped[uuid.UUID] = mapped_column(UUIDType, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    vector_collection_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)  # 向量库集合名称，用于隔离
    metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow)
    
    # 关系
    documents: Mapped[list["Document"]] = relationship(back_populates="library")
    # owner关系需要在应用层根据type动态处理
    
    # 索引
    __table_args__ = (
        Index("idx_library_owner_type", "owner_id", "type"),
    )

class Document(Base):
    __tablename__ = "documents"
    
    # 原有字段...
    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255))
    source_path: Mapped[str] = mapped_column(String(512))
    
    # 新增字段
    library_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("document_libraries.id"), nullable=False)
    owner_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("users.id"), nullable=False)
    visibility: Mapped[VisibilityLevel] = mapped_column(SQLEnum(VisibilityLevel), default=VisibilityLevel.LIBRARY)
    access_count: Mapped[int] = mapped_column(default=0)
    last_accessed_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    
    metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
    
    # 关系
    library: Mapped["DocumentLibrary"] = relationship(back_populates="documents")
    owner: Mapped["User"] = relationship()
    chunks: Mapped[list["Chunk"]] = relationship(back_populates="document")
```

## 2. 文档库服务 (`service.py`)

### DocumentLibraryService类

**职责**: 提供文档库的CRUD操作和权限检查

### 方法列表

#### 1. `async def create_private_library(user_id: uuid.UUID, name: str, description: str | None = None) -> DocumentLibrary`
**描述**: 创建私人文档库

**参数**:
- `user_id`: 用户ID
- `name`: 文档库名称
- `description`: 描述（可选）

**返回**: DocumentLibrary实例

**实现**:
```python
async def create_private_library(
    self,
    session: AsyncSession,
    user_id: uuid.UUID,
    name: str,
    description: str | None = None
) -> DocumentLibrary:
    library = DocumentLibrary(
        name=name,
        type=LibraryType.PRIVATE,
        owner_id=user_id,
        description=description
    )
    session.add(library)
    await session.commit()
    await session.refresh(library)
    return library
```

#### 2. `async def create_group_library(group_id: uuid.UUID, name: str, description: str | None = None) -> DocumentLibrary`
**描述**: 创建群组文档库

**参数**:
- `group_id`: 群组ID
- `name`: 文档库名称
- `description`: 描述（可选）

**返回**: DocumentLibrary实例

#### 3. `async def get_user_libraries(user_id: uuid.UUID, include_groups: bool = True) -> list[DocumentLibrary]`
**描述**: 获取用户可访问的所有文档库

**参数**:
- `user_id`: 用户ID
- `include_groups`: 是否包含群组文档库

**返回**: DocumentLibrary列表

**实现逻辑**:
1. 查询用户的私人文档库（`type=PRIVATE AND owner_id=user_id`）
2. 查询用户所在群组的文档库：
   - 查询用户加入的群组（GroupMember表）
   - 查询这些群组拥有的文档库（`type=GROUP AND owner_id IN (用户所在群组ID列表)`）
3. 合并返回（不需要去重，因为私人库和群组库的owner_id指向不同表）

**重要**: 两层结构，群组直接拥有Library，不需要中间关联表

#### 4. `async def get_accessible_library_ids(user_id: uuid.UUID, library_ids: list[uuid.UUID] | None = None) -> list[uuid.UUID]`
**描述**: 获取用户可访问的文档库ID列表（用于检索过滤）

**参数**:
- `user_id`: 用户ID
- `library_ids`: 指定的文档库ID列表（如果为None，返回所有可访问的）

**返回**: 文档库ID列表

**实现**:
```python
async def get_accessible_library_ids(
    self,
    session: AsyncSession,
    user_id: uuid.UUID,
    library_ids: list[uuid.UUID] | None = None
) -> list[uuid.UUID]:
    # 1. 查询用户可访问的所有文档库
    accessible_libs = await self.get_user_libraries(session, user_id)
    accessible_ids = [lib.id for lib in accessible_libs]
    
    # 2. 如果指定了library_ids，进行过滤和权限验证
    if library_ids:
        # 只返回用户有权限访问的文档库ID
        accessible_ids = [lib_id for lib_id in library_ids if lib_id in accessible_ids]
    
    return accessible_ids
```

#### 5. `async def check_permission(user_id: uuid.UUID, library_id: uuid.UUID, permission: str) -> bool`
**描述**: 检查用户对文档库的权限

**参数**:
- `user_id`: 用户ID
- `library_id`: 文档库ID
- `permission`: 权限类型（`read` | `write` | `manage`）

**返回**: 是否有权限

**权限规则**:
- **私人库** (`type=PRIVATE`):
  - 只有所有者（`owner_id=user_id`）有所有权限
  - 其他用户无权限

- **群组库** (`type=GROUP`):
  - 检查用户是否是群组成员（`GroupMember`表中存在记录）
  - `read`: 群组成员都可以
  - `write`: 群组成员且角色为maintenance及以上
  - `manage`: 群组管理员（`GroupMember.role=admin`）或manager角色用户

#### 6. `async def add_document_to_library(document_id: uuid.UUID, library_id: uuid.UUID, session: AsyncSession) -> Document`
**描述**: 将文档添加到文档库

**参数**:
- `document_id`: 文档ID
- `library_id`: 文档库ID
- `session`: 数据库会话

**返回**: Document实例

**实现**:
```python
async def add_document_to_library(
    self,
    document_id: uuid.UUID,
    library_id: uuid.UUID,
    session: AsyncSession
) -> Document:
    document = await session.get(Document, document_id)
    if document:
        document.library_id = library_id
        await session.commit()
        await session.refresh(document)
    return document
```

## 3. 文档存储管理 (`storage.py`)

### DocumentStorageService类

**职责**: 管理文档的物理存储和元数据

### 方法列表

#### 1. `async def store_file(file: UploadFile, library_id: uuid.UUID, owner_id: uuid.UUID) -> Document`
**描述**: 存储上传的文件

**参数**:
- `file`: 上传的文件对象
- `library_id`: 文档库ID
- `owner_id`: 所有者ID

**返回**: Document实例

**实现流程**:
1. 保存文件到对象存储（本地文件系统或S3等）
2. 创建Document记录
3. 关联到文档库
4. 返回Document实例

#### 2. `async def get_file_path(document_id: uuid.UUID) -> Path`
**描述**: 获取文档的存储路径

**参数**:
- `document_id`: 文档ID

**返回**: 文件路径

#### 3. `async def delete_file(document_id: uuid.UUID) -> bool`
**描述**: 删除文档文件

**参数**:
- `document_id`: 文档ID

**返回**: 是否成功

**实现**:
- 删除物理文件
- 删除数据库记录
- 删除向量库中的嵌入（需要调用Ingestion服务）

## 4. 权限检查 (`permissions.py`)

### LibraryPermissionChecker类

**职责**: 提供文档库权限检查的便捷方法

### 方法列表

#### 1. `async def can_read(user_id: uuid.UUID, library_id: uuid.UUID) -> bool`
**描述**: 检查用户是否可以读取文档库

#### 2. `async def can_write(user_id: uuid.UUID, library_id: uuid.UUID) -> bool`
**描述**: 检查用户是否可以写入文档库

#### 3. `async def can_manage(user_id: uuid.UUID, library_id: uuid.UUID) -> bool`
**描述**: 检查用户是否可以管理文档库

### 权限检查实现示例

```python
class LibraryPermissionChecker:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.library_service = DocumentLibraryService()
    
    async def can_read(self, user_id: uuid.UUID, library_id: uuid.UUID) -> bool:
        library = await self.session.get(DocumentLibrary, library_id)
        if not library:
            return False
        
        # 私人库：只有所有者可以读取
        if library.type == LibraryType.PRIVATE:
            return library.owner_id == user_id
        
        # 群组库：检查用户是否是群组成员
        if library.type == LibraryType.GROUP:
            return await self._is_group_member(user_id, library.owner_id)
        
        return False
    
    async def can_write(self, user_id: uuid.UUID, library_id: uuid.UUID) -> bool:
        if not await self.can_read(user_id, library_id):
            return False
        
        library = await self.session.get(DocumentLibrary, library_id)
        if library.type == LibraryType.PRIVATE:
            return library.owner_id == user_id
        
        # 群组库：需要maintenance角色及以上
        if library.type == LibraryType.GROUP:
            user = await self.session.get(User, user_id)
            return user.role in ["maintenance", "manager", "admin"]
        
        return False
```

## 文档库使用流程

### 1. 创建私人文档库

```python
# API端点
@router.post("/libraries/private")
async def create_private_library(
    name: str,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    library_service = DocumentLibraryService()
    library = await library_service.create_private_library(
        session=session,
        user_id=current_user.id,
        name=name
    )
    return {"library_id": str(library.id), "name": library.name}
```

### 2. 上传文档到文档库

```python
# API端点
@router.post("/docs/upload")
async def upload_document(
    file: UploadFile,
    library_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    # 1. 检查权限
    checker = LibraryPermissionChecker(session)
    if not await checker.can_write(current_user.id, library_id):
        raise HTTPException(403, "No permission to write to this library")
    
    # 2. 存储文件
    storage_service = DocumentStorageService()
    document = await storage_service.store_file(file, library_id, current_user.id)
    
    # 3. 触发文档摄取（异步任务）
    await trigger_ingestion(document.id)
    
    return {"document_id": str(document.id), "library_id": str(library_id)}
```

### 3. 查询文档库中的文档

```python
# API端点
@router.get("/libraries/{library_id}/documents")
async def list_library_documents(
    library_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    # 1. 检查权限
    checker = LibraryPermissionChecker(session)
    if not await checker.can_read(current_user.id, library_id):
        raise HTTPException(403, "No permission to read this library")
    
    # 2. 查询文档
    library_service = DocumentLibraryService()
    documents = await library_service.get_library_documents(session, library_id)
    
    return [{"id": str(d.id), "title": d.title} for d in documents]
```

## 与RAG模块集成

### 检索时过滤文档库

```python
# 在Retriever中
class HybridRetriever:
    async def search(
        self,
        query: str,
        library_ids: list[uuid.UUID],  # 文档库ID列表
        top_k: int = 5
    ) -> list[RetrievedChunk]:
        # 1. 从向量库检索（按library_id过滤）
        vector_results = await self._vector_search(
            query=query,
            library_ids=library_ids,  # 传递给向量库查询
            top_k=top_k * 2
        )
        
        # 2. 从BM25索引检索（按library_id过滤）
        bm25_results = await self._bm25_search(
            query=query,
            library_ids=library_ids,
            top_k=top_k * 2
        )
        
        # 3. 结果融合
        fused = self._rrf_fusion(vector_results, bm25_results)
        
        return fused[:top_k]
```

### 向量库存储时按Library隔离

```python
# 在Ingestion中
class DocumentIngestor:
    async def ingest_file(self, path: Path, library_id: uuid.UUID, session: AsyncSession):
        # 1. 获取Library信息（包含vector_collection_name）
        library = await session.get(DocumentLibrary, library_id)
        
        # 2. 文档解析和分块
        # ... 文档解析和分块 ...
        
        # 3. 存储到向量库（使用Library的独立集合）
        for chunk in chunks:
            # 使用Library的vector_collection_name作为集合名称
            await self.vector_store.add(
                collection_name=library.vector_collection_name,  # 重要：使用Library的集合名称
                id=str(chunk.id),
                embedding=chunk.embedding,
                metadata={
                    "document_id": str(document.id),
                    "library_id": str(library_id),  # 重要：包含文档库ID
                    "chunk_index": chunk.index
                }
            )
```

### 数据隔离实现

**向量库隔离**:
- 每个Library有独立的向量集合（通过`vector_collection_name`）
- 检索时只查询指定Library的向量集合
- 不同Library的向量数据完全隔离

**关系库隔离**:
- Document表通过`library_id`字段关联到Library
- 查询时通过`library_id`过滤，确保数据隔离
- 不同Library的Document不会混合

**Agent记忆隔离**:
- 每个Library有独立的会话上下文
- Agent的记忆（对话历史）按Library隔离存储
- 不同Library之间的Agent记忆不共享

## 数据隔离和Agent记忆隔离

### 数据隔离规则

1. **Library级别的完全隔离**:
   - 不同Library之间的Document完全隔离
   - 不同Group的Library数据不共享
   - 不同User的私人Library数据不共享
   - 向量索引按Library隔离（每个Library有独立的向量集合）

2. **检索隔离**:
   - 检索时只能访问指定Library的文档
   - 不能跨Library检索（除非用户有多个Library的访问权限）
   - 向量检索时使用Library的`vector_collection_name`作为集合名称

3. **存储隔离**:
   - Document表通过`library_id`字段关联
   - 向量库使用不同的集合名称隔离
   - 元数据存储也按Library隔离

### Agent记忆隔离

1. **会话上下文隔离**:
   - 每个Library有独立的Agent会话上下文
   - 会话历史按Library存储（`session_id`包含`library_id`）
   - 不同Library之间的对话历史不共享

2. **记忆存储结构**:
```python
# Agent记忆存储示例
class AgentMemory:
    def __init__(self, library_id: uuid.UUID):
        self.library_id = library_id
        self.session_key = f"agent_memory:{library_id}"  # 包含library_id
    
    async def get_conversation_history(self, user_id: uuid.UUID):
        # 查询时包含library_id过滤
        return await db.query(
            ConversationHistory
            .where(
                ConversationHistory.library_id == self.library_id,
                ConversationHistory.user_id == user_id
            )
        )
```

3. **上下文传递**:
   - Agent处理查询时，只使用当前Library的上下文
   - 不能访问其他Library的对话历史
   - 多轮对话时，上下文限制在当前Library范围内

## 性能优化建议

1. **索引优化**:
   - 在 `(library_id, document_id)` 上创建复合索引
   - 在向量库中按Library使用独立集合（已通过`vector_collection_name`实现）

2. **缓存策略**:
   - 缓存用户可访问的文档库列表
   - 缓存文档库权限检查结果
   - 缓存按Library隔离（缓存key包含library_id）

3. **批量操作**:
   - 支持批量上传文档（限制在同一Library内）
   - 不支持跨Library移动文档（数据隔离要求）

4. **异步处理**:
   - 文档摄取使用异步任务队列
   - 文档删除时异步清理向量库（按Library的集合清理）

