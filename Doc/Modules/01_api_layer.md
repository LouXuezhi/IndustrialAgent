# API层模块文档

## 概述
API 层基于 FastAPI，所有受保护接口使用 Bearer JWT（jti + Redis 黑名单吊销），CORS 已配置。

## 模块结构
```
app/api/v1/
├── auth.py       # 登录/刷新/注销
├── qa.py         # 问答接口（RAG/Agent）
├── docs.py       # 文档与库管理
└── admin.py      # 健康检查
```

## 0. 认证相关
- `POST /api/v1/auth/register`（如启用）：注册
- `POST /api/v1/auth/login`：获取 access token（含 jti）
- `POST /api/v1/auth/refresh`：刷新 token
- `POST /api/v1/auth/logout`：注销当前 token（jti 写入 Redis 黑名单）
- 认证头：`Authorization: Bearer <access_token>`

## 1. 问答接口 (`qa.py`)

### 端点
`POST /api/v1/qa/ask`

- 认证：Bearer JWT
- 请求体 `AskRequest`（直接 JSON，或按 FastAPI 推断为 `{ "payload": {...} }` 包裹）：
```json
{
  "query": "设备怎么维护？",
  "library_ids": ["<library_uuid>"],
  "top_k": 5
}
```
- 响应 `StandardResponse[AskData]`：包含 `answer`、`references`（含 library_id）、`latency_ms`。
- 流程：校验 JWT → 注入 RAGPipeline → QAAgent 运行 → 返回答案与引用。

## 2. 文档与库接口 (`docs.py`)

### 库管理
- `POST /api/v1/docs/libraries`：创建库（私库/群库，需有群组成员权限）。
- `GET /api/v1/docs/libraries`：列出可访问的库。
- `DELETE /api/v1/docs/libraries/{library_id}`：删除库，级联删库下文档与向量。
- 认证：Bearer JWT；群库操作校验成员/角色。

### 文档上传与向量化（分步）
- `POST /api/v1/docs/ingest`：上传文件，仅落盘+入库，`vectorized=False`。
  - Form: `file`，可选 `library_id`。
  - 响应：`document_id`，`chunks=0`，`vectorized=false`。
- `POST /api/v1/docs/documents/{document_id}/vectorize`：显式触发分块+向量化。
  - JSON（通常需包一层 `payload`）：`{"chunk_size": 800}`
  - 成功返回 `vectorized=true` 与块数；失败 `code=1` 且 `vectorized=false`。
- `GET /api/v1/docs/documents`：列出文档，含 `vectorized` 状态。

### 检索与下载
- `POST /api/v1/docs/documents/search`：按关键字/库搜索文档（需 JWT）。
- `GET /api/v1/docs/documents/{id}/preview`：返回文本预览。
- `GET /api/v1/docs/documents/{id}/download`：下载原文件。
- `POST /api/v1/docs/documents/batch-download`：批量打包 zip 下载。

### 权限与策略
- 私库：仅 owner；群库：成员可见，按角色（owner/admin/member）控制增删改。
- 删除库会级联清理库内文档及向量集合。

## 3. 管理接口 (`admin.py`)
- `GET /api/v1/admin/healthz`：健康检查。
- `GET /api/v1/admin/ping`：连通性测试。

## 安全机制
- Bearer JWT（`Authorization`），jti 写入 Redis 黑名单支持注销/吊销。
- 依赖 `get_current_user` 完成解码、过期校验、黑名单校验。
- CORS 在 `app/main.py` 配置，域名通过配置注入。

## 典型交互流程
1) 登录获取 token → 2) 创建/选择库 → 3) 上传文件 `/docs/ingest`（vectorized=false）→ 4) 显式 `/documents/{id}/vectorize` → 5) QA `/qa/ask` 指定库检索。

## 错误与返回
- 401：缺失/失效/被吊销的 JWT。
- 422：请求体验证失败（注意部分路由需 `{ "payload": {...} }` 包裹）。
- 500：内部错误；向量化失败会返回 `code=1` 且 `vectorized=false`。
