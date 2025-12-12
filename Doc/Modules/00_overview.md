# 项目模块总览

## 架构图参考
本项目参考了以下架构图（位于 `Doc/diagram/graph/`）：
- `graph.001.jpeg` - 系统整体架构图
- `graph.002.jpeg` - 数据流架构图
- `graph.003.jpeg` - 组件交互图

## 核心模块划分

系统分为以下核心模块，各模块职责清晰，通过定义良好的接口进行通信：

```
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway Layer                        │
│              (app/api/v1/ - HTTP接口层)                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              Authentication & Authorization                  │
│         (app/core/security.py - 认证授权层)                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  Document    │ │    Agent     │ │    User      │
│  Library     │ │  Orchestrator│ │  Management  │
│  Module      │ │   Module     │ │   Module     │
│              │ │              │ │              │
│ app/library/ │ │ app/agents/  │ │ app/users/   │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                 │                │
       │                 ▼                │
       │         ┌──────────────┐         │
       │         │   RAG        │         │
       │         │  Pipeline    │         │
       │         │  Module      │         │
       │         │              │         │
       │         │ app/rag/     │         │
       │         └──────┬───────┘         │
       │                │                 │
       └────────────────┼─────────────────┘
                        │
        ┌───────────────┼───────────────┐
        │               │               │
        ▼               ▼               ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  Vector DB   │ │  Relational  │ │   Storage    │
│  (Chroma/    │ │     DB       │ │   (Object    │
│   Qdrant)    │ │ (PostgreSQL/ │ │   Storage)   │
│              │ │   SQLite)    │ │              │
└──────────────┘ └──────────────┘ └──────────────┘
```

## 模块详细说明

### 1. API Gateway Layer (`app/api/v1/`)
**职责**: HTTP接口层，处理客户端请求和响应
- `qa.py`: 问答接口
- `docs.py`: 文档管理接口（上传、索引）
- `admin.py`: 管理接口（健康检查、监控）
- `users.py`: 用户管理接口（注册、登录、权限）
- `groups.py`: 群组管理接口（创建、成员管理）

### 2. Document Library Module (`app/library/`)
**职责**: 文档库管理，支持私人库和群组库

**两层结构**:
- **私人库**: User → Library → Document
- **群组库**: Group → Library → Document

**核心特性**:
- 数据完全隔离：不同Library之间的数据不共享
- Agent记忆隔离：每个Library有独立的会话上下文
- 向量索引隔离：每个Library有独立的向量集合

**模块文件**:
- `models.py`: 文档库数据模型（DocumentLibrary）
- `service.py`: 文档库服务（创建、查询、权限检查）
- `storage.py`: 文档存储管理（对象存储、元数据）

### 3. Agent Orchestrator Module (`app/agents/`)
**职责**: Agent编排，协调工具调用和RAG流程
- `qa_agent.py`: QA Agent核心逻辑
- `tools.py`: 工具注册表
- `context_manager.py`: 上下文管理（用户角色、权限、文档库范围）

### 4. RAG Pipeline Module (`app/rag/`)
**职责**: 检索增强生成流水线
- `pipeline.py`: RAG流水线主控制器
- `retriever.py`: 混合检索器（支持多文档库检索）
- `prompts.py`: 提示模板管理（角色相关）
- `ingestion.py`: 文档摄取处理
- `evaluators.py`: 响应评估

### 5. User Management Module (`app/users/`)
**职责**: 用户、群组、权限管理
- `models.py`: 用户、群组、权限数据模型
- `auth.py`: 认证服务（JWT、API Key）
- `permissions.py`: 权限检查服务（RBAC）
- `roles.py`: 角色定义和管理
- `crud.py`: 用户相关CRUD操作

### 6. Database Layer (`app/db/`)
**职责**: 数据库抽象层
- `models.py`: SQLAlchemy数据模型
- `crud.py`: CRUD操作封装
- `session.py`: 数据库会话管理
- `base.py`: SQLAlchemy基类

### 7. Core Layer (`app/core/`)
**职责**: 基础设施功能
- `config.py`: 配置管理
- `security.py`: 安全中间件
- `logging.py`: 日志配置

## 模块间通信协议

### 1. API → Agent 通信

**请求流程**:
```python
# API层接收请求
@router.post("/ask")
async def ask(payload: AskRequest, current_user: User = Depends(get_current_user)):
    # 1. 获取用户上下文（角色、权限、可访问的文档库）
    context = await get_user_context(current_user.id)
    
    # 2. 创建Agent实例（注入用户上下文）
    agent = QAAgent(
        pipeline=pipeline,
        user_context=context
    )
    
    # 3. 执行查询
    result = await agent.run(
        query=payload.query,
        library_ids=payload.library_ids,  # 指定搜索的文档库
        top_k=payload.top_k
    )
    
    return result
```

**数据传递**:
- `UserContext`: 用户ID、角色、权限列表、可访问的文档库ID列表
- `AskRequest`: 查询字符串、文档库ID列表（可选）、top_k等参数

### 2. Agent → RAG Pipeline 通信

**请求流程**:
```python
# Agent调用RAG Pipeline
class QAAgent:
    async def run(self, query: str, library_ids: list[uuid.UUID], top_k: int):
        # 1. 根据用户角色选择prompt模板
        role = self.user_context.role
        
        # 2. 调用RAG Pipeline（传递文档库范围）
        result = await self.pipeline.run(
            query=query,
            library_ids=library_ids,  # 限制检索范围
            top_k=top_k,
            role=role,  # 用于选择prompt
            user_permissions=self.user_context.permissions  # 用于权限过滤
        )
        
        return result
```

**数据传递**:
- `QueryRequest`: 查询字符串、文档库ID列表、top_k、角色、权限
- `PipelineResult`: 答案、引用列表、延迟

### 3. RAG Pipeline → Retriever 通信

**请求流程**:
```python
# RAG Pipeline调用Retriever
class RAGPipeline:
    async def run(self, query: str, library_ids: list[uuid.UUID], ...):
        # 1. 调用Retriever（传递文档库范围）
        chunks = await self.retriever.search(
            query=query,
            library_ids=library_ids,  # 限制检索范围
            top_k=top_k
        )
        
        # 2. 根据权限过滤结果
        filtered_chunks = self._filter_by_permissions(chunks, user_permissions)
        
        # 3. 构建上下文和提示
        context = self._build_context(filtered_chunks)
        prompt = get_prompt(role=role).format(context=context, question=query)
        
        # 4. 调用LLM生成答案
        answer = await self._generate_answer(prompt)
        
        return PipelineResult(answer=answer, references=filtered_chunks, ...)
```

**数据传递**:
- `SearchRequest`: 查询字符串、文档库ID列表、top_k
- `RetrievedChunk[]`: 检索到的文档块列表（包含文档库ID）

### 4. Retriever → Document Library 通信

**请求流程**:
```python
# Retriever查询文档库
class HybridRetriever:
    async def search(self, query: str, library_ids: list[uuid.UUID], top_k: int):
        # 1. 获取文档库服务实例
        library_service = get_library_service()
        
        # 2. 验证文档库访问权限（已在Agent层验证，这里做二次确认）
        accessible_libs = await library_service.get_accessible_libraries(
            user_id=self.user_id,
            library_ids=library_ids
        )
        
        # 3. 从向量库检索（按文档库过滤）
        vector_results = await self._vector_search(query, accessible_libs, top_k)
        
        # 4. BM25检索（按文档库过滤）
        bm25_results = await self._bm25_search(query, accessible_libs, top_k)
        
        # 5. 结果融合
        fused_results = self._rrf_fusion(vector_results, bm25_results)
        
        return fused_results[:top_k]
```

**数据传递**:
- `LibraryQuery`: 文档库ID列表、查询字符串
- `DocumentChunk[]`: 文档块（包含library_id字段）

### 5. Document Library → Database 通信

**请求流程**:
```python
# 文档库服务查询数据库
class DocumentLibraryService:
    async def get_accessible_libraries(
        self, 
        user_id: uuid.UUID, 
        library_ids: list[uuid.UUID] | None = None
    ) -> list[uuid.UUID]:
        # 1. 查询用户可访问的所有文档库
        #    - 私人文档库（owner_id = user_id）
        #    - 群组文档库（用户是群组成员）
        accessible = await db.query(
            select(DocumentLibrary)
            .where(
                or_(
                    DocumentLibrary.owner_id == user_id,  # 私人库
                    DocumentLibrary.id.in_(
                        select(GroupLibrary.library_id)
                        .join(GroupMember)
                        .where(GroupMember.user_id == user_id)
                    )  # 群组库
                )
            )
        )
        
        # 2. 如果指定了library_ids，进行过滤
        if library_ids:
            accessible = [lib for lib in accessible if lib.id in library_ids]
        
        return [lib.id for lib in accessible]
```

## 数据流示例

### 完整问答流程

```
1. 用户请求
   POST /api/v1/ask
   {
     "query": "如何维护设备？",
     "library_ids": ["lib-123", "lib-456"]  // 可选，不指定则搜索所有可访问库
   }
   ↓
2. API层
   - 验证用户身份（JWT/API Key）
   - 获取用户上下文（角色、权限、可访问文档库）
   ↓
3. Agent层
   - 根据用户角色选择prompt模板
   - 调用RAG Pipeline（传递文档库范围）
   ↓
4. RAG Pipeline
   - 调用Retriever（传递文档库ID列表）
   - 构建上下文
   - 根据角色选择prompt
   - 调用LLM生成答案
   ↓
5. Retriever
   - 验证文档库访问权限
   - 从向量库检索（按文档库过滤）
   - 从BM25索引检索（按文档库过滤）
   - 结果融合和重排序
   ↓
6. Document Library Service
   - 查询数据库获取用户可访问的文档库
   - 返回文档库ID列表
   ↓
7. 返回结果
   {
     "answer": "根据文档...",
     "references": [
       {"document_id": "...", "library_id": "lib-123", "score": 0.9},
       ...
     ]
   }
```

### 文档上传流程

```
1. 用户上传文档
   POST /api/v1/docs/upload
   {
     "file": <file>,
     "library_id": "lib-123",  // 指定文档库
     "is_private": true  // 是否私人库
   }
   ↓
2. API层
   - 验证用户身份
   - 验证文档库权限（用户是否有权限上传到该库）
   ↓
3. Document Library Service
   - 创建文档记录
   - 分配文档库
   ↓
4. Ingestion Service
   - 文档解析和分块
   - 向量化
   - 存储到向量库（包含library_id元数据）
   - 存储元数据到关系库
   ↓
5. 返回结果
   {
     "document_id": "...",
     "library_id": "lib-123",
     "chunks": 10
   }
```

## 权限模型

### 角色定义

| 角色 | 描述 | Prompt风格 | 权限 |
|------|------|-----------|------|
| `operator` | 运维技术人员 | 技术细节、操作步骤 | 读取私人库、读取所在群组库 |
| `maintenance` | 维护工程师 | 维护流程、故障排查 | 读取私人库、读取所在群组库、写入群组库 |
| `manager` | 工厂管理者 | 决策支持、数据分析 | 读取所有群组库、管理群组 |
| `admin` | 系统管理员 | 系统管理视角 | 所有权限 |

### 权限类型

- `library:read`: 读取文档库
- `library:write`: 写入文档库
- `library:delete`: 删除文档库
- `library:manage`: 管理文档库（添加成员等）
- `group:create`: 创建群组
- `group:manage`: 管理群组成员

### 文档库访问规则

1. **私人文档库** (`type=PRIVATE`):
   - 只有所有者（`owner_id=user_id`）可以访问
   - 所有者拥有所有权限
   - 数据完全隔离，其他用户无法访问

2. **群组文档库** (`type=GROUP`):
   - 群组成员可以读取（用户是群组成员）
   - 特定角色可以写入（maintenance及以上）
   - 群组管理员可以管理
   - 不同群组的Library数据完全隔离

3. **数据隔离**:
   - 不同Library之间的数据完全隔离
   - 不同Group的Library数据不共享
   - 不同User的私人Library数据不共享
   - 向量索引按Library隔离（每个Library有独立的向量集合）

4. **Agent记忆隔离**:
   - 每个Library有独立的Agent会话上下文
   - 不同Library之间的Agent记忆不共享
   - 对话历史按Library隔离存储

5. **默认行为**:
   - 如果查询时不指定library_ids，搜索所有用户有权限访问的文档库
   - Agent根据用户角色自动过滤结果
   - 检索时只查询指定Library的向量集合

## 技术栈

- **Web框架**: FastAPI
- **ORM**: SQLAlchemy (异步)
- **向量数据库**: Chroma (默认), 支持 Qdrant/Milvus/pgvector
- **检索**: 混合检索（向量 + BM25）
- **LLM集成**: OpenAI (默认), 可扩展其他提供商
- **认证**: JWT + API Key
- **权限**: RBAC (基于角色的访问控制)
- **配置管理**: Pydantic Settings
- **日志**: Python logging

## 扩展点

1. **文档库类型**: 可扩展支持更多文档库类型（项目库、部门库等）
2. **权限系统**: 可扩展支持更细粒度的权限控制（文档级别权限）
3. **检索策略**: 可扩展支持文档库级别的检索策略配置
4. **角色系统**: 可扩展支持自定义角色和权限组合

## 环境与配置（更新）
- 使用 `.env` 注入敏感值，代码中默认均为空字符串（API keys、数据库、Redis、JWT 等）。
- 关键变量：`DATABASE_URL`(MySQL)、`REDIS_URL`、`JWT_SECRET`、`STORAGE_DIR`、`VECTOR_DB_URI`、DashScope/OpenAI 分钥 (`DASHSCOPE_EMBEDDING_API_KEY` / `DASHSCOPE_LLM_API_KEY` / `OPENAI_API_KEY`)。
- DashScope 兼容 OpenAI API，需设置对应 `*_BASE_URL`。
- 示例参见 `env.example` 与 `Doc/Modules/05_core_layer.md`。

## 测试（更新）
- API 集成与 E2E：`tests/test_api_endpoints.py`（含 agent_rag_flow：建库、上传、显式向量化、检索/Agent 问答）。
- RAG/配置单测：`tests/test_rag_unit.py`（LLM/embedding 选择逻辑等）。
- 运行示例：`PYTHONPATH=./ uv run pytest -q tests/test_api_endpoints.py -k agent_rag_flow`；或 `uv run pytest -q tests/test_rag_unit.py`。

