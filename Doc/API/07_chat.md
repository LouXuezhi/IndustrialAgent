# 7.0 Chat对话模块API

> 创建人: 楼学之
> 更新人: 楼学之
> 创建时间: 2025-12-01 19:52:37
> 更新时间: 2025-12-06 11:48:01

## 模块说明

Chat对话模块提供对话管理相关的API接口，包括问答接口、新建对话、加载历史、发送消息等功能。

**参考文档**: 
- [公共文档](./00_common.md) - 全局参数、响应格式规范
- [模块文档 - Agent层](../Modules/02_agent_layer.md) - Agent层设计文档
- [模块文档 - RAG层](../Modules/03_rag_layer.md) - RAG层设计文档

**重要说明**:
- Agent记忆按Library隔离，不同Library的对话历史不共享
- 会话ID格式：`"{user_id}:{library_id}"`
- 问答接口（7.0）已实现，其他对话管理接口开发中

---

# ❗️7.0Chat对话_

**接口状态**

> 开发中

**接口URL**

> http://localhost/chat

**请求方式**

> GET

**Content-Type**

> none

**认证方式**

> 继承父级

**响应示例**

* 成功(200)

```javascript
暂无数据
```

* 失败(404)

```javascript
暂无数据
```

**Query**

# 7.0Chat对话

> 创建人: 黄明峰

> 更新人: 黄明峰

> 创建时间: 2025-12-05 18:52:27

> 更新时间: 2025-12-05 18:52:31

```text
暂无描述
```

**目录Header参数**

| 参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | ---- | ---- | ---- |
| 暂无参数 |

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

**Query**

## 7.0 Chat对话_问答接口 ⭐

> 创建人: 系统  
> 更新人: 系统  
> 创建时间: 2025-12-07  
> 更新时间: 2025-12-07

```text
提交问答查询，接收用户自然语言问题，返回答案和引用来源。这是Chat对话的核心接口，已实现并可直接使用。
```

**接口状态**

> ✅ 已实现

**接口URL**

> http://localhost/api/v1/ask

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
    "query": "如何维护设备？",        // string, 必填, 用户问题（最少3个字符）
    "library_ids": ["lib-123", "lib-456"],  // array[string], 可选, 指定的文档库ID列表，不指定则搜索所有可访问的文档库
    "top_k": 5                      // integer, 可选, 返回的检索结果数量（1-20，默认5）
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
        "answer": "根据文档，设备维护需要定期检查...",
        "references": [
            {
                "document_id": "doc-123",
                "library_id": "lib-123",
                "score": 0.95,
                "metadata": {
                    "source": "设备维护手册.pdf",
                    "page": 5,
                    "chunk_index": 2
                }
            },
            {
                "document_id": "doc-456",
                "library_id": "lib-123",
                "score": 0.88,
                "metadata": {
                    "source": "操作指南.docx",
                    "page": 10,
                    "chunk_index": 5
                }
            }
        ],
        "latency_ms": 1250
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

* 失败(422) - 请求参数验证失败

```javascript
{
    "code": 422,
    "message": "Validation error",
    "detail": "query字段最少需要3个字符"
}
```

* 失败(500) - 服务器内部错误

```javascript
{
    "code": 500,
    "message": "Internal server error",
    "detail": "服务器处理请求时发生错误"
}
```

**Query**

## 7.1Chat对话_发送消息

> 创建人: 黄明峰

> 更新人: 黄明峰

> 创建时间: 2025-12-03 14:16:08

> 更新时间: 2025-12-05 19:07:40

```text
暂无描述
```

**接口状态**

> 开发中

**接口URL**

> http://localhost/chat/send

**请求方式**

> GET

**Content-Type**

> json

**请求Body参数**

```javascript
暂无数据
```

**认证方式**

> 继承父级

**响应示例**

* 成功(200)

```javascript
暂无数据
```

* 失败(404)

```javascript
暂无数据
```

**Query**

## 7.2.1Chat对话_新建对话

> 创建人: 黄明峰

> 更新人: 黄明峰

> 创建时间: 2025-12-03 14:19:05

> 更新时间: 2025-12-05 19:08:13

```text
暂无描述
```

**接口状态**

> 开发中

**接口URL**

> http://localhost/chat/conversation/new

**请求方式**

> POST

**Content-Type**

> json

**请求Header参数**

| 参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | ---- | ---- | ---- |
| Content-Type | application/json | string | 是 | - |

**请求Body参数**

```javascript
{
	"conversationName": "dolore Ut minim quis consequat"
}
```

**认证方式**

> 继承父级

**响应示例**

* 成功(200)

```javascript
{
	"code": 0,
	"message": "success",
	"data": {
		"conversationId": "aliqua aliquip occaecat ut",
		"conversationName": "eu",
		"createTime": "2000-02-10 02:36:00"
	},
	"timestamp": 1704067200
}
```

* 失败(404)

```javascript
暂无数据
```

**请求Header参数**

| 参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | ---- | ---- | ---- |
| Content-Type | application/json | string | 是 | - |

**Query**

## 7.2.2Chat对话_加载历史对话

> 创建人: 黄明峰

> 更新人: 黄明峰

> 创建时间: 2025-12-03 14:19:55

> 更新时间: 2025-12-05 19:08:31

```text
暂无描述
```

**接口状态**

> 开发中

**接口URL**

> http://localhost/chat/conversation/list

**请求方式**

> GET

**Content-Type**

> none

**认证方式**

> 继承父级

**响应示例**

* 成功(200)

```javascript
暂无数据
```

* 失败(404)

```javascript
暂无数据
```

**Query**

## 7.2.3Chat对话_加载对话历史

> 创建人: 黄明峰

> 更新人: 黄明峰

> 创建时间: 2025-12-03 14:24:49

> 更新时间: 2025-12-05 19:08:53

```text
暂无描述
```

**接口状态**

> 开发中

**接口URL**

> http://localhost/chat/conversation/history?conversationId=

**请求方式**

> GET

**Content-Type**

> none

**请求Query参数**

| 参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | ---- | ---- | ---- |
| conversationId | - | string | 是 | - |

**认证方式**

> 继承父级

**响应示例**

* 成功(200)

```javascript
暂无数据
```

* 失败(404)

```javascript
暂无数据
```

**Query**

## 7.2.4Chat对话_关闭对话

> 创建人: 黄明峰

> 更新人: 黄明峰

> 创建时间: 2025-12-05 14:59:30

> 更新时间: 2025-12-05 19:10:40

```text
暂无描述
```

**接口状态**

> 开发中

**接口URL**

> http://localhost/chat/conversation/close

**请求方式**

> POST

**Content-Type**

> json

**请求Body参数**

```javascript
暂无数据
```

**认证方式**

> 继承父级

**响应示例**

* 成功(200)

```javascript
暂无数据
```

* 失败(404)

```javascript
暂无数据
```

**Query**

## 7.3Chat对话_附件

> 创建人: 黄明峰

> 更新人: 黄明峰

> 创建时间: 2025-12-05 13:01:38

> 更新时间: 2025-12-05 19:09:48

```text
暂无描述
```

**接口状态**

> 开发中

**接口URL**

> http://localhost/chat/attachment

**请求方式**

> GET

**Content-Type**

> form-data

**请求Header参数**

| 参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | ---- | ---- | ---- |
| Content-Type | multipart/form-data | string | 是 | - |

**请求Body参数**

| 参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | ---- | ---- | ---- |
| fileUrl | - | string | 是 | - |
| timestamp | - | string | 是 | - |

**认证方式**

> 继承父级

**响应示例**

* 成功(200)

```javascript
暂无数据
```

* 失败(404)

```javascript
暂无数据
```

**请求Header参数**

| 参数名 | 示例值 | 参数类型 | 是否必填 | 参数描述 |
| --- | --- | ---- | ---- | ---- |
| Content-Type | multipart/form-data | string | 是 | - |

**Query**

## 7.4Chat对话_重新生成

> 创建人: 黄明峰

> 更新人: 黄明峰

> 创建时间: 2025-12-05 15:06:05

> 更新时间: 2025-12-05 19:10:22

```text
暂无描述
```

**接口状态**

> 开发中

**接口URL**

> http://localhost/chat/resend

**请求方式**

> GET

**Content-Type**

> json

**请求Body参数**

```javascript
暂无数据
```

**认证方式**

> 继承父级

**响应示例**

* 成功(200)

```javascript
暂无数据
```

* 失败(404)

```javascript
暂无数据
```

**Query**

