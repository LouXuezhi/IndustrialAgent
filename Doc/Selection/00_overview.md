# 技术选型总览

> 创建时间: 2025-12-07  
> 更新人: 系统

## 文档说明

本文档目录包含工业问答后端系统的技术选型文档，详细说明各个技术栈的选择理由、对比分析和最佳实践。

## 技术选型文档结构

```
Doc/Selection/
├── 00_overview.md           # 本文档（技术选型总览）
├── 01_web_framework.md      # Web框架选型（FastAPI）
├── 02_database.md           # 数据库选型（SQLAlchemy + 向量数据库）
├── 03_vector_db.md          # 向量数据库选型（Chroma/Qdrant/Milvus/pgvector）
├── 04_llm_embedding.md      # LLM和Embedding模型选型
├── 05_retrieval.md          # 检索策略选型（混合检索）
├── 06_auth_security.md      # 认证和授权选型
├── 07_rag_framework.md      # RAG框架选型（LangChain/LlamaIndex）
└── 08_deployment.md         # 部署和运维选型
```

## 技术栈概览

### 核心架构层

| 层级 | 技术选型 | 主要组件 |
|------|---------|---------|
| **API层** | FastAPI | FastAPI + Pydantic + Uvicorn |
| **Agent层** | LangChain | LangChain Agent + Tools |
| **RAG层** | LangChain | LangChain RAG Pipeline + 混合检索器 |
| **存储层** | 多存储方案 | SQLAlchemy + MySQL + Redis + Chroma/Qdrant/Milvus/pgvector |

### 关键技术组件

1. **Web框架**: FastAPI
   - 异步支持
   - 自动API文档
   - 类型安全

2. **关系数据库**: SQLAlchemy (异步) + MySQL
   - MySQL (生产) / SQLite (开发)
   - 异步ORM
   - 迁移工具（Alembic）

3. **缓存数据库**: Redis
   - 查询结果缓存
   - 会话存储
   - 频率限制

4. **向量数据库**: Chroma (默认)
   - 可选：Qdrant, Milvus, pgvector
   - 支持多向量库适配

4. **检索策略**: 混合检索
   - 向量检索（语义相似度）
   - BM25（关键词匹配）
   - 融合排序

5. **LLM集成**: Qwen/DeepSeek (主要) + 本地模型
   - 大厂API：Qwen (DashScope), DeepSeek
   - 本地模型：vLLM, Ollama
   - 基于LangChain统一接口

6. **Embedding模型**: Qwen Embedding (主要) + 本地模型
   - 大厂API：Qwen Embedding (DashScope)
   - 本地模型：BGE-Large, Qwen Embedding
   - 基于LangChain统一接口

7. **RAG框架**: LangChain
   - Agent和RAG统一使用LangChain
   - 丰富的组件和集成

8. **邮件服务**: 阿里云邮件推送
   - 国内服务，稳定可靠
   - 免费额度：每天200封
   - 用于邮箱验证、密码重置等

7. **认证授权**: API Key + RBAC
   - API Key认证
   - 基于角色的访问控制

## 选型原则

1. **性能优先**: 选择高性能、低延迟的技术方案
2. **可扩展性**: 支持水平扩展和模块化替换
3. **开发效率**: 提供良好的开发体验和文档
4. **社区支持**: 选择活跃的开源社区
5. **生产就绪**: 经过生产环境验证的成熟技术
6. **成本效益**: 平衡性能和成本

## 技术选型决策流程

1. **需求分析**: 明确业务需求和技术要求
2. **候选方案**: 列出可行的技术方案
3. **对比评估**: 从性能、成本、生态等维度对比
4. **POC验证**: 进行概念验证和性能测试
5. **决策确认**: 确定最终选型并记录理由
6. **持续优化**: 根据实际使用情况调整

## 快速导航

- [Web框架选型](./01_web_framework.md) - FastAPI选型理由
- [数据库选型](./02_database.md) - SQLAlchemy和向量数据库选型
- [向量数据库选型](./03_vector_db.md) - Chroma/Qdrant/Milvus/pgvector对比
- [LLM和Embedding选型](./04_llm_embedding.md) - 模型选择策略
- [检索策略选型](./05_retrieval.md) - 混合检索方案
- [RAG框架选型](./07_rag_framework.md) - LangChain
- [邮件服务选型](./09_email_service.md) - 阿里云邮件推送
- [认证授权选型](./06_auth_security.md) - 安全方案（待补充）
- [部署运维选型](./08_deployment.md) - 容器化和监控方案（待补充）

## 更新日志

- 2025-12-07: 创建技术选型文档结构

