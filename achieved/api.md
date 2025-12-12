# 已实现的 API 接口文档 (v1)

## 概述

所有 API 端点位于 `/api/v1` 前缀下。受保护的接口需要 Bearer JWT 认证（`Authorization: Bearer <token>`）。

**注意**：参数名为 `payload` 的路由，请求体需要包裹在 `{"payload": {...}}` 中。

---

## 1. 认证接口 (`/api/v1/auth`)

### 1.1 注册
- **端点**: `POST /api/v1/register`
- **认证**: 不需要
- **请求体**:
  ```json
  {
    "email": "user@example.com",
    "password": "pwd123",
    "username": "optional",
    "full_name": "optional"
  }
  ```
- **响应**:
  ```json
  {
    "code": 0,
    "data": {
      "user_id": "<uuid>",
      "is_verified": true
    },
    "message": "success"
  }
  ```
- **说明**: 
  - 邮箱必须唯一
  - 密码长度 >= 6
  - 注册时自动创建个人默认库（名为"<full_name|username|email前缀>的个人库"）

### 1.2 登录
- **端点**: `POST /api/v1/login`
- **认证**: 不需要
- **请求体**:
  ```json
  {
    "payload": {
      "email": "user@example.com",
      "password": "pwd123"
    }
  }
  ```
- **响应**:
  ```json
  {
    "code": 0,
    "data": {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "token_type": "bearer",
      "expires_in": 3600,
      "user_id": "<uuid>",
      "is_verified": true
    },
    "message": "success"
  }
  ```
- **说明**: Token 包含 `jti`，用于注销时的黑名单管理

### 1.3 刷新 Token
- **端点**: `POST /api/v1/refresh`
- **认证**: Bearer JWT
- **请求体**: 空
- **响应**: 同登录响应结构

### 1.4 注销
- **端点**: `POST /api/v1/logout`
- **认证**: Bearer JWT
- **请求体**: 空
- **响应**:
  ```json
  {
    "code": 0,
    "data": {
      "message": "logged out"
    },
    "message": "success"
  }
  ```
- **说明**: 将当前 token 的 `jti` 写入 Redis 黑名单，直到 token 过期

### 1.5 邮箱验证（已禁用）
- **端点**: `POST /api/v1/verify-email`
- **端点**: `POST /api/v1/resend-verification`
- **状态**: 返回 503 Service Unavailable

---

## 2. 问答接口 (`/api/v1/qa`)

### 2.1 问答查询
- **端点**: `POST /api/v1/qa/ask`
- **认证**: Bearer JWT
- **请求体**:
  ```json
  {
    "payload": {
      "query": "根据文档库内容,日常巡检是什么样的",
      "library_ids": ["c87deba0-204c-4fec-a149-c757ac143d9d"],
      "top_k": 5
    }
  }
  ```
- **参数说明**:
  - `query`: 用户问题（最少 3 个字符）
  - `library_ids`: 文档库ID列表（可选，不指定则搜索所有可访问的文档库）
  - `top_k`: 返回的检索结果数量（1-20，默认 5）
- **响应**:
  ```json
  {
    "code": 0,
    "data": {
      "answer": "根据文档内容，日常巡检包括以下步骤...",
      "references": [
        {
          "document_id": "<uuid>",
          "score": 0.85,
          "metadata": {
            "document_id": "<uuid>",
            "library_id": "<uuid>",
            "offset": 0,
            "length": 800
          }
        }
      ],
      "latency_ms": 1234
    },
    "message": "success"
  }
  ```
- **说明**: 
  - 使用 RAG（检索增强生成）技术
  - 仅检索已向量化的文档（`vectorized=true`）
  - 按库隔离检索

---

## 3. 文档库管理 (`/api/v1/docs/libraries`)

### 3.1 创建文档库
- **端点**: `POST /api/v1/docs/libraries`
- **认证**: Bearer JWT
- **请求体**:
  ```json
  {
    "payload": {
      "name": "我的文档库",
      "description": "可选描述",
      "owner_type": "user",
      "owner_id": null
    }
  }
  ```
- **参数说明**:
  - `name`: 库名称（必填，最少 1 个字符）
  - `description`: 描述（可选）
  - `owner_type`: 所有者类型，`"user"` 或 `"group"`（默认 `"user"`）
  - `owner_id`: 所有者ID（可选，默认当前用户）
- **响应**:
  ```json
  {
    "code": 0,
    "data": {
      "id": "<library-uuid>",
      "name": "我的文档库",
      "owner_id": "<user-uuid>",
      "owner_type": "user",
      "description": "可选描述",
      "vector_collection_name": "library_<library-uuid>"
    },
    "message": "success"
  }
  ```
- **权限**: 
  - 个人库：只能为自己创建
  - 群组库：需要是群组的 owner 或 admin

### 3.2 列出文档库
- **端点**: `GET /api/v1/docs/libraries`
- **认证**: Bearer JWT
- **查询参数**:
  - `owner_id`: 可选，指定所有者ID
  - `owner_type`: 可选，`"user"` 或 `"group"`（默认 `"user"`）
- **响应**:
  ```json
  {
    "code": 0,
    "data": [
      {
        "id": "<library-uuid>",
        "name": "我的文档库",
        "owner_id": "<user-uuid>",
        "owner_type": "user",
        "description": "...",
        "vector_collection_name": "library_<library-uuid>"
      }
    ],
    "message": "success"
  }
  ```
- **说明**: 返回用户有权限访问的所有文档库

### 3.3 获取文档库详情
- **端点**: `GET /api/v1/docs/libraries/{library_id}`
- **认证**: Bearer JWT
- **响应**: 同创建文档库的响应结构

### 3.4 更新文档库
- **端点**: `PUT /api/v1/docs/libraries/{library_id}`
- **认证**: Bearer JWT
- **请求体**:
  ```json
  {
    "payload": {
      "name": "新名称",
      "description": "新描述"
    }
  }
  ```
- **权限**: 
  - 个人库：仅 owner
  - 群组库：owner 或 admin

### 3.5 删除文档库
- **端点**: `DELETE /api/v1/docs/libraries/{library_id}`
- **认证**: Bearer JWT
- **响应**:
  ```json
  {
    "code": 0,
    "data": {},
    "message": "success"
  }
  ```
- **说明**: 
  - 级联删除库内所有文档和向量数据
  - 权限要求：个人库仅 owner，群组库需 owner 或 admin

### 3.6 获取文档库统计
- **端点**: `GET /api/v1/docs/libraries/{library_id}/stats`
- **认证**: Bearer JWT
- **响应**:
  ```json
  {
    "code": 0,
    "data": {
      "library_id": "<uuid>",
      "document_count": 10,
      "total_chunks": 150,
      "total_size_bytes": 1048576
    },
    "message": "success"
  }
  ```

### 3.7 列出库内文档
- **端点**: `GET /api/v1/docs/libraries/{library_id}/documents`
- **认证**: Bearer JWT
- **查询参数**:
  - `limit`: 每页数量（1-200，默认 50）
  - `offset`: 偏移量（默认 0）
- **响应**: 文档列表（见文档管理部分）

---

## 4. 文档管理 (`/api/v1/docs/documents`)

### 4.1 上传文档
- **端点**: `POST /api/v1/docs/ingest`
- **认证**: Bearer JWT
- **请求**: `multipart/form-data`
  - `file`: 文件（必填，支持 PDF/DOCX/TXT/MD）
  - `library_id`: 文档库ID（可选，UUID 字符串）
- **响应**:
  ```json
  {
    "code": 0,
    "data": {
      "document_id": "<uuid>",
      "chunks": 0,
      "library_id": "<library-uuid>",
      "vectorized": false
    },
    "message": "success"
  }
  ```
- **说明**: 
  - 文件保存到 `data/uploads/` 目录
  - 仅创建文档记录，**不进行向量化**
  - 若未提供 `library_id`，自动使用用户的个人默认库

### 4.2 向量化文档
- **端点**: `POST /api/v1/docs/documents/{document_id}/vectorize`
- **认证**: Bearer JWT
- **请求体**:
  ```json
  {
    "payload": {
      "chunk_size": 800
    }
  }
  ```
- **参数说明**:
  - `chunk_size`: 分块大小（100-4000，默认 800）
- **成功响应**:
  ```json
  {
    "code": 0,
    "data": {
      "document_id": "<uuid>",
      "chunks": 15,
      "vectorized": true
    },
    "message": "success"
  }
  ```
- **失败响应**:
  ```json
  {
    "code": 1,
    "data": {
      "document_id": "<uuid>",
      "chunks": 0,
      "vectorized": false
    },
    "message": "Vectorization failed: <error message>"
  }
  ```
- **说明**: 
  - 提取文本 → 分块 → 生成向量 → 写入 ChromaDB
  - 向量化后文档才可用于检索和问答

### 4.3 列出所有文档
- **端点**: `GET /api/v1/docs/documents`
- **认证**: Bearer JWT
- **查询参数**:
  - `library_id`: 可选，过滤指定库的文档
  - `limit`: 每页数量（1-200，默认 50）
  - `offset`: 偏移量（默认 0）
- **响应**:
  ```json
  {
    "code": 0,
    "data": [
      {
        "id": "<uuid>",
        "title": "文档标题.pdf",
        "source_path": "data/uploads/...",
        "library_id": "<library-uuid>",
        "meta": {
          "file_type": ".pdf",
          "file_size": 1024000,
          "vectorized": true
        },
        "vectorized": true,
        "created_at": "2024-01-01T00:00:00"
      }
    ],
    "message": "success"
  }
  ```
- **说明**: 返回用户有权限访问的所有文档

### 4.4 获取文档详情
- **端点**: `GET /api/v1/docs/documents/{document_id}`
- **认证**: Bearer JWT
- **响应**: 同文档列表中的单个文档结构

### 4.5 删除文档
- **端点**: `DELETE /api/v1/docs/documents/{document_id}`
- **认证**: Bearer JWT
- **响应**:
  ```json
  {
    "code": 0,
    "data": {},
    "message": "success"
  }
  ```
- **说明**: 级联删除文档的所有分块和向量数据

### 4.6 批量删除文档
- **端点**: `POST /api/v1/docs/documents/batch-delete`
- **认证**: Bearer JWT
- **请求体**:
  ```json
  {
    "payload": {
      "document_ids": ["<uuid1>", "<uuid2>", ...]
    }
  }
  ```
- **参数限制**: 1-100 个文档ID
- **响应**:
  ```json
  {
    "code": 0,
    "data": {
      "deleted": 5,
      "document_ids": ["<uuid1>", "<uuid2>", ...]
    },
    "message": "success"
  }
  ```

### 4.7 搜索文档
- **端点**: `POST /api/v1/docs/documents/search`
- **认证**: Bearer JWT
- **请求体**:
  ```json
  {
    "payload": {
      "query": "巡检",
      "library_id": "<library-uuid>",
      "limit": 20
    }
  }
  ```
- **参数说明**:
  - `query`: 搜索关键词（必填，最少 1 个字符）
  - `library_id`: 可选，限制搜索范围
  - `limit`: 返回数量（1-100，默认 20）
- **响应**:
  ```json
  {
    "code": 0,
    "data": [
      {
        "document_id": "<uuid>",
        "title": "文档标题",
        "snippet": "...包含关键词的文本片段...",
        "score": 2.0,
        "library_id": "<library-uuid>"
      }
    ],
    "message": "success"
  }
  ```
- **说明**: 在文档标题和内容中搜索关键词

### 4.8 预览文档
- **端点**: `GET /api/v1/docs/documents/{document_id}/preview`
- **认证**: Bearer JWT
- **响应**:
  ```json
  {
    "code": 0,
    "data": {
      "document_id": "<uuid>",
      "title": "文档标题",
      "content": "文档文本内容...",
      "content_length": 5000,
      "file_type": ".pdf",
      "vectorized": true
    },
    "message": "success"
  }
  ```

### 4.9 下载单个文档
- **端点**: `GET /api/v1/docs/documents/{document_id}/download`
- **认证**: Bearer JWT
- **响应**: 文件流
- **Headers**: 
  - `Content-Disposition: attachment; filename="文档标题.pdf"`

### 4.10 批量下载文档
- **端点**: `POST /api/v1/docs/documents/batch-download`
- **认证**: Bearer JWT
- **请求体**:
  ```json
  {
    "payload": {
      "document_ids": ["<uuid1>", "<uuid2>", ...]
    }
  }
  ```
- **参数限制**: 1-50 个文档ID
- **响应**: ZIP 文件流
- **Headers**: 
  - `Content-Type: application/zip`
  - `Content-Disposition: attachment; filename=documents.zip`

### 4.11 重建索引（占位）
- **端点**: `POST /api/v1/docs/reindex`
- **认证**: Bearer JWT
- **响应**:
  ```json
  {
    "code": 0,
    "data": {
      "status": "queued"
    },
    "message": "success"
  }
  ```
- **说明**: 当前为占位实现，实际应集成任务队列系统

---

## 5. 管理接口 (`/api/v1/admin`)

### 5.1 健康检查
- **端点**: `GET /api/v1/admin/healthz`
- **认证**: 不需要
- **响应**:
  ```json
  {
    "status": "healthy",
    "timestamp": "1735689600.123"
  }
  ```
- **用途**: 
  - Kubernetes/Docker 健康检查
  - 负载均衡器健康探测
  - 监控系统状态检查

### 5.2 连通性测试
- **端点**: `GET /api/v1/admin/ping`
- **认证**: 不需要
- **响应**:
  ```json
  {
    "message": "pong"
  }
  ```
- **用途**: 快速测试服务是否可达

---

## 认证说明

### Bearer JWT 认证

所有受保护的接口需要在请求头中包含：

```
Authorization: Bearer <access_token>
```

其中 `<access_token>` 是通过 `/api/v1/login` 或 `/api/v1/refresh` 获取的 JWT token。

### Token 结构

JWT token 包含以下声明：
- `sub`: 用户ID
- `jti`: Token 唯一标识（用于注销）
- `exp`: 过期时间
- `email`: 用户邮箱（额外声明）
- `role`: 用户角色（额外声明）

### 注销机制

调用 `/api/v1/logout` 后，token 的 `jti` 会被写入 Redis 黑名单，直到 token 自然过期。后续使用该 token 的请求会被拒绝。

---

## 请求体格式说明

### 需要 `payload` 包裹的路由

以下路由的参数名为 `payload`，请求体需要包裹：

```json
{
  "payload": {
    // 实际参数
  }
}
```

**需要包裹的路由**：
- `POST /api/v1/login`
- `POST /api/v1/qa/ask`
- `POST /api/v1/docs/libraries`
- `PUT /api/v1/docs/libraries/{library_id}`
- `POST /api/v1/docs/documents/{document_id}/vectorize`
- `POST /api/v1/docs/documents/search`
- `POST /api/v1/docs/documents/batch-delete`
- `POST /api/v1/docs/documents/batch-download`

### 不需要包裹的路由

以下路由直接使用请求体：

- `POST /api/v1/register` - 直接 JSON
- `POST /api/v1/docs/ingest` - multipart/form-data

---

## 错误响应格式

所有接口使用统一的错误响应格式：

```json
{
  "code": 1,
  "message": "错误描述",
  "data": null,
  "timestamp": 1735689600
}
```

### 常见 HTTP 状态码

- `200 OK`: 请求成功
- `400 Bad Request`: 请求参数错误
- `401 Unauthorized`: 未认证或 token 无效/已注销
- `403 Forbidden`: 无权限访问
- `404 Not Found`: 资源不存在
- `422 Unprocessable Entity`: 请求体验证失败
- `500 Internal Server Error`: 服务器内部错误
- `503 Service Unavailable`: 服务不可用（如邮箱验证已禁用）

---

## 典型使用流程

### 1. 注册和登录
```bash
# 1. 注册
POST /api/v1/register
{"email": "user@example.com", "password": "pwd123"}

# 2. 登录获取 token
POST /api/v1/login
{"payload": {"email": "user@example.com", "password": "pwd123"}}
```

### 2. 创建库并上传文档
```bash
# 1. 创建文档库
POST /api/v1/docs/libraries
{"payload": {"name": "我的库", "owner_type": "user"}}

# 2. 上传文档
POST /api/v1/docs/ingest
multipart/form-data: file=@document.pdf, library_id=<library-uuid>

# 3. 向量化文档
POST /api/v1/docs/documents/{document_id}/vectorize
{"payload": {"chunk_size": 800}}
```

### 3. 问答查询
```bash
POST /api/v1/qa/ask
{
  "payload": {
    "query": "设备维护流程是什么？",
    "library_ids": ["<library-uuid>"],
    "top_k": 5
  }
}
```

---

## 注意事项

1. **文档向量化**: 上传文档后必须显式调用向量化接口，文档才能被检索
2. **库隔离**: 每个文档库有独立的向量集合，检索时按库隔离
3. **权限控制**: 
   - 个人库：仅 owner 可访问
   - 群组库：成员可访问，owner/admin 可管理
4. **默认库**: 注册时自动创建个人默认库，上传文档时若不指定库，自动使用默认库
5. **向量化状态**: 文档的 `vectorized` 字段反映是否已成功向量化
6. **批量操作**: 批量删除和批量下载的路由在参数化路由之前，避免路由冲突
