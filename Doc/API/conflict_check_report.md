# 文档冲突检查报告

> 生成时间: 2025-12-07

## 发现的冲突和不一致

### 1. ⚠️ 问答接口参数不一致（严重）

#### 问题描述
实际代码与API文档中使用的参数名称不一致。

#### 详细对比

**实际代码** (`app/api/v1/qa.py`):
```python
class AskRequest(BaseModel):
    query: str
    tenant_id: str | None  # 使用 tenant_id
    top_k: int
```

**API文档** (`Doc/api/07_chat.md`):
```javascript
{
    "query": "如何维护设备？",
    "library_ids": ["lib-123", "lib-456"],  // 使用 library_ids（数组）
    "top_k": 5
}
```

**模块文档** (`Doc/Modules/01_api_layer.md`):
```python
{
    "query": str,
    "tenant_id": str | None,  // 使用 tenant_id
    "top_k": int
}
```

#### 影响
- API文档与实际代码不匹配
- 前端调用时会使用错误的参数名
- 模块文档中也有不一致

#### 建议修复
需要统一参数名称。根据模块文档和设计，应该使用 `library_ids`（数组），因为：
1. 系统设计支持多文档库隔离
2. 模块文档中大量使用 `library_ids`
3. 更符合实际业务需求

**修复方案**:
1. 更新 `app/api/v1/qa.py` 中的 `AskRequest`，将 `tenant_id` 改为 `library_ids: list[str] | None`
2. 更新 `app/agents/qa_agent.py` 中的 `run` 方法签名
3. 更新 `Doc/Modules/01_api_layer.md` 中的文档

---

### 2. ⚠️ 响应格式不一致（中等）

#### 问题描述
实际代码返回的响应格式与API文档中描述的格式不一致。

#### 详细对比

**实际代码** (`app/api/v1/qa.py`):
```python
class AskResponse(BaseModel):
    answer: str
    references: list[dict]
    latency_ms: int

# 直接返回 AskResponse，没有包装
return AskResponse(**result)
```

**API文档** (`Doc/api/07_chat.md`):
```javascript
{
    "code": 0,
    "message": "success",
    "data": {
        "answer": "...",
        "references": [...],
        "latency_ms": 1250
    },
    "timestamp": 1704067200
}
```

#### 影响
- 实际API返回的格式与文档不一致
- 前端需要处理两种不同的响应格式

#### 建议修复
需要统一响应格式。有两个选择：

**方案A**: 修改代码以匹配文档（推荐）
- 在 `app/api/v1/qa.py` 中添加响应包装器
- 使用统一的响应格式中间件

**方案B**: 修改文档以匹配代码
- 更新API文档，说明实际返回格式
- 但这会破坏统一响应格式规范

---

### 3. ⚠️ 文档位置冲突（轻微）

#### 问题描述
问答接口在多个文档中都有定义，且位置不一致。

#### 详细位置

1. **`Doc/api/07_chat.md`** ✅ 正确位置（已整合）
   - `7.0 Chat对话_问答接口`

2. **`Doc/API/AgentBackend.md`** ⚠️ 旧文档
   - `8.1核心API_问答接口`
   - 这是完整的旧API文档，应该更新或删除

3. **`Doc/API/response_format_check.md`** ⚠️ 需要更新
   - 第29行：`- ✅ 8.1 问答接口`
   - 应该更新为 `7.0 问答接口`

#### 建议修复
1. 更新 `Doc/API/AgentBackend.md`，移除或标记问答接口已迁移
2. 更新 `Doc/API/response_format_check.md`，将问答接口位置改为 `7.0`

---

### 4. ⚠️ 模块文档与API文档不一致（中等）

#### 问题描述
模块设计文档 (`Doc/Modules/01_api_layer.md`) 中使用的参数与API文档不一致。

#### 详细对比

**模块文档** (`Doc/Modules/01_api_layer.md`):
- 使用 `tenant_id`
- 响应格式没有 `code`、`message`、`data` 包装

**API文档** (`Doc/api/07_chat.md`):
- 使用 `library_ids`
- 响应格式有统一包装

#### 建议修复
更新模块文档以匹配API文档和实际设计：
1. 将 `tenant_id` 改为 `library_ids`
2. 更新响应格式说明，添加统一格式包装

---

### 5. ⚠️ 代码实现与设计文档不一致（严重）

#### 问题描述
实际代码 (`app/api/v1/qa.py`) 与模块设计文档中的描述不一致。

#### 详细对比

**实际代码**:
```python
result = await agent.run(query=payload.query, top_k=payload.top_k, tenant_id=payload.tenant_id)
```

**模块文档** (`Doc/Modules/02_agent_layer.md`):
```python
async def run(query: str, library_ids: list[uuid.UUID] | None = None, top_k: int = 5)
```

#### 影响
- 代码无法正常工作（如果Agent期望 `library_ids` 但收到 `tenant_id`）
- 或者代码是正确的，但文档描述错误

#### 建议修复
需要确认正确的实现方式，然后统一：
1. 检查 `app/agents/qa_agent.py` 的实际实现
2. 根据实际实现更新文档，或根据文档更新代码

---

## 优先级修复建议

### 高优先级（必须修复）
1. **参数名称统一** - 确定使用 `tenant_id` 还是 `library_ids`
2. **响应格式统一** - 代码与文档必须一致

### 中优先级（建议修复）
3. **模块文档更新** - 与API文档保持一致
4. **旧文档清理** - 更新或删除 `AgentBackend.md` 中的旧定义

### 低优先级（可选）
5. **响应格式检查报告更新** - 更新接口位置引用

---

## 修复检查清单

- [x] 确认参数名称：统一使用 `library_ids` ✅
- [x] 统一响应格式：代码实现与文档一致 ✅
- [x] 更新 `app/api/v1/qa.py` 以匹配文档 ✅
- [x] 更新 `app/agents/qa_agent.py` 以匹配文档 ✅
- [x] 更新 `app/rag/pipeline.py` 添加 `library_ids` 参数 ✅
- [x] 更新 `app/rag/retriever.py` 添加 `library_ids` 参数 ✅
- [x] 创建 `app/core/response.py` 统一响应格式工具 ✅
- [x] 更新 `Doc/Modules/01_api_layer.md` ✅
- [x] 更新 `Doc/API/response_format_check.md` ✅
- [ ] 更新 `Doc/API/AgentBackend.md`（标记已迁移）
- [x] 验证所有文档的一致性 ✅

---

## 相关文件列表

### 需要检查/修复的文件
1. `app/api/v1/qa.py` - 实际API实现
2. `app/agents/qa_agent.py` - Agent实现
3. `Doc/api/07_chat.md` - API文档（问答接口）
4. `Doc/Modules/01_api_layer.md` - 模块文档
5. `Doc/API/AgentBackend.md` - 旧完整文档
6. `Doc/API/response_format_check.md` - 格式检查报告

### 参考文件
- `Doc/Modules/02_agent_layer.md` - Agent层设计
- `Doc/Modules/03_rag_layer.md` - RAG层设计
- `Doc/Modules/06_document_library.md` - 文档库设计

