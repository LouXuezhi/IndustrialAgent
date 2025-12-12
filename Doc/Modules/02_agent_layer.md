# Agent层模块文档

## 概述
Agent层负责编排问答流程，协调RAG Pipeline和工具调用。当前实现为简化版本，未来可扩展为多工具Agent系统。

## 模块结构

```
app/agents/
├── qa_agent.py    # QA Agent核心实现
└── tools.py       # 工具注册表
```

## 1. QA Agent (`qa_agent.py`)

### 功能
QA Agent是问答流程的编排器，负责：
- 接收用户查询和用户上下文
- 根据用户角色选择prompt模板
- 根据用户权限过滤文档库范围
- 调用RAG Pipeline获取答案
- 格式化返回结果

### 类定义

```python
from app.users.permissions import UserContext

@dataclass
class QAAgent:
    pipeline: RAGPipeline        # RAG流水线实例
    user_context: UserContext    # 用户上下文（角色、权限、可访问文档库）
```

### 方法

#### `async def run(query: str, library_ids: list[uuid.UUID] | None = None, top_k: int = 5) -> dict[str, Any]`
**描述**: 执行问答查询

**参数**:
- `query`: 用户查询字符串
- `library_ids`: 指定的文档库ID列表（可选，不指定则搜索所有可访问的文档库）
- `top_k`: 检索结果数量（默认5）

**返回**:
```python
{
    "answer": str,                    # 生成的答案
    "references": list[dict],         # 引用来源（包含library_id）
    "latency_ms": int                 # 处理延迟（毫秒）
}
```

**实现流程**:
1. **文档库范围确定**:
   - 如果指定了`library_ids`，验证用户是否有权限访问这些文档库
   - 如果未指定，使用用户可访问的所有文档库
   - 过滤掉用户无权限访问的文档库

2. **角色和权限传递**:
   - 从`user_context`获取用户角色
   - 将角色传递给RAG Pipeline（用于选择prompt模板）
   - 将权限列表传递给RAG Pipeline（用于结果过滤）

3. **调用RAG Pipeline**:
   - 传递查询、文档库ID列表、角色、权限
   - 获取检索和生成结果

4. **结果格式化**:
   - 提取答案、引用和延迟信息
   - 确保引用中包含文档库ID信息
   - 返回格式化的结果字典

**实现示例**:
```python
@dataclass
class QAAgent:
    pipeline: RAGPipeline
    user_context: UserContext
    
    async def run(
        self,
        query: str,
        library_ids: list[uuid.UUID] | None = None,
        top_k: int = 5
    ) -> dict[str, Any]:
        # 1. 确定文档库范围
        if library_ids is None:
            # 使用用户可访问的所有文档库
            library_ids = self.user_context.accessible_library_ids
        else:
            # 过滤：只保留用户有权限访问的文档库
            library_ids = [
                lib_id for lib_id in library_ids
                if self.user_context.can_access_library(lib_id)
            ]
        
        if not library_ids:
            raise ValueError("No accessible libraries")
        
        # 2. 调用RAG Pipeline（传递角色和文档库范围）
        result: PipelineResult = await self.pipeline.run(
            query=query,
            library_ids=library_ids,
            top_k=top_k,
            role=self.user_context.role,  # 用于选择prompt模板
            user_permissions=self.user_context.permissions  # 用于权限过滤
        )
        
        # 3. 格式化返回结果
        return {
            "answer": result.answer,
            "references": result.references,  # 已包含library_id
            "latency_ms": result.latency_ms,
        }
```

### 用户上下文管理

Agent通过`UserContext`获取用户信息：

```python
from app.users.permissions import UserContext

# UserContext包含：
# - user_id: 用户ID
# - email: 用户邮箱
# - role: 用户角色（operator/maintenance/manager/admin）
# - permissions: 权限列表
# - accessible_library_ids: 可访问的文档库ID列表
# - group_ids: 用户所在的群组ID列表
```

### Agent记忆隔离

**重要**: Agent的记忆（对话历史）按Library隔离：

1. **会话上下文隔离**:
   - 每个Library有独立的会话上下文
   - 会话ID包含library_id：`session_id = f"{user_id}:{library_id}"`
   - 不同Library之间的对话历史不共享

2. **记忆存储**:
```python
class QAAgent:
    def __init__(self, pipeline: RAGPipeline, user_context: UserContext, library_id: uuid.UUID):
        self.pipeline = pipeline
        self.user_context = user_context
        self.library_id = library_id  # 当前Library ID
        self.memory = AgentMemory(library_id=library_id)  # Library级别的记忆
    
    async def run(self, query: str, ...):
        # 获取当前Library的对话历史
        history = await self.memory.get_conversation_history(
            user_id=self.user_context.user_id,
            library_id=self.library_id  # 只获取当前Library的历史
        )
        
        # 使用历史上下文（限制在当前Library）
        result = await self.pipeline.run(
            query=query,
            library_ids=[self.library_id],  # 只搜索当前Library
            conversation_history=history  # 当前Library的历史
        )
        
        # 保存对话历史（按Library隔离）
        await self.memory.save_conversation(
            user_id=self.user_context.user_id,
            library_id=self.library_id,
            query=query,
            answer=result.answer
        )
```

3. **多Library查询**:
   - 如果用户指定多个library_ids，Agent会为每个Library维护独立的记忆
   - 但检索结果会合并，记忆仍然隔离

### 角色与Prompt关联

Agent根据用户角色选择不同的prompt模板：

- **operator**: 技术细节、操作步骤导向的prompt
- **maintenance**: 维护流程、故障排查导向的prompt
- **manager**: 决策支持、数据分析导向的prompt
- **admin**: 系统管理导向的prompt

角色信息传递给RAG Pipeline，由`prompts.py`模块根据角色选择对应的模板。

### 未来扩展方向

1. **意图分类**:
   ```python
   intent = await classify_intent(query)
   if intent == "calculation":
       return await calculator_tool.run(query)
   elif intent == "knowledge_search":
       return await pipeline.run(query)
   ```

2. **多工具编排**:
   - 根据查询类型选择合适工具
   - 支持工具链式调用
   - 支持并行工具调用

3. **租户隔离**:
   - 根据tenant_id过滤知识库
   - 应用租户特定的配置
   - 记录租户级别的使用统计

## 2. 工具系统 (`tools.py`)

### 功能
定义工具协议和具体工具实现，为Agent提供可调用的能力。

### 工具协议

```python
class Tool(Protocol):
    name: str                    # 工具名称
    description: str             # 工具描述
    
    async def run(self, query: str) -> str:
        """执行工具并返回结果"""
        ...
```

### 已实现工具

#### 1. KnowledgeBaseTool
**名称**: `knowledge_base_search`

**描述**: 搜索内部知识库获取相关片段

**当前实现**: 占位实现，返回模拟结果

**未来实现**:
- 调用RAG Retriever搜索知识库
- 返回相关文档片段
- 支持过滤和排序

#### 2. CalculatorTool
**名称**: `calculator`

**描述**: 执行基本数值计算

**实现**:
- 使用Python的 `eval` 函数（受限环境）
- 支持基本数学运算
- 错误处理

**安全注意**: 当前实现使用 `eval`，生产环境应使用更安全的表达式解析器（如 `ast.literal_eval` 或专用数学库）

### 工具注册机制

当前为静态定义，未来可扩展为动态注册：

```python
# 未来扩展示例
class ToolRegistry:
    _tools: dict[str, Tool] = {}
    
    @classmethod
    def register(cls, tool: Tool):
        cls._tools[tool.name] = tool
    
    @classmethod
    def get(cls, name: str) -> Tool:
        return cls._tools[name]
```

### 工具扩展指南

添加新工具的步骤：

1. **定义工具类**:
```python
@dataclass
class MyCustomTool:
    name: str = "my_tool"
    description: str = "Tool description"
    
    async def run(self, query: str) -> str:
        # 实现工具逻辑
        return "result"
```

2. **在Agent中集成**:
```python
# 在qa_agent.py中
tools = {
    "knowledge_base_search": KnowledgeBaseTool(),
    "calculator": CalculatorTool(),
    "my_tool": MyCustomTool(),
}
```

3. **实现工具选择逻辑**:
```python
def select_tool(query: str) -> Tool:
    # 基于查询内容选择合适工具
    if "calculate" in query.lower():
        return tools["calculator"]
    return tools["knowledge_base_search"]
```

## Agent工作流程

### 当前流程（简化版）
```
用户查询
    ↓
QAAgent.run()
    ↓
RAG Pipeline.run()
    ↓
返回答案
```

### 未来流程（完整版）
```
用户查询
    ↓
意图分类
    ↓
工具选择
    ├─► KnowledgeBaseTool → RAG Pipeline
    ├─► CalculatorTool → 计算
    └─► OtherTool → 其他操作
    ↓
结果合并/格式化
    ↓
返回答案
```

## 集成点

### 与RAG Pipeline集成
- Agent通过依赖注入获取RAG Pipeline实例
- 调用Pipeline的 `run` 方法执行检索和生成

### 与API层集成
- API端点创建Agent实例
- Agent处理业务逻辑，API层处理HTTP协议

### 与工具系统集成
- Agent根据查询选择并调用工具
- 工具可以是RAG Pipeline或其他能力

## 性能考虑

1. **异步执行**: Agent方法为异步，支持并发请求
2. **缓存**: 可添加查询结果缓存（Redis等）
3. **超时控制**: 应添加工具调用超时机制
4. **重试机制**: 对失败的工具调用实现重试

## 测试建议

1. **单元测试**: 测试Agent的查询处理逻辑
2. **集成测试**: 测试Agent与Pipeline的集成
3. **工具测试**: 测试各个工具的功能正确性
4. **端到端测试**: 测试完整的API → Agent → Pipeline流程

