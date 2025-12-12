# 技术选型文档索引

> 创建时间: 2025-12-07

## 文档说明

本目录包含工业问答后端系统的完整技术选型文档，详细说明各个技术栈的选择理由、对比分析和最佳实践。

## 文档结构

```
Doc/Selection/
├── README.md                # 本文档（索引）
├── 00_overview.md           # 技术选型总览
├── 01_web_framework.md      # Web框架选型（FastAPI）
├── 02_database.md           # 数据库选型（SQLAlchemy）
├── 03_vector_db.md          # 向量数据库选型
├── 04_llm_embedding.md      # LLM和Embedding选型
├── 05_retrieval.md          # 检索策略选型
├── 06_auth_security.md      # 认证和授权选型（待补充）
├── 07_rag_framework.md      # RAG框架选型
├── 08_deployment.md         # 部署和运维选型（待补充）
└── 09_email_service.md      # 邮件服务选型（阿里云邮件推送）
```

## 快速导航

### 核心架构层

1. **[Web框架选型](./01_web_framework.md)** - FastAPI
   - 为什么选择FastAPI
   - 与其他框架对比
   - 性能和使用场景

2. **[数据库选型](./02_database.md)** - SQLAlchemy + MySQL + Redis
   - SQLAlchemy异步ORM
   - MySQL (生产) / SQLite (开发)
   - Redis缓存
   - 迁移工具（Alembic）

3. **[向量数据库选型](./03_vector_db.md)** - Chroma/Qdrant/Milvus/pgvector
   - 多方案对比
   - 默认选择Chroma
   - 适配器模式实现

### AI和检索层

4. **[LLM和Embedding选型](./04_llm_embedding.md)** - Qwen/DeepSeek + 本地模型
   - LLM提供商对比（Qwen、DeepSeek、本地模型）
   - Embedding模型选择（Qwen Embedding、本地BGE/Qwen）
   - 基于LangChain统一接口
   - 成本分析

5. **[检索策略选型](./05_retrieval.md)** - 混合检索
   - 向量检索 + BM25
   - RRF融合算法
   - 性能优化

6. **[RAG框架选型](./07_rag_framework.md)** - LangChain
   - Agent和RAG统一使用LangChain
   - 丰富的组件和集成
   - 实现示例

### 其他选型（待补充）

6. **认证和授权选型** - API Key + RBAC
7. **RAG框架选型** - LangChain/LlamaIndex
8. **部署和运维选型** - Docker/Kubernetes

## 技术栈总览

| 层级 | 技术选型 | 状态 |
|------|---------|------|
| **API层** | FastAPI + Pydantic + Uvicorn | ✅ 已确定 |
| **ORM层** | SQLAlchemy (异步) | ✅ 已确定 |
| **关系数据库** | MySQL (生产) / SQLite (开发) | ✅ 已确定 |
| **缓存数据库** | Redis | ✅ 已确定 |
| **向量数据库** | Chroma (默认) / Qdrant / Milvus / pgvector | ✅ 已确定 |
| **检索策略** | 混合检索（向量 + BM25） | ✅ 已确定 |
| **LLM** | Qwen/DeepSeek (主要) + 本地模型 | ✅ 已确定 |
| **Embedding** | Qwen Embedding (主要) + 本地模型 | ✅ 已确定 |
| **RAG框架** | LangChain | ✅ 已确定 |
| **Agent框架** | LangChain | ✅ 已确定 |
| **邮件服务** | 阿里云邮件推送 | ✅ 已确定 |
| **认证** | API Key | ✅ 已确定 |
| **授权** | RBAC | ✅ 已确定 |

## 选型原则

1. **性能优先**: 选择高性能、低延迟的技术方案
2. **可扩展性**: 支持水平扩展和模块化替换
3. **开发效率**: 提供良好的开发体验和文档
4. **社区支持**: 选择活跃的开源社区
5. **生产就绪**: 经过生产环境验证的成熟技术
6. **成本效益**: 平衡性能和成本

## 关键决策记录

### 1. FastAPI vs Flask/Django
- **决策**: 选择FastAPI
- **理由**: 异步支持、类型安全、自动文档
- **文档**: [01_web_framework.md](./01_web_framework.md)

### 2. SQLAlchemy vs Django ORM
- **决策**: 选择SQLAlchemy
- **理由**: 灵活性、异步支持、数据库无关
- **文档**: [02_database.md](./02_database.md)

### 3. MySQL vs PostgreSQL
- **决策**: 选择MySQL
- **理由**: 成熟稳定、生态完善、运维经验丰富
- **文档**: [02_database.md](./02_database.md)

### 4. Redis缓存
- **决策**: 使用Redis做缓存
- **理由**: 高性能、丰富数据结构、广泛应用
- **文档**: [02_database.md](./02_database.md)

### 5. Chroma vs Qdrant/Milvus
- **决策**: Chroma为默认，支持多方案
- **理由**: 易用性、快速开发、适配器模式
- **文档**: [03_vector_db.md](./03_vector_db.md)

### 6. 混合检索 vs 纯向量检索
- **决策**: 选择混合检索
- **理由**: 高召回率、高精确度、鲁棒性
- **文档**: [05_retrieval.md](./05_retrieval.md)

### 7. Qwen/DeepSeek vs OpenAI
- **决策**: Qwen/DeepSeek为主要选择，支持本地模型
- **理由**: 中文优化、成本低、数据合规、支持本地部署
- **文档**: [04_llm_embedding.md](./04_llm_embedding.md)

### 8. LangChain vs LlamaIndex
- **决策**: 选择LangChain
- **理由**: 统一框架（Agent和RAG）、丰富集成、活跃社区
- **文档**: [07_rag_framework.md](./07_rag_framework.md)

### 9. 邮件服务选型
- **决策**: 选择阿里云邮件推送
- **理由**: 国内服务稳定、有免费额度、数据合规、高送达率
- **文档**: [09_email_service.md](./09_email_service.md)

## 使用指南

### 查看特定技术选型
1. 从本文档找到对应的文档链接
2. 查看详细对比分析
3. 了解实现方式和最佳实践

### 评估新技术方案
1. 参考现有选型文档的对比框架
2. 进行POC验证
3. 更新选型文档

### 技术栈升级
1. 评估升级的必要性和风险
2. 进行兼容性测试
3. 更新相关文档

## 更新日志

- 2025-12-07: 创建技术选型文档结构
- 2025-12-07: 完成Web框架、数据库、向量数据库、LLM/Embedding、检索策略选型文档
- 2025-12-07: 更新数据库选型（MySQL + Redis）、LLM/Embedding选型（Qwen/DeepSeek + 本地模型）、RAG框架选型（LangChain）

## 相关文档

- [项目计划](../Plan/project_plan.md) - 项目整体计划
- [模块文档](../Modules/README.md) - 系统模块设计
- [API文档](../api/README.md) - API接口文档

