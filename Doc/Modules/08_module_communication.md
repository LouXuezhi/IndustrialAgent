# 模块间通信协议文档

## 概述
本文档详细定义各模块之间的通信接口、数据传递格式和调用流程，确保模块间解耦和可维护性。

## 通信架构图

```
┌─────────────┐
│   API Layer │
└──────┬──────┘
       │ HTTP Request/Response
       ▼
┌─────────────────────────────────────┐
│  Authentication & Authorization      │
│  (JWT/API Key验证)                   │
└──────┬───────────────────────────────┘
       │ UserContext
       ▼
┌─────────────────────────────────────┐
│         Agent Layer                  │
│  (QAAgent + Context Manager)        │
└──────┬───────────────────────────────┘
       │ QueryRequest (包含library_ids, role)
       ▼
┌─────────────────────────────────────┐
│         RAG Pipeline                 │
│  (Pipeline + Retriever)             │
└──────┬───────────────────────────────┘
       │ SearchRequest (library_ids)
       ▼
┌─────────────────────────────────────┐
│    Document Library Service          │
│  (权限验证 + 文档库查询)              │
└──────┬───────────────────────────────┘
       │ Library IDs
       ▼
┌─────────────────────────────────────┐
│      Vector DB + Relational DB       │
└─────────────────────────────────────┘
```

## 1. API层 → Agent层通信

### 接口定义

**请求数据** (`AskRequest`):
```python
from pydantic import BaseModel, Field
from uuid import UUID

class AskRequest(BaseModel):
    query: str = Field(..., min_length=3, description="用户查询")
    library_ids: list[UUID] | None = Field(
        default=None,
        description="指定的文档库ID列表，不指定则搜索所有可访问的文档库"
    )
    top_k: int = Field(default=5, ge=1, le=20, description="返回结果数量")
```

**响应数据** (`AskResponse`):
```python
class AskResponse(BaseModel):
    answer: str                    # 生成的答案
    references: list[Reference]    # 引用来源列表
    latency_ms: int               # 处理延迟（毫秒）

class Reference(BaseModel):
    document_id: str               # 文档ID
    library_id: str                # 文档库ID
    score: float                   # 相关性分数
    metadata: dict                 # 元数据（来源、页码等）
```

### 调用流程

```python
# API端点实现
@router.post("/ask", response_model=AskResponse)
async def ask_entrypoint(
    payload: AskRequest,
    current_user: User = Depends(get_current_user),  # 从JWT获取用户
    pipeline: RAGPipeline = Depends(get_pipeline),
    session: AsyncSession = Depends(get_db_session)
):
    # 1. 获取用户上下文（角色、权限、可访问的文档库）
    permission_checker = PermissionChecker(session)
    user_context = await permission_checker.get_user_context(current_user.id)
    
    # 2. 创建Agent实例（注入用户上下文）
    agent = QAAgent(
        pipeline=pipeline,
        user_context=user_context
    )
    
    # 3. 执行查询
    result = await agent.run(
        query=payload.query,
        library_ids=payload.library_ids,  # 可选，None则使用所有可访问的文档库
        top_k=payload.top_k
    )
    
    # 4. 返回响应
    return AskResponse(**result)
```

### 数据传递

- **输入**: `AskRequest` + `UserContext`（从认证中间件获取）
- **输出**: `AskResponse`
- **错误处理**: 
  - 401: 未认证
  - 403: 无权限访问指定的文档库
  - 422: 请求参数验证失败

## 2. Agent层 → RAG Pipeline通信

### 接口定义

**请求数据** (`PipelineRequest`):
```python
from dataclasses import dataclass
from uuid import UUID

@dataclass
class PipelineRequest:
    query: str
    library_ids: list[UUID]          # 文档库ID列表（必填）
    top_k: int
    role: str                        # 用户角色
    user_permissions: list[str]      # 用户权限列表
```

**响应数据** (`PipelineResult`):
```python
@dataclass
class PipelineResult:
    answer: str
    references: list[RetrievedChunk]  # 包含library_id
    latency_ms: int
```

### 调用流程

```python
# Agent实现
class QAAgent:
    async def run(
        self,
        query: str,
        library_ids: list[UUID] | None = None,
        top_k: int = 5
    ) -> dict[str, Any]:
        # 1. 确定文档库范围
        if library_ids is None:
            library_ids = self.user_context.accessible_library_ids
        else:
            # 过滤：只保留用户有权限访问的文档库
            library_ids = [
                lib_id for lib_id in library_ids
                if self.user_context.can_access_library(lib_id)
            ]
        
        # 2. 调用RAG Pipeline
        result = await self.pipeline.run(
            query=query,
            library_ids=library_ids,  # 必填
            top_k=top_k,
            role=self.user_context.role,
            user_permissions=self.user_context.permissions
        )
        
        return {
            "answer": result.answer,
            "references": [
                {
                    "document_id": ref.document_id,
                    "library_id": ref.library_id,  # 重要：包含文档库ID
                    "score": ref.score,
                    "metadata": ref.metadata
                }
                for ref in result.references
            ],
            "latency_ms": result.latency_ms
        }
```

### 数据传递

- **输入**: `PipelineRequest`（包含查询、文档库范围、角色、权限）
- **输出**: `PipelineResult`
- **职责分离**:
  - Agent负责权限验证和文档库范围确定
  - Pipeline负责检索和生成

## 3. RAG Pipeline → Retriever通信

### 接口定义

**请求数据** (`SearchRequest`):
```python
@dataclass
class SearchRequest:
    query: str
    library_ids: list[UUID]          # 文档库ID列表（必填）
    top_k: int
```

**响应数据** (`RetrievedChunk[]`):
```python
@dataclass
class RetrievedChunk:
    document_id: str
    library_id: str                  # 文档库ID（必填）
    text: str
    score: float
    metadata: dict[str, Any]
```

### 调用流程

```python
# RAG Pipeline实现
class RAGPipeline:
    async def run(
        self,
        query: str,
        library_ids: list[UUID],
        top_k: int = 5,
        role: str | None = None,
        user_permissions: list[str] | None = None
    ) -> PipelineResult:
        start = time.perf_counter()
        
        # 1. 调用Retriever（传递文档库范围）
        chunks = await self.retriever.search(
            query=query,
            library_ids=library_ids,  # 限制检索范围
            top_k=top_k * 2  # 检索更多结果，后续过滤
        )
        
        # 2. 权限过滤（二次验证）
        filtered_chunks = self._filter_by_permissions(
            chunks,
            user_permissions
        )
        
        # 3. 构建上下文
        context = "\n".join(chunk.text for chunk in filtered_chunks[:top_k])
        
        # 4. 构建提示（根据角色）
        prompt = get_prompt(role=role).format(
            context=context,
            question=query
        )
        
        # 5. 调用LLM生成答案
        answer = await self._generate_answer(prompt)
        
        latency_ms = int((time.perf_counter() - start) * 1000)
        
        return PipelineResult(
            answer=answer,
            references=filtered_chunks[:top_k],
            latency_ms=latency_ms
        )
    
    def _filter_by_permissions(
        self,
        chunks: list[RetrievedChunk],
        user_permissions: list[str] | None
    ) -> list[RetrievedChunk]:
        # 根据权限过滤文档块
        # 例如：如果用户没有library:read权限，过滤掉某些文档库的文档
        if not user_permissions:
            return chunks
        
        # 这里可以添加更细粒度的权限过滤逻辑
        return chunks
```

### 数据传递

- **输入**: `SearchRequest`（查询、文档库ID列表、top_k）
- **输出**: `RetrievedChunk[]`（每个chunk包含library_id）
- **重要**: Retriever必须确保返回的chunk包含`library_id`字段

## 4. Retriever → Document Library Service通信

### 接口定义

**请求数据** (`LibraryQuery`):
```python
@dataclass
class LibraryQuery:
    user_id: UUID
    library_ids: list[UUID] | None  # None表示查询所有可访问的文档库
```

**响应数据** (`list[UUID]`):
文档库ID列表（用户有权限访问的）

### 调用流程

```python
# Retriever实现
class HybridRetriever:
    def __init__(self, vector_uri: str, embedding_model: str, user_id: UUID | None = None):
        self.vector_uri = vector_uri
        self.embedding_model = embedding_model
        self.user_id = user_id
        self.library_service = DocumentLibraryService()
    
    async def search(
        self,
        query: str,
        library_ids: list[UUID],
        top_k: int = 5
    ) -> list[RetrievedChunk]:
        # 1. 验证文档库访问权限（二次确认）
        if self.user_id:
            accessible_libs = await self.library_service.get_accessible_library_ids(
                session=self.session,
                user_id=self.user_id,
                library_ids=library_ids
            )
            library_ids = accessible_libs
        
        # 2. 从向量库检索（按library_id过滤）
        vector_results = await self._vector_search(
            query=query,
            library_ids=library_ids,  # 传递给向量库查询
            top_k=top_k * 2
        )
        
        # 3. 从BM25索引检索（按library_id过滤）
        bm25_results = await self._bm25_search(
            query=query,
            library_ids=library_ids,
            top_k=top_k * 2
        )
        
        # 4. 结果融合
        fused_results = self._rrf_fusion(vector_results, bm25_results)
        
        return fused_results[:top_k]
```

### 数据传递

- **输入**: `LibraryQuery`（用户ID、文档库ID列表）
- **输出**: `list[UUID]`（可访问的文档库ID列表）
- **用途**: 权限验证和文档库范围过滤

## 5. Document Library Service → Database通信

### 接口定义

**查询方法**:
```python
async def get_accessible_library_ids(
    session: AsyncSession,
    user_id: UUID,
    library_ids: list[UUID] | None = None
) -> list[UUID]
```

### 实现示例

```python
# Document Library Service实现
class DocumentLibraryService:
    async def get_accessible_library_ids(
        self,
        session: AsyncSession,
        user_id: UUID,
        library_ids: list[UUID] | None = None
    ) -> list[UUID]:
        # 1. 查询用户可访问的所有文档库
        #    - 私人文档库（owner_id = user_id）
        #    - 群组文档库（用户是群组成员）
        query = select(DocumentLibrary).where(
            or_(
                and_(
                    DocumentLibrary.type == LibraryType.PRIVATE,
                    DocumentLibrary.owner_id == user_id
                ),
                and_(
                    DocumentLibrary.type == LibraryType.GROUP,
                    DocumentLibrary.owner_id.in_(
                        select(Group.id)
                        .join(GroupMember)
                        .where(GroupMember.user_id == user_id)
                    )
                )
            )
        )
        
        result = await session.execute(query)
        accessible_libs = result.scalars().all()
        accessible_ids = [lib.id for lib in accessible_libs]
        
        # 2. 如果指定了library_ids，进行过滤
        if library_ids:
            accessible_ids = [
                lib_id for lib_id in library_ids
                if lib_id in accessible_ids
            ]
        
        return accessible_ids
```

## 6. 错误处理和异常传递

### 异常类型定义

```python
class ModuleCommunicationError(Exception):
    """模块通信错误基类"""
    pass

class PermissionDeniedError(ModuleCommunicationError):
    """权限拒绝错误"""
    pass

class LibraryNotFoundError(ModuleCommunicationError):
    """文档库不存在错误"""
    pass

class InvalidLibraryAccessError(ModuleCommunicationError):
    """无效的文档库访问错误"""
    pass
```

### 错误处理流程

```python
# 在Agent中
try:
    result = await self.pipeline.run(...)
except PermissionDeniedError as e:
    # 转换为HTTP 403错误
    raise HTTPException(status_code=403, detail=str(e))
except LibraryNotFoundError as e:
    # 转换为HTTP 404错误
    raise HTTPException(status_code=404, detail=str(e))
```

## 7. 数据一致性保证

### 事务管理

```python
# 在文档上传流程中
async def upload_document(...):
    async with session.begin():  # 开启事务
        # 1. 创建文档记录
        document = await create_document(...)
        
        # 2. 关联到文档库
        document.library_id = library_id
        
        # 3. 触发文档摄取（异步任务，不阻塞事务）
        await trigger_ingestion(document.id)
        
        # 事务提交
```

### 向量库与关系库同步

- 文档摄取时：同时写入向量库和关系库（使用事务保证一致性）
- 文档删除时：同时删除向量库和关系库中的记录
- 文档库删除时：级联删除所有文档和向量

## 8. 性能优化建议

1. **缓存策略**:
   - 缓存用户可访问的文档库列表（TTL: 5分钟）
   - 缓存文档库权限检查结果（TTL: 1分钟）

2. **批量操作**:
   - 支持批量查询多个文档库
   - 支持批量权限检查

3. **异步处理**:
   - 文档摄取使用异步任务队列
   - 权限检查可以异步化（如果允许）

4. **连接池**:
   - 数据库连接池配置
   - 向量库连接池配置

## 9. 测试建议

1. **单元测试**: 测试各模块的接口实现
2. **集成测试**: 测试模块间的通信流程
3. **端到端测试**: 测试完整的API → Agent → Pipeline → Retriever流程
4. **权限测试**: 测试权限验证和文档库访问控制

