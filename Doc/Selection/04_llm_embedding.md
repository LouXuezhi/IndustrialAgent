# LLM和Embedding模型选型

> 创建时间: 2025-12-07  
> 决策状态: ✅ 已确定（支持多方案）

## 选型结果

**LLM策略**: 支持大厂API（Qwen、DeepSeek） + 本地模型  
**Embedding策略**: 支持大厂API + 本地模型  
**框架**: LangChain统一接口  
**策略**: 统一接口抽象，支持多提供商和本地模型切换

## 已选定的技术方案

### LLM方案
- **Qwen (通义千问)**: Qwen-Max/Qwen-Plus/Qwen-Turbo
- **DeepSeek**: DeepSeek-Chat
- **本地模型**: Qwen/LLaMA/Mistral (vLLM/Ollama)

### Embedding方案
- **Qwen Embedding**: DashScope API
- **本地模型**: BGE-Large、Qwen Embedding (HuggingFace)

## LLM方案

### Qwen (通义千问)

#### 特性
- **中文优化**: 专为中文场景优化，中文理解能力强
- **成本低**: 价格竞争力强，性价比高
- **性能优秀**: Qwen-Max在多个中文基准测试中表现优异
- **国内服务**: 阿里云DashScope，数据合规性好
- **LangChain支持**: 官方LangChain集成

#### 模型选择
- **Qwen-Max**: 最强性能，适合复杂任务
- **Qwen-Plus**: 平衡性能和成本
- **Qwen-Turbo**: 快速响应，适合实时场景

#### 配置示例
```python
# .env
LLM_PROVIDER=dashscope
LLM_MODEL=qwen-max
DASHSCOPE_API_KEY=sk-xxx
```

#### LangChain集成
```python
from langchain_community.llms import Tongyi

llm = Tongyi(
    model_name="qwen-max",
    dashscope_api_key=settings.dashscope_api_key,
    temperature=0.7
)
```

### DeepSeek

#### 特性
- **中文优化**: 针对中文场景深度优化
- **成本极低**: 价格竞争力强，性价比极高
- **性能优秀**: DeepSeek-Chat在中文任务上表现优异
- **响应快速**: 低延迟，适合实时场景
- **LangChain支持**: 官方LangChain集成

#### 配置示例
```python
# .env
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-chat
DEEPSEEK_API_KEY=sk-xxx
```

#### LangChain集成
```python
from langchain_community.llms import DeepSeek

llm = DeepSeek(
    model_name="deepseek-chat",
    deepseek_api_key=settings.deepseek_api_key,
    temperature=0.7
)
```

### 本地模型 (私有部署)

#### 特性
- **数据安全**: 完全私有化部署，数据不出境
- **成本可控**: 一次投入，无API调用费用
- **可定制**: 可以微调和优化模型
- **无限制**: 不受API调用频率限制

#### 支持的本地模型
- **Qwen系列**: Qwen-7B/14B/72B
- **LLaMA系列**: LLaMA-2/3
- **Mistral系列**: Mistral-7B
- **ChatGLM**: ChatGLM-6B/3-6B

#### 配置示例（vLLM）
```python
# .env
LLM_PROVIDER=local_vllm
LLM_MODEL=Qwen/Qwen-14B-Chat
LLM_BASE_URL=http://localhost:8000/v1
```

#### LangChain集成（vLLM）
```python
from langchain_community.llms import VLLM

llm = VLLM(
    model="Qwen/Qwen-14B-Chat",
    trust_remote_code=True,
    max_new_tokens=512,
    temperature=0.7
)
```

#### 配置示例（Ollama）
```python
# .env
LLM_PROVIDER=local_ollama
LLM_MODEL=qwen:14b
LLM_BASE_URL=http://localhost:11434
```

#### LangChain集成（Ollama）
```python
from langchain_community.llms import Ollama

llm = Ollama(
    model="qwen:14b",
    base_url="http://localhost:11434"
)
```

## Embedding方案

### Qwen Embedding

#### 特性
- **中文优化**: 专为中文场景优化，中文语义理解强
- **成本低**: DashScope API价格竞争力强
- **性能优秀**: 在中文Embedding基准测试中表现优异
- **维度适中**: 1024维，平衡性能和效果
- **LangChain支持**: 官方LangChain集成

#### 配置示例
```python
# .env
EMBEDDING_PROVIDER=dashscope
EMBEDDING_MODEL=text-embedding-v2
DASHSCOPE_API_KEY=sk-xxx
```

#### LangChain集成
```python
from langchain_community.embeddings import DashScopeEmbeddings

embeddings = DashScopeEmbeddings(
    model="text-embedding-v2",
    dashscope_api_key=settings.dashscope_api_key
)
```

### BGE-Large (本地部署)

#### 特性
- **开源免费**: 可本地部署，无API费用
- **中文优化**: 针对中英文优化
- **性能优秀**: 在多个基准测试中表现优异
- **维度适中**: 1024维，平衡性能和效果

#### 配置示例
```python
# .env
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=bge-large-zh-v1.5
EMBEDDING_MODEL_PATH=/path/to/bge-large
```

#### LangChain集成（本地）
```python
from langchain_community.embeddings import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-large-zh-v1.5",
    model_kwargs={'device': 'cuda'}  # 或 'cpu'
)
```

### 本地Qwen Embedding

#### 配置示例
```python
# .env
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=qwen-embedding
EMBEDDING_MODEL_PATH=/path/to/qwen-embedding
```

#### LangChain集成
```python
from langchain_community.embeddings import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(
    model_name="Qwen/Qwen-Embedding",
    model_kwargs={'device': 'cuda'}
)
```

## 项目中的实现（基于LangChain）

### LangChain统一接口

LangChain提供了统一的接口抽象，支持多种LLM和Embedding提供商：

```python
# app/rag/llm.py
from langchain_community.llms import Tongyi, DeepSeek, VLLM, Ollama
from langchain_core.language_models import BaseLLM

def get_llm(settings: Settings) -> BaseLLM:
    """根据配置获取LLM实例"""
    if settings.llm_provider == "dashscope":
        return Tongyi(
            model_name=settings.llm_model,  # qwen-max, qwen-plus, qwen-turbo
            dashscope_api_key=settings.dashscope_api_key,
            temperature=0.7
        )
    elif settings.llm_provider == "deepseek":
        return DeepSeek(
            model_name=settings.llm_model,  # deepseek-chat
            deepseek_api_key=settings.deepseek_api_key,
            temperature=0.7
        )
    elif settings.llm_provider == "local_vllm":
        return VLLM(
            model=settings.llm_model,  # Qwen/Qwen-14B-Chat
            trust_remote_code=True,
            max_new_tokens=512,
            temperature=0.7
        )
    elif settings.llm_provider == "local_ollama":
        return Ollama(
            model=settings.llm_model,  # qwen:14b
            base_url=settings.llm_base_url or "http://localhost:11434"
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")

# app/rag/embedding.py
from langchain_community.embeddings import (
    DashScopeEmbeddings,
    HuggingFaceEmbeddings
)
from langchain_core.embeddings import Embeddings

def get_embeddings(settings: Settings) -> Embeddings:
    """根据配置获取Embedding实例"""
    if settings.embedding_provider == "dashscope":
        return DashScopeEmbeddings(
            model="text-embedding-v2",
            dashscope_api_key=settings.dashscope_api_key
        )
    elif settings.embedding_provider == "local":
        return HuggingFaceEmbeddings(
            model_name=settings.embedding_model,  # BAAI/bge-large-zh-v1.5
            model_kwargs={'device': settings.embedding_device or 'cpu'}
        )
    else:
        raise ValueError(f"Unsupported embedding provider: {settings.embedding_provider}")
```

### 配置示例

```python
# .env

# LLM配置 - Qwen
LLM_PROVIDER=dashscope
LLM_MODEL=qwen-max
DASHSCOPE_API_KEY=sk-xxx

# LLM配置 - DeepSeek
# LLM_PROVIDER=deepseek
# LLM_MODEL=deepseek-chat
# DEEPSEEK_API_KEY=sk-xxx

# LLM配置 - 本地模型（vLLM）
# LLM_PROVIDER=local_vllm
# LLM_MODEL=Qwen/Qwen-14B-Chat
# LLM_BASE_URL=http://localhost:8000/v1

# LLM配置 - 本地模型（Ollama）
# LLM_PROVIDER=local_ollama
# LLM_MODEL=qwen:14b
# LLM_BASE_URL=http://localhost:11434

# Embedding配置 - Qwen Embedding
EMBEDDING_PROVIDER=dashscope
EMBEDDING_MODEL=text-embedding-v2
# DASHSCOPE_API_KEY已在上面配置

# Embedding配置 - 本地BGE
# EMBEDDING_PROVIDER=local
# EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5
# EMBEDDING_DEVICE=cuda  # 或 cpu

# Embedding配置 - 本地Qwen
# EMBEDDING_PROVIDER=local
# EMBEDDING_MODEL=Qwen/Qwen-Embedding
# EMBEDDING_DEVICE=cuda
```

## 成本对比（参考）

### LLM成本（每1000 tokens，人民币）

| 模型 | 输入 | 输出 | 月调用量 | 月成本估算 |
|------|------|------|---------|-----------|
| **Qwen-Max** | ¥0.12 | ¥0.12 | 100万 | ~¥120 |
| **Qwen-Plus** | ¥0.08 | ¥0.08 | 100万 | ~¥80 |
| **Qwen-Turbo** | ¥0.008 | ¥0.008 | 100万 | ~¥8 |
| **DeepSeek-Chat** | ¥0.14 | ¥0.14 | 100万 | ~¥140 |
| GPT-4o-mini | $0.15 | $0.60 | 100万 | ~$750 (≈¥5,400) |
| **本地模型** | 一次性 | 一次性 | 无限制 | 服务器成本 |

### Embedding成本（每1000 tokens，人民币）

| 模型 | 成本 | 月调用量 | 月成本估算 |
|------|------|---------|-----------|
| **Qwen Embedding** | ¥0.0007 | 1000万 | ~¥7 |
| **BGE-Large (本地)** | ¥0 | 1000万 | ¥0 |
| **Qwen Embedding (本地)** | ¥0 | 1000万 | ¥0 |

## 部署建议

### 开发环境
- **LLM**: Qwen-Turbo 或 DeepSeek
- **Embedding**: Qwen Embedding API

### 生产环境
- **LLM**: Qwen-Max/Plus 或 本地Qwen部署
- **Embedding**: Qwen Embedding API 或 本地BGE/Qwen部署

### 数据安全要求高
- **LLM**: 本地vLLM部署（Qwen-14B/72B）
- **Embedding**: 本地BGE/Qwen部署

## 最佳实践

1. **模型选择**: 根据任务复杂度选择合适模型
2. **成本优化**: 使用缓存减少重复调用
3. **降级策略**: 支持模型降级（GPT-4o → GPT-4o-mini）
4. **监控告警**: 监控API调用成本和错误率
5. **A/B测试**: 对比不同模型的效果

## 总结

- **主要选择**: Qwen/DeepSeek + Qwen Embedding（大厂API）
- **本地支持**: 支持本地模型部署（Qwen/BGE）
- **统一框架**: 基于LangChain统一接口
- **灵活切换**: 根据业务需求选择合适的模型和部署方式
- **成本优化**: 提供本地部署选项大幅降低成本
- **数据安全**: 支持完全私有化部署

## 参考资源

- [BGE模型](https://github.com/FlagOpen/FlagEmbedding)
- [DashScope文档](https://help.aliyun.com/zh/model-studio/)
- [DeepSeek文档](https://platform.deepseek.com/)
- [LangChain文档](https://python.langchain.com/)

