# 已实现的 API 接口文档 (v1)

## 概述

所有 API 端点位于 `/api/v1` 前缀下。受保护的接口需要 Bearer JWT 认证（`Authorization: Bearer <token>`）。

**重要**：如果配置了邮箱服务（`ALIYUN_SMTP_PASSWORD`），所有需要 JWT 认证的接口都要求用户已验证邮箱。未验证用户会收到 403 错误："Email verification required. Please verify your email before using this feature."

**注意**：参数名为 `payload` 的路由，请求体需要包裹在 `{"payload": {...}}` 中。

---

## 1. 认证接口 (`/api/v1`)

### 1.1 注册
- **端点**: `POST /api/v1/register`
- **认证**: 不需要
- **请求体**:
  ```json
  {
    "email": "user@example.com",
    "password": "pwd123",
    "username": "optional",
    "full_name": "optional",
    "role": "operator"
  }
  ```
- **参数说明**:
  - `email`: 邮箱（必填，必须唯一）
  - `password`: 密码（必填，长度 >= 6）
  - `username`: 用户名（可选，如果提供必须唯一）
  - `full_name`: 全名（可选）
  - `role`: 用户角色（可选，默认 `"operator"`）
    - 可选值: `"operator"`, `"maintenance"`, `"manager"`
    - **不能设置为 `"admin"`**（管理员角色只能通过脚本或现有管理员分配）
- **响应**:
  ```json
  {
    "code": 0,
    "data": {
      "user_id": "<uuid>",
      "is_verified": true,
      "default_library_id": "<library-uuid>"
    },
    "message": "success"
  }
  ```
- **说明**: 
  - 邮箱必须唯一
  - 密码长度 >= 6
  - 注册时自动创建个人默认库（名为"<full_name|username|email前缀>的个人库"）
  - 如果尝试注册为 `admin` 角色，会返回 400 错误
- **错误示例**:
  ```json
  // 尝试注册为管理员
  {
    "email": "admin@example.com",
    "password": "pwd123",
    "role": "admin"
  }
  // 响应: 400 Bad Request
  {
    "code": 1,
    "message": "Cannot register as admin. Admin role must be assigned by existing administrators."
  }
  ```

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
- **说明**: 
  - Token 包含 `jti`，用于注销时的黑名单管理
  - 响应中的 `is_verified` 字段表示用户邮箱是否已验证
  - **重要**：如果配置了邮箱服务（`ALIYUN_SMTP_PASSWORD`），未验证邮箱的用户**无法使用任何需要JWT认证的功能**
  - 未验证用户会收到 403 错误："Email verification required. Please verify your email before using this feature."
  - 未验证用户可以使用的接口：
    - `POST /api/v1/verify-email` - 验证邮箱
    - `POST /api/v1/resend-verification` - 重新发送验证码
    - `POST /api/v1/forgot-password` - 忘记密码
    - `POST /api/v1/reset-password` - 重置密码

### 1.3 刷新 Token
- **端点**: `POST /api/v1/refresh`
- **认证**: Bearer JWT（如果配置了邮箱服务，需要已验证邮箱）
- **请求体**: 空
- **响应**: 同登录响应结构
- **说明**: 
  - 如果配置了邮箱服务且用户未验证，会返回 403 错误
  - 未验证用户无法刷新token，需要先验证邮箱

### 1.4 注销
- **端点**: `POST /api/v1/logout`
- **认证**: Bearer JWT（如果配置了邮箱服务，需要已验证邮箱）
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
- **说明**: 
  - 将当前 token 的 `jti` 写入 Redis 黑名单，直到 token 过期
  - 如果配置了邮箱服务且用户未验证，会返回 403 错误
  - 未验证用户无法登出，需要先验证邮箱

### 1.5 邮箱验证

- **端点**: `POST /api/v1/verify-email`
- **认证**: 不需要
- **请求体**:
  ```json
  {
    "email": "user@example.com",
    "code": "123456"
  }
  ```
- **响应**:
  ```json
  {
    "code": 0,
    "message": "success",
    "data": {
      "verified": true,
      "message": "Email verified successfully"
    }
  }
  ```
- **说明**: 
  - 使用注册或重新发送验证邮件时收到的6位数字验证码来验证邮箱
  - 验证码5分钟内有效
  - 如果验证码无效或过期，返回 400 错误
  - 如果邮箱服务未配置，返回 503 错误

### 1.6 重新发送验证码

- **端点**: `POST /api/v1/resend-verification`
- **认证**: 不需要
- **请求体**:
  ```json
  {
    "email": "user@example.com"
  }
  ```
- **响应**:
  ```json
  {
    "code": 0,
    "message": "success",
    "data": {
      "message": "If the email exists and is not verified, a verification code has been sent"
    }
  }
  ```
- **说明**: 
  - 如果用户没有收到验证码或验证码已过期，可以使用此接口重新发送
  - 验证码5分钟内有效
  - **重发限制**：发送验证码后需要等待5分钟才能再次发送（防止滥用）
  - 如果在5分钟内重复请求，会返回 429 错误："Please wait X seconds before requesting another verification code"
  - 如果邮箱服务未配置，返回 503 错误
  - 为了安全，即使用户不存在也返回成功（防止邮箱枚举）

### 1.7 忘记密码

- **端点**: `POST /api/v1/forgot-password`
- **认证**: 不需要
- **请求体**:
  ```json
  {
    "email": "user@example.com"
  }
  ```
- **响应**:
  ```json
  {
    "code": 0,
    "message": "success",
    "data": {
      "message": "If the email exists, a password reset link has been sent"
    }
  }
  ```
- **说明**: 
  - 发送密码重置链接到注册邮箱
  - 重置链接1小时内有效
  - 如果邮箱服务未配置，返回 503 错误
  - 为了安全，即使用户不存在也返回成功（防止邮箱枚举）

### 1.8 重置密码

- **端点**: `POST /api/v1/reset-password`
- **认证**: 不需要
- **请求体**:
  ```json
  {
    "token": "reset-token-from-email",
    "new_password": "new_password_123"
  }
  ```
- **响应**:
  ```json
  {
    "code": 0,
    "message": "success",
    "data": {
      "message": "Password reset successfully"
    }
  }
  ```
- **说明**: 
  - 使用忘记密码接口收到的 token 来重置密码
  - Token 1小时内有效
  - 新密码长度至少6位
  - 如果 token 无效或过期，返回 400 错误

### 1.9 删除账号

- **端点**: `DELETE /api/v1/account`
- **认证**: Bearer JWT（只能删除自己的账号）
- **请求体**: 空
- **响应**:
  ```json
  {
    "code": 0,
    "message": "success",
    "data": {
      "deleted": true,
      "user_id": "<uuid>",
      "libraries_deleted": 2,
      "documents_deleted": 10,
      "files_deleted": 10
    }
  }
  ```
- **说明**: 
  - **此操作不可恢复**，会永久删除：
    - 用户账号
    - 用户拥有的所有文档库
    - 文档库中的所有文档和文件
    - 向量数据库中的相关集合
    - 文件系统中的所有文件
    - 用户的群组成员关系
    - 用户的反馈记录
    - Redis 中的相关缓存
  - 用户只能删除自己的账号，不能删除其他用户的账号
  - 与登出（logout）的区别：
    - **登出**：只是让当前 token 失效，账号和数据仍然存在
    - **删除账号**：永久删除账号和所有相关数据
  - 删除后，用户需要重新注册才能使用系统

### 1.10 查看账号信息

- **端点**: `GET /api/v1/account`
- **认证**: Bearer JWT（查看自己的账号信息）
- **请求体**: 无
- **响应**:
  ```json
  {
    "code": 0,
    "message": "success",
    "data": {
      "id": "<user-uuid>",
      "email": "user@example.com",
      "username": "username",
      "full_name": "Full Name",
      "role": "operator",
      "is_active": true,
      "is_verified": true,
      "created_at": "2024-01-01T00:00:00",
      "last_login_at": "2024-01-02T00:00:00",
      "library_count": 2,
      "document_count": 10,
      "group_count": 3
    }
  }
  ```
- **说明**: 
  - 返回当前登录用户的完整账号信息
  - 包括基本信息（邮箱、用户名、角色等）
  - 包括状态信息（是否激活、是否已验证）
  - 包括统计数据：
    - `library_count`: 用户拥有的文档库数量
    - `document_count`: 用户拥有的文档总数
    - `group_count`: 用户加入的群组数量
  - 用户只能查看自己的账号信息

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
  - `owner_id`: 所有者ID
    - 个人库：不需要提供，自动使用当前用户ID
    - 群组库：**必须提供群组ID**（通过 `GET /api/v1/groups` 获取）
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
  - 群组库：需要是群组的 owner 或 admin，且必须提供 `owner_id`（群组ID）
- **创建群组库示例**:
  ```json
  {
    "payload": {
      "name": "群组共享库",
      "owner_type": "group",
      "owner_id": "<group-uuid>",  // 必须提供群组ID
      "description": "群组共享文档库"
    }
  }
  ```

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

## 5. 群组管理 (`/api/v1/groups`)

### 5.1 创建群组
- **端点**: `POST /api/v1/groups`
- **认证**: Bearer JWT
- **请求体**:
  ```json
  {
    "name": "生产团队",
    "description": "生产部门的协作群组"
  }
  ```
- **参数说明**:
  - `name`: 群组名称（必填，1-255 个字符）
  - `description`: 描述（可选，最多 1000 个字符）
- **响应**:
  ```json
  {
    "code": 0,
    "data": {
      "id": "<group-uuid>",
      "name": "生产团队",
      "description": "生产部门的协作群组",
      "member_count": 1,
      "created_at": "2024-01-01T00:00:00"
    },
    "message": "success"
  }
  ```
- **说明**: 创建者自动成为群组的 owner

### 5.2 列出群组
- **端点**: `GET /api/v1/groups`
- **认证**: Bearer JWT
- **响应**:
  ```json
  {
    "code": 0,
    "data": [
      {
        "id": "<group-uuid>",
        "name": "生产团队",
        "description": "生产部门的协作群组",
        "member_count": 5,
        "created_at": "2024-01-01T00:00:00"
      }
    ],
    "message": "success"
  }
  ```
- **说明**: 返回当前用户所属的所有群组

### 5.3 获取群组详情
- **端点**: `GET /api/v1/groups/{group_id}`
- **认证**: Bearer JWT
- **响应**: 同创建群组的响应结构
- **权限**: 必须是群组成员

### 5.4 更新群组
- **端点**: `PUT /api/v1/groups/{group_id}`
- **认证**: Bearer JWT
- **请求体**:
  ```json
  {
    "name": "新名称",
    "description": "新描述"
  }
  ```
- **参数说明**:
  - `name`: 群组名称（可选）
  - `description`: 描述（可选）
- **权限**: 仅 owner 和 admin 可以更新

### 5.5 删除群组
- **端点**: `DELETE /api/v1/groups/{group_id}`
- **认证**: Bearer JWT
- **响应**:
  ```json
  {
    "code": 0,
    "data": {
      "deleted": true,
      "group_id": "<group-uuid>"
    },
    "message": "success"
  }
  ```
- **权限**: 仅 owner 可以删除
- **说明**: 级联删除群组的所有成员和库

### 5.6 邀请成员
- **端点**: `POST /api/v1/groups/{group_id}/members/invite`
- **认证**: Bearer JWT
- **请求体**（两种方式）:
  ```json
  // 方式一：通过用户ID
  {
    "user_id": "<user-uuid>",
    "role": "member"
  }
  
  // 方式二：通过邮箱（推荐）
  {
    "email": "user@example.com",
    "role": "member"
  }
  ```
- **参数说明**:
  - `user_id`: 用户ID（可选，与 `email` 二选一）
  - `email`: 用户邮箱（可选，与 `user_id` 二选一）
  - `role`: 角色，`"owner"` | `"admin"` | `"member"`（默认 `"member"`）
- **响应**:
  ```json
  {
    "code": 0,
    "data": {
      "id": "<member-uuid>",
      "user_id": "<user-uuid>",
      "username": "username",
      "email": "user@example.com",
      "full_name": "Full Name",
      "role": "member",
      "joined_at": "2024-01-01T00:00:00"
    },
    "message": "success"
  }
  ```
- **权限**: 仅 owner 和 admin 可以邀请
- **说明**: 
  - 邀请后用户立即成为成员（无需同意）
  - 如果用户已经是成员，返回 400 错误

### 5.7 列出成员
- **端点**: `GET /api/v1/groups/{group_id}/members`
- **认证**: Bearer JWT
- **响应**:
  ```json
  {
    "code": 0,
    "data": [
      {
        "id": "<member-uuid>",
        "user_id": "<user-uuid>",
        "username": "username",
        "email": "user@example.com",
        "full_name": "Full Name",
        "role": "owner",
        "joined_at": "2024-01-01T00:00:00"
      }
    ],
    "message": "success"
  }
  ```
- **权限**: 必须是群组成员
- **说明**: 按角色排序（owner > admin > member），然后按加入时间排序

### 5.8 更新成员角色
- **端点**: `PUT /api/v1/groups/{group_id}/members/{member_id}/role`
- **认证**: Bearer JWT
- **请求体**:
  ```json
  {
    "role": "admin"
  }
  ```
- **参数说明**:
  - `role`: 新角色，`"owner"` | `"admin"` | `"member"`
- **响应**: 同邀请成员的响应结构
- **权限**: 仅 owner 和 admin 可以更新角色
- **限制**: 
  - 不能修改唯一 owner 的角色
  - 如果只有一个 owner，必须先转移所有权

### 5.9 移除成员
- **端点**: `DELETE /api/v1/groups/{group_id}/members/{member_id}`
- **认证**: Bearer JWT
- **响应**:
  ```json
  {
    "code": 0,
    "data": {
      "removed": true,
      "member_id": "<member-uuid>"
    },
    "message": "success"
  }
  ```
- **权限**: 仅 owner 和 admin 可以移除成员
- **限制**: 
  - 不能移除唯一的 owner
  - 如果只有一个 owner，必须先转移所有权

### 5.10 转移所有权
- **端点**: `POST /api/v1/groups/{group_id}/transfer-ownership`
- **认证**: Bearer JWT
- **请求体**（两种方式）:
  ```json
  // 方式一：通过用户ID
  {
    "new_owner_id": "<user-uuid>"
  }
  
  // 方式二：通过成员ID（推荐）
  {
    "new_owner_member_id": "<member-uuid>"
  }
  ```
- **参数说明**:
  - `new_owner_id`: 新所有者的用户ID（可选，与 `new_owner_member_id` 二选一）
  - `new_owner_member_id`: 新所有者的成员ID（可选，与 `new_owner_id` 二选一）
- **响应**:
  ```json
  {
    "code": 0,
    "data": {
      "transferred": true,
      "group_id": "<group-uuid>",
      "new_owner_id": "<user-uuid>",
      "new_owner_email": "user@example.com",
      "new_owner_username": "username",
      "previous_owner_id": "<user-uuid>"
    },
    "message": "success"
  }
  ```
- **权限**: 仅当前 owner 可以转移所有权
- **说明**: 
  - 原 owner 自动变为 admin
  - 新 owner 必须是群组成员
  - 不能转移给自己
  - 转移后，原 owner（现在是 admin）可以删除自己

### 群组角色说明

- **owner（所有者）**:
  - 可以管理群组（更新、删除）
  - 可以邀请成员、更新角色、移除成员
  - 可以转移所有权
  - 不能删除唯一的 owner（需先转移所有权）

- **admin（管理员）**:
  - 可以管理群组（更新，但不能删除）
  - 可以邀请成员、更新角色、移除成员
  - 不能转移所有权

- **member（成员）**:
  - 可以查看群组和成员列表
  - 可以访问群组库
  - 不能管理群组或成员

---

## 6. 管理接口 (`/api/v1/admin`)

所有管理接口需要管理员权限（`role: "admin"`）。

### 6.1 创建用户（包括管理员）

- **端点**: `POST /api/v1/admin/users`
- **认证**: Bearer JWT（仅管理员）
- **请求体**:
  ```json
  {
    "email": "newadmin@example.com",
    "password": "secure_password_123",
    "username": "NewAdmin",
    "full_name": "New Administrator",
    "role": "admin",
    "is_active": true,
    "is_verified": true
  }
  ```
- **参数说明**:
  - `email`: 邮箱（必填，必须唯一）
  - `password`: 密码（必填，长度 >= 6）
  - `username`: 用户名（可选，如果提供必须唯一）
  - `full_name`: 全名（可选）
  - `role`: 用户角色（可选，默认 `"operator"`）
    - 可选值: `"operator"`, `"maintenance"`, `"manager"`, `"admin"`（管理员可以创建管理员）
  - `is_active`: 是否激活（默认 `true`）
  - `is_verified`: 是否已验证（默认 `true`，管理员创建的用户默认已验证）
- **响应**:
  ```json
  {
    "code": 0,
    "message": "success",
    "data": {
      "id": "<user-uuid>",
      "email": "newadmin@example.com",
      "username": "NewAdmin",
      "full_name": "New Administrator",
      "role": "admin",
      "is_active": true,
      "is_verified": true,
      "created_at": "2025-12-15T01:50:00",
      "last_login_at": null
    }
  }
  ```
- **说明**: 
  - 管理员可以创建任何角色的用户，包括其他管理员
  - 新用户会自动创建个人默认文档库
  - 密码使用 bcrypt 哈希存储
  - 如果邮箱或用户名已存在，返回 400 错误

### 6.2 更新用户信息

- **端点**: `PUT /api/v1/admin/users/{user_id}`
- **认证**: Bearer JWT（仅管理员）
- **路径参数**:
  - `user_id`: 用户 UUID
- **请求体**:
  ```json
  {
    "username": "UpdatedUsername",
    "full_name": "Updated Full Name",
    "role": "manager",
    "is_active": true,
    "is_verified": true,
    "password": "new_password_123"
  }
  ```
- **参数说明**:
  - `username`: 用户名（可选，如果提供必须唯一）
  - `full_name`: 全名（可选）
  - `role`: 用户角色（可选）
    - 可选值: `"operator"`, `"maintenance"`, `"manager"`, `"admin"`
  - `is_active`: 是否激活（可选）
  - `is_verified`: 是否已验证（可选）
  - `password`: 新密码（可选，长度 >= 6）
- **响应**: 同创建用户响应结构
- **说明**: 
  - 管理员可以更新任何用户的信息，包括角色、密码等
  - 如果更新用户名，会检查是否与其他用户冲突

### 6.3 删除用户

- **端点**: `DELETE /api/v1/admin/users/{user_id}`
- **认证**: Bearer JWT（仅管理员）
- **路径参数**:
  - `user_id`: 用户 UUID
- **请求体**: 无
- **响应**:
  ```json
  {
    "code": 0,
    "message": "success",
    "data": {
      "deleted": true,
      "user_id": "<user-uuid>"
    }
  }
  ```
- **说明**: 
  - 删除用户会同时删除其个人文档库和相关数据
  - 不能删除自己（返回 400 错误）
  - 如果用户不存在，返回 404 错误

### 6.4 列出所有用户

- **端点**: `GET /api/v1/admin/users`
- **认证**: Bearer JWT（仅管理员）
- **查询参数**:
  - `limit`: 每页数量（1-200，默认 50）
  - `offset`: 偏移量（默认 0）
  - `role`: 可选，按角色过滤（operator, maintenance, manager, admin）
- **响应**:
  ```json
  {
    "code": 0,
    "data": [
      {
        "id": "<user-uuid>",
        "email": "user@example.com",
        "username": "username",
        "full_name": "Full Name",
        "role": "operator",
        "is_active": true,
        "is_verified": true,
        "created_at": "2024-01-01T00:00:00",
        "last_login_at": "2024-01-02T00:00:00"
      }
    ],
    "message": "success"
  }
  ```
- **权限**: 仅管理员可以访问
- **说明**: 
  - 返回所有已注册用户的信息
  - 支持分页和按角色过滤
  - 不返回密码哈希等敏感信息

### 6.5 获取用户统计信息
- **端点**: `GET /api/v1/admin/users/stats`
- **认证**: Bearer JWT（仅管理员）
- **响应**:
  ```json
  {
    "code": 0,
    "data": {
      "total_users": 100,
      "active_users": 95,
      "verified_users": 90,
      "role_distribution": {
        "operator": 60,
        "maintenance": 20,
        "manager": 15,
        "admin": 5
      }
    },
    "message": "success"
  }
  ```
- **权限**: 仅管理员可以访问
- **说明**: 返回用户总数、活跃用户数、已验证用户数和角色分布统计

### 6.6 健康检查

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

### 6.7 连通性测试

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

## 管理员创建管理员账号的方法

### 方法 1: 使用 API 接口（推荐）

管理员可以通过 `POST /api/v1/admin/users` 接口创建其他管理员账号：

```bash
# 1. 管理员登录获取 token
TOKEN=$(curl -X POST http://localhost:8000/api/v1/login \
  -H "Content-Type: application/json" \
  -d '{"payload": {"email": "louxuezhi@outlook.com", "password": "271828LXZ"}}' \
  | jq -r '.data.access_token')

# 2. 创建新的管理员账号
curl -X POST http://localhost:8000/api/v1/admin/users \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newadmin@example.com",
    "password": "secure_password_123",
    "username": "NewAdmin",
    "full_name": "New Administrator",
    "role": "admin"
  }'
```

### 方法 2: 使用脚本

使用 `scripts/create_admin.py` 脚本：

```bash
python scripts/create_admin.py newadmin@example.com secure_password_123 NewAdmin "New Administrator"
```

### 方法 3: 数据库迁移

通过 Alembic 迁移自动创建（已在 `001_create_admin_user.py` 中实现）：

```bash
alembic upgrade head
```

这会自动创建初始管理员账号（用户名: LXZ, 邮箱: louxuezhi@outlook.com）

---

## 管理员功能总结

管理员（`role: "admin"`）拥有以下权限：

1. **用户管理**:
   - ✅ 创建用户（包括其他管理员）
   - ✅ 更新用户信息（包括角色、密码）
   - ✅ 删除用户
   - ✅ 查看所有用户列表
   - ✅ 获取用户统计信息

2. **系统管理**:
   - ✅ 访问所有管理接口
   - ✅ 不受普通权限限制

3. **安全限制**:
   - ❌ 不能删除自己
   - ❌ 不能通过普通注册接口创建管理员账号（必须通过管理员接口）

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
# 1. 创建文档库（个人库）
POST /api/v1/docs/libraries
{"payload": {"name": "我的库", "owner_type": "user"}}

# 或者创建群组库
# 1.1 先获取群组ID
GET /api/v1/groups

# 1.2 使用群组ID创建库
POST /api/v1/docs/libraries
{"payload": {"name": "群组共享库", "owner_type": "group", "owner_id": "<group-uuid>"}}

# 2. 上传文档
POST /api/v1/docs/ingest
multipart/form-data: file=@document.pdf, library_id=<library-uuid>

# 3. 向量化文档
POST /api/v1/docs/documents/{document_id}/vectorize
{"payload": {"chunk_size": 800}}
```

### 3. 群组协作流程
```bash
# 1. 创建群组
POST /api/v1/groups
{"name": "生产团队", "description": "生产部门"}

# 2. 邀请成员（通过邮箱）
POST /api/v1/groups/{group_id}/members/invite
{"email": "user@example.com", "role": "member"}

# 3. 创建群组库
POST /api/v1/docs/libraries
{"payload": {"name": "群组共享库", "owner_type": "group", "owner_id": "<group-uuid>"}}

# 4. 成员可以上传文档到群组库
POST /api/v1/docs/ingest
multipart/form-data: file=@document.pdf, library_id=<group-library-uuid>
```

### 4. 问答查询
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
7. **群组库创建**: 创建群组库时必须提供 `owner_id`（群组ID），可通过 `GET /api/v1/groups` 获取
8. **群组角色**: owner 可以管理群组和成员，admin 可以管理成员但不能删除群组，member 只能查看和访问
9. **转移所有权**: owner 可以转移所有权给其他成员，转移后原 owner 变为 admin
10. **默认个人库保护**: 用户的默认个人库（注册时自动创建）无法被删除
