# 数据隔离和Agent记忆隔离文档

## 概述
本文档详细说明系统的数据隔离机制和Agent记忆隔离规则，确保不同Library之间的数据完全隔离，Agent记忆不共享。

## 架构原则

### 两层结构

系统采用两层结构，Library直接包含Document：

```
私人库结构:
User
  └── Library (DocumentLibrary, type=PRIVATE)
      └── Document
          └── Chunk

群组库结构:
Group
  └── Library (DocumentLibrary, type=GROUP)
      └── Document
          └── Chunk
```

**重要**: 
- 只有两层结构，没有中间层
- Library直接包含Document（通过Document.library_id）
- 不需要GroupLibrary关联表

## 数据隔离机制

### 1. Library级别的完全隔离

**原则**: 不同Library之间的数据完全隔离，不能跨Library访问。

#### 关系数据库隔离

```python
# Document表通过library_id字段关联
class Document(Base):
    library_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, 
        ForeignKey("document_libraries.id"),
        nullable=False
    )
    
    # 查询时通过library_id过滤
    @classmethod
    async def get_by_library(cls, session: AsyncSession, library_id: uuid.UUID):
        return await session.execute(
            select(cls).where(cls.library_id == library_id)
        )
```

**隔离规则**:
- Document必须属于一个Library（`library_id`必填）
- 查询Document时必须指定`library_id`
- 不能跨Library查询Document
- 不同Library的Document不会出现在同一查询结果中

#### 向量数据库隔离

```python
# 每个Library有独立的向量集合
class DocumentLibrary(Base):
    vector_collection_name: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
    )  # 例如: "library_abc123_collection"

# 存储时使用Library的集合名称
async def store_chunk(library: DocumentLibrary, chunk: Chunk):
    await vector_store.add(
        collection_name=library.vector_collection_name,  # 使用Library的集合
        id=str(chunk.id),
        embedding=chunk.embedding,
        metadata={"library_id": str(library.id)}
    )

# 检索时只查询指定Library的集合
async def search(library_id: uuid.UUID, query: str):
    library = await get_library(library_id)
    results = await vector_store.query(
        collection_name=library.vector_collection_name,  # 只查询这个Library的集合
        query_vector=embed_query(query),
        top_k=10
    )
    return results
```

**隔离规则**:
- 每个Library有唯一的`vector_collection_name`
- 向量存储时使用Library的集合名称
- 向量检索时只查询指定Library的集合
- 不同Library的向量数据存储在不同的集合中

### 2. 群组和私人库隔离

#### 私人库隔离

```python
# 私人库只有所有者可以访问
class DocumentLibrary:
    type: LibraryType = LibraryType.PRIVATE
    owner_id: uuid.UUID  # 指向User.id

# 查询私人库
async def get_private_libraries(user_id: uuid.UUID):
    return await session.execute(
        select(DocumentLibrary)
        .where(
            DocumentLibrary.type == LibraryType.PRIVATE,
            DocumentLibrary.owner_id == user_id
        )
    )
```

**隔离规则**:
- 私人库的`owner_id`指向User表
- 只有所有者可以访问
- 不同用户的私人库完全隔离

#### 群组库隔离

```python
# 群组库只有群组成员可以访问
class DocumentLibrary:
    type: LibraryType = LibraryType.GROUP
    owner_id: uuid.UUID  # 指向Group.id

# 查询群组库（用户是群组成员）
async def get_group_libraries(user_id: uuid.UUID):
    # 1. 查询用户加入的群组
    user_groups = await session.execute(
        select(GroupMember.group_id)
        .where(GroupMember.user_id == user_id)
    )
    group_ids = [g[0] for g in user_groups]
    
    # 2. 查询这些群组的Library
    return await session.execute(
        select(DocumentLibrary)
        .where(
            DocumentLibrary.type == LibraryType.GROUP,
            DocumentLibrary.owner_id.in_(group_ids)
        )
    )
```

**隔离规则**:
- 群组库的`owner_id`指向Group表
- 只有群组成员可以访问
- 不同群组的Library完全隔离
- 用户只能访问自己加入的群组的Library

### 3. 检索隔离

#### 向量检索隔离

```python
class HybridRetriever:
    async def search(
        self,
        query: str,
        library_ids: list[uuid.UUID],  # 必须指定Library ID列表
        top_k: int = 5
    ) -> list[RetrievedChunk]:
        results = []
        
        # 为每个Library分别检索
        for library_id in library_ids:
            library = await get_library(library_id)
            
            # 只查询这个Library的向量集合
            library_results = await self._vector_search(
                collection_name=library.vector_collection_name,  # 使用Library的集合
                query=query,
                top_k=top_k
            )
            
            results.extend(library_results)
        
        # 合并结果并重排序
        return self._rerank(results)[:top_k]
```

**隔离规则**:
- 检索时必须指定`library_ids`列表
- 每个Library的向量集合独立检索
- 结果按Library分组，不会混淆
- 不能跨Library检索（除非用户有多个Library的访问权限）

#### BM25检索隔离

```python
class HybridRetriever:
    async def _bm25_search(
        self,
        query: str,
        library_ids: list[uuid.UUID],
        top_k: int
    ):
        results = []
        
        for library_id in library_ids:
            # 获取Library的BM25索引（每个Library有独立索引）
            bm25_index = await self._get_bm25_index(library_id)
            
            # 只在这个Library的索引中检索
            library_results = bm25_index.get_top_n(query, top_k)
            results.extend(library_results)
        
        return results
```

**隔离规则**:
- 每个Library有独立的BM25索引
- 检索时只查询指定Library的索引
- 不同Library的索引完全隔离

## Agent记忆隔离机制

### 1. 会话上下文隔离

**原则**: 每个Library有独立的Agent会话上下文，不同Library之间的记忆不共享。

#### 会话ID结构

```python
# 会话ID包含library_id，确保隔离
def generate_session_id(user_id: uuid.UUID, library_id: uuid.UUID) -> str:
    return f"{user_id}:{library_id}"  # 例如: "user123:lib456"
```

**隔离规则**:
- 会话ID必须包含`library_id`
- 不同Library的会话ID不同
- 查询会话历史时必须指定`library_id`

#### 记忆存储结构

```python
class ConversationHistory(Base):
    __tablename__ = "conversation_histories"
    
    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("users.id"))
    library_id: Mapped[uuid.UUID] = mapped_column(UUIDType, ForeignKey("document_libraries.id"))  # 重要：包含library_id
    session_id: Mapped[str] = mapped_column(String(255))  # 格式: "{user_id}:{library_id}"
    query: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(Text)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, default=dt.datetime.utcnow)
    
    # 索引
    __table_args__ = (
        Index("idx_conversation_library_user", "library_id", "user_id"),
        Index("idx_conversation_session", "session_id"),
    )
```

**隔离规则**:
- 对话历史表包含`library_id`字段
- 查询时必须同时指定`user_id`和`library_id`
- 不同Library的对话历史不会混合

### 2. Agent记忆管理

#### 获取对话历史

```python
class AgentMemory:
    def __init__(self, library_id: uuid.UUID):
        self.library_id = library_id
    
    async def get_conversation_history(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        limit: int = 10
    ) -> list[ConversationHistory]:
        # 只查询当前Library的对话历史
        result = await session.execute(
            select(ConversationHistory)
            .where(
                ConversationHistory.library_id == self.library_id,  # 重要：按Library过滤
                ConversationHistory.user_id == user_id
            )
            .order_by(ConversationHistory.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
```

**隔离规则**:
- 只获取当前Library的对话历史
- 不能访问其他Library的对话历史
- 查询时强制包含`library_id`条件

#### 保存对话历史

```python
class AgentMemory:
    async def save_conversation(
        self,
        session: AsyncSession,
        user_id: uuid.UUID,
        query: str,
        answer: str
    ):
        session_id = f"{user_id}:{self.library_id}"  # 包含library_id
        
        history = ConversationHistory(
            user_id=user_id,
            library_id=self.library_id,  # 重要：保存library_id
            session_id=session_id,
            query=query,
            answer=answer
        )
        
        session.add(history)
        await session.commit()
```

**隔离规则**:
- 保存时必须包含`library_id`
- 不同Library的对话历史分别存储
- 不会混淆不同Library的对话

### 3. Agent处理流程

#### 单Library查询

```python
class QAAgent:
    async def run(
        self,
        query: str,
        library_id: uuid.UUID,  # 必须指定Library ID
        top_k: int = 5
    ):
        # 1. 获取当前Library的对话历史
        memory = AgentMemory(library_id=library_id)
        history = await memory.get_conversation_history(
            user_id=self.user_context.user_id,
            library_id=library_id  # 只获取当前Library的历史
        )
        
        # 2. 调用RAG Pipeline（只搜索当前Library）
        result = await self.pipeline.run(
            query=query,
            library_ids=[library_id],  # 只搜索当前Library
            conversation_history=history  # 当前Library的历史
        )
        
        # 3. 保存对话历史（按Library隔离）
        await memory.save_conversation(
            user_id=self.user_context.user_id,
            query=query,
            answer=result.answer
        )
        
        return result
```

#### 多Library查询

```python
class QAAgent:
    async def run_multiple_libraries(
        self,
        query: str,
        library_ids: list[uuid.UUID],  # 多个Library
        top_k: int = 5
    ):
        all_results = []
        
        # 为每个Library分别处理（记忆隔离）
        for library_id in library_ids:
            # 获取这个Library的对话历史
            memory = AgentMemory(library_id=library_id)
            history = await memory.get_conversation_history(
                user_id=self.user_context.user_id,
                library_id=library_id  # 只获取这个Library的历史
            )
            
            # 只搜索这个Library
            result = await self.pipeline.run(
                query=query,
                library_ids=[library_id],  # 只搜索这个Library
                conversation_history=history  # 这个Library的历史
            )
            
            # 保存这个Library的对话历史
            await memory.save_conversation(
                user_id=self.user_context.user_id,
                query=query,
                answer=result.answer
            )
            
            all_results.append(result)
        
        # 合并结果（但记忆仍然隔离）
        return self._merge_results(all_results)
```

**隔离规则**:
- 多Library查询时，每个Library的记忆独立处理
- 检索结果可以合并，但记忆仍然隔离
- 每个Library的对话历史分别保存

## 实现检查清单

### 数据隔离检查

- [ ] Document表包含`library_id`字段（必填）
- [ ] 查询Document时强制包含`library_id`条件
- [ ] DocumentLibrary表包含`vector_collection_name`字段（唯一）
- [ ] 向量存储时使用Library的`vector_collection_name`
- [ ] 向量检索时只查询指定Library的集合
- [ ] BM25索引按Library隔离

### Agent记忆隔离检查

- [ ] ConversationHistory表包含`library_id`字段
- [ ] 会话ID格式为`"{user_id}:{library_id}"`
- [ ] 获取对话历史时强制包含`library_id`条件
- [ ] 保存对话历史时包含`library_id`
- [ ] Agent处理时只使用当前Library的对话历史
- [ ] 多Library查询时，每个Library的记忆独立处理

## 测试建议

1. **数据隔离测试**:
   - 测试不同Library的Document不会出现在同一查询结果中
   - 测试向量检索时只返回指定Library的文档
   - 测试用户只能访问自己有权限的Library

2. **Agent记忆隔离测试**:
   - 测试不同Library的对话历史不会混合
   - 测试多Library查询时，每个Library的记忆独立
   - 测试会话ID包含library_id

3. **权限隔离测试**:
   - 测试用户不能访问其他用户的私人Library
   - 测试用户不能访问未加入群组的Library
   - 测试跨Library访问被拒绝

