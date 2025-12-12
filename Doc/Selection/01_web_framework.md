# Web框架选型：FastAPI

> 创建时间: 2025-12-07  
> 决策状态: ✅ 已确定

## 选型结果

**选择**: FastAPI  
**版本**: >= 0.111.0  
**ASGI服务器**: Uvicorn (standard)

## 技术特性

### 1. 高性能 ⭐⭐⭐⭐⭐

- **ASGI架构**: 基于Starlette和Pydantic，性能接近NodeJS和Go
- **异步支持**: 原生支持async/await，适合I/O密集型应用
- **基准测试**: 在TechEmpower基准测试中表现优异

```python
# 异步端点示例
@router.post("/ask")
async def ask_entrypoint(payload: AskRequest):
    result = await agent.run(query=payload.query)
    return result
```

### 2. 类型安全和验证 ⭐⭐⭐⭐⭐

- **Pydantic集成**: 自动数据验证和序列化
- **类型提示**: 完整的Python类型系统支持
- **IDE支持**: 优秀的代码补全和类型检查

```python
class AskRequest(BaseModel):
    query: str = Field(..., min_length=3)
    library_ids: list[str] | None = None
    top_k: int = Field(default=5, ge=1, le=20)
```

### 3. 自动API文档 ⭐⭐⭐⭐⭐

- **OpenAPI/Swagger**: 自动生成交互式API文档
- **ReDoc**: 提供美观的文档界面
- **零配置**: 开箱即用的文档功能

### 4. 依赖注入系统 ⭐⭐⭐⭐⭐

- **简洁的DI**: 基于Python类型提示的依赖注入
- **生命周期管理**: 支持单例、请求级别等生命周期
- **测试友好**: 易于mock和测试

```python
@router.post("/ask")
async def ask_entrypoint(
    payload: AskRequest,
    pipeline: RAGPipeline = Depends(get_pipeline),
) -> StandardResponse[AskData]:
    # pipeline自动注入
    pass
```

### 5. 现代化特性 ⭐⭐⭐⭐⭐

- **Python 3.10+**: 支持最新Python特性（类型联合、模式匹配等）
- **WebSocket支持**: 原生WebSocket支持
- **后台任务**: 内置后台任务支持

### 6. 生态兼容性 ⭐⭐⭐⭐

- **SQLAlchemy**: 完美集成异步SQLAlchemy
- **Pydantic**: 统一的数据验证和配置管理
- **第三方库**: 丰富的中间件和插件生态

## 项目中的使用

### 1. API端点定义

```python
from fastapi import APIRouter, Depends
from app.core.response import StandardResponse

router = APIRouter(tags=["qa"])

@router.post("/ask", dependencies=[Depends(get_api_key)])
async def ask_entrypoint(
    payload: AskRequest,
    pipeline: RAGPipeline = Depends(get_pipeline),
) -> StandardResponse[AskData]:
    # 业务逻辑
    pass
```

### 2. 中间件配置

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 3. 错误处理

```python
from fastapi import HTTPException

@router.get("/items/{item_id}")
async def read_item(item_id: int):
    if item_id not in items:
        raise HTTPException(status_code=404, detail="Item not found")
    return items[item_id]
```

## 性能指标

- **吞吐量**: 可处理数万QPS（取决于硬件和业务逻辑）
- **延迟**: P99延迟 < 100ms（简单端点）
- **内存**: 相对轻量，适合容器化部署

## 最佳实践

1. **使用异步**: 所有I/O操作使用async/await
2. **类型提示**: 充分利用类型系统
3. **依赖注入**: 使用Depends管理依赖
4. **响应模型**: 使用Pydantic模型定义响应
5. **错误处理**: 统一错误响应格式

## 总结

FastAPI作为工业问答后端的Web框架：
- ✅ 高性能，适合高并发场景
- ✅ 类型安全，减少运行时错误
- ✅ 自动文档，提升开发效率
- ✅ 异步支持，充分利用现代Python特性
- ✅ 活跃社区，持续更新和维护

## 参考资源

- [FastAPI官方文档](https://fastapi.tiangolo.com/)
- [FastAPI GitHub](https://github.com/tiangolo/fastapi)
- [TechEmpower基准测试](https://www.techempower.com/benchmarks/)

