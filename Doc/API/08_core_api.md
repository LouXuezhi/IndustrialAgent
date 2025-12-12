# 8.0 核心API接口模块

> 创建人: 系统
> 更新人: 系统
> 创建时间: 2025-12-01
> 更新时间: 2025-12-07

## 模块说明

核心API接口模块提供系统的基础功能接口，包括文档管理、系统管理等。这些接口是系统的核心功能，已实现并可直接使用。

**注意**: 问答接口已整合到 [Chat对话模块](./07_chat.md#70-chat对话_问答接口)。

**参考文档**: 
- [公共文档](./00_common.md) - 全局参数、响应格式规范
- [模块文档 - API层](../Modules/01_api_layer.md) - API层设计文档
- [Chat对话模块](./07_chat.md) - 问答接口已整合到此模块

**接口状态**: ✅ 已实现

---

# ❗️8.0核心API接口_

**接口状态**

> 已实现

**接口URL**

> http://localhost/api/v1

**请求方式**

> 多种（GET/POST）

**Content-Type**

> application/json / multipart/form-data

**认证方式**

> API Key (X-API-Key Header)

**Query**

# 8.0核心API接口

> 创建人: 系统

> 更新人: 系统

> 创建时间: 2025-12-07

> 更新时间: 2025-12-07

```text
核心API接口定义，包括问答、文档管理、系统管理等基础功能
```

**目录Header参数**

| 参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | ---- | ---- | ---- |
| X-API-Key | your-api-key-here | string | 是 | API密钥（除健康检查接口外） |

**目录Query参数**

| 参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | ---- | ---- | ---- |
| 暂无参数 |

**目录Body参数**

| 参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | ---- | ---- | ---- |
| 暂无参数 |

**目录认证信息**

> API Key认证（X-API-Key Header）

## 8.1核心API_文档摄取接口

> 创建人: 系统

> 更新人: 系统

> 创建时间: 2025-12-07

> 更新时间: 2025-12-07

```text
上传并摄取文档到知识库，支持PDF、DOCX、TXT等格式
```

**接口状态**

> 已实现

**接口URL**

> http://localhost/api/v1/docs/ingest

**请求方式**

> POST

**Content-Type**

> multipart/form-data

**请求Header参数**

| 参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | ---- | ---- | ---- |
| X-API-Key | your-api-key-here | string | 是 | API密钥 |
| Content-Type | multipart/form-data | string | 是 | 请求内容类型 |

**请求Body参数**

| 参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | ---- | ---- | ---- |
| file | (文件) | file | 是 | 上传的文件（PDF、DOCX、TXT等） |
| library_id | lib-123 | string | 可选 | 文档库ID，不指定则使用默认文档库 |

**认证方式**

> API Key认证

**响应示例**

* 成功(200)

```javascript
{
    "code": 0,
    "message": "success",
    "data": {
        "document_id": "doc-789",
        "library_id": "lib-123",
        "chunks": 15,
        "title": "设备维护手册.pdf",
        "file_size": 1024000,
        "file_type": "application/pdf"
    },
    "timestamp": 1704067200
}
```

* 失败(401) - API Key无效

```javascript
{
    "code": 401,
    "message": "Invalid or missing API key",
    "detail": "API Key缺失或无效"
}
```

* 失败(400) - 文件格式不支持

```javascript
{
    "code": 400,
    "message": "Unsupported file type",
    "detail": "不支持的文件格式，仅支持PDF、DOCX、TXT等格式"
}
```

* 失败(500) - 服务器内部错误

```javascript
{
    "code": 500,
    "message": "Internal server error",
    "detail": "文档处理失败"
}
```

**Query**

## 8.2核心API_索引重建接口

> 创建人: 系统

> 更新人: 系统

> 创建时间: 2025-12-07

> 更新时间: 2025-12-07

```text
触发全量索引重建（异步任务）
```

**接口状态**

> 已实现（占位实现）

**接口URL**

> http://localhost/api/v1/docs/reindex

**请求方式**

> POST

**Content-Type**

> application/json

**请求Header参数**

| 参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | ---- | ---- | ---- |
| X-API-Key | your-api-key-here | string | 是 | API密钥 |
| Content-Type | application/json | string | 是 | 请求内容类型 |

**请求Body参数**

```javascript
{
    "library_id": "lib-123"  // string, 可选, 文档库ID，不指定则重建所有文档库的索引
}
```

**认证方式**

> API Key认证

**响应示例**

* 成功(200)

```javascript
{
    "code": 0,
    "message": "success",
    "data": {
        "status": "queued",
        "task_id": "task-123",
        "estimated_time": 300
    },
    "timestamp": 1704067200
}
```

* 失败(401) - API Key无效

```javascript
{
    "code": 401,
    "message": "Invalid or missing API key",
    "detail": "API Key缺失或无效"
}
```

* 失败(500) - 服务器内部错误

```javascript
{
    "code": 500,
    "message": "Internal server error",
    "detail": "索引重建任务创建失败"
}
```

**Query**

## 8.3核心API_健康检查接口

> 创建人: 系统

> 更新人: 系统

> 创建时间: 2025-12-07

> 更新时间: 2025-12-07

```text
系统健康检查端点，用于Kubernetes/Docker健康检查、负载均衡器健康探测
```

**接口状态**

> 已实现

**接口URL**

> http://localhost/api/v1/admin/healthz

**请求方式**

> GET

**Content-Type**

> none

**认证方式**

> 无需认证

**响应示例**

* 成功(200)

```javascript
{
    "code": 0,
    "message": "success",
    "data": {
        "status": "healthy",
        "timestamp": 1704067200,
        "service": "Industrial QA Backend",
        "version": "0.1.0"
    },
    "timestamp": 1704067200
}
```

* 失败(503) - 服务不健康

```javascript
{
    "code": 503,
    "message": "Service unhealthy",
    "detail": "数据库连接失败"
}
```

**Query**

## 8.4核心API_Ping接口

> 创建人: 系统

> 更新人: 系统

> 创建时间: 2025-12-07

> 更新时间: 2025-12-07

```text
简单连通性测试接口
```

**接口状态**

> 已实现

**接口URL**

> http://localhost/api/v1/admin/ping

**请求方式**

> GET

**Content-Type**

> none

**认证方式**

> 无需认证

**响应示例**

* 成功(200)

```javascript
{
    "code": 0,
    "message": "success",
    "data": {
        "message": "pong"
    },
    "timestamp": 1704067200
}
```

**Query**

