# 🏭 Industrial QA Backend

> 让工业知识库"活"起来！一个集成了 RAG 和智能 Agent 的工业问答后端系统。

## 🚀 快速开始

```bash
# 1. 安装依赖
uv sync

# 2. 配置环境变量
cp env.example .env
# 编辑 .env，填入你的 API 密钥和数据库连接

# 3. 初始化数据库
uv run python scripts/init_db.py

# 4. 启动服务
uvicorn app.main:app --reload
```

就这么简单！🎉

## ✨ 核心特性

- 🤖 **智能问答 Agent** - 基于 LangChain 的多工具 Agent，能理解意图、检索知识、生成答案
- 📚 **RAG 增强生成** - 结合向量检索和重排序，让 AI 回答更准确
- 📦 **文档库管理** - 支持个人库和群组库，灵活的知识组织方式
- 🔐 **JWT 认证** - 安全的用户认证和权限管理
- 🔍 **多格式文档支持** - PDF、DOCX、TXT、MD 等，自动提取文本和向量化
- ⚡ **异步高性能** - 全异步架构，支持高并发

## 🛠️ 技术栈

| 组件 | 技术选型 |
|------|---------|
| Web 框架 | FastAPI + Pydantic |
| 数据库 | MySQL (SQLAlchemy Async) |
| 向量库 | ChromaDB |
| 缓存 | Redis |
| RAG 框架 | LangChain |
| LLM 支持 | OpenAI / DashScope (Qwen) |

## 📁 项目结构

```
app/
├── api/v1/        # API 路由（认证、文档、问答）
├── core/          # 核心配置（安全、日志、设置）
├── rag/           # RAG 管道（检索、生成、向量化）
├── agents/        # 智能 Agent
└── db/            # 数据模型和会话管理

scripts/           # 工具脚本（初始化、迁移）
tests/             # 测试套件
```

## ⚙️ 环境配置

关键环境变量（详见 `env.example`）：

```bash
# 数据库
DATABASE_URL=mysql+aiomysql://user:pass@localhost:3306/dbname
REDIS_URL=redis://localhost:6379

# LLM 配置
LLM_PROVIDER=dashscope  # 或 openai
DASHSCOPE_API_KEY=your_key
OPENAI_API_KEY=your_key

# 向量库
VECTOR_DB_URI=chroma://./chroma_store
```

## 🎯 使用场景

1. **上传文档** → 系统自动提取文本并分块
2. **向量化文档** → 将文档转换为可检索的向量
3. **智能问答** → Agent 从知识库中检索相关信息并生成答案
4. **库管理** → 创建个人库或群组库，灵活组织知识

## 📖 文档

- [API 文档](achieved/api.md) - 完整的 API 接口说明
- [测试文档](tests/README.md) - 测试指南和用例
- [环境配置](env.example) - 环境变量说明

## 🧪 测试

```bash
# 初始化测试数据
uv run python tests/init_test_data.py

# 运行 API 测试
uv run python tests/test_api_endpoints.py
```

## 🎨 架构概览

```
前端请求
  ↓
FastAPI 网关
  ↓
Agent 编排层（意图识别、工具选择）
  ↓
RAG 管道（检索 → 重排序 → 生成）
  ↓
存储层（MySQL + ChromaDB + Redis）
```

## 🔧 开发建议

- 使用 `uv` 管理依赖（更快更可靠）
- 开发时启用 `--reload` 自动重载
- 查看 `achieved/` 目录了解已实现的功能
- 运行测试前确保数据库和 Redis 已启动

## 📝 下一步

- [ ] 接入更多 LLM 提供商（Moonshot、本地 vLLM）
- [ ] 优化检索策略（混合检索、重排序）
- [ ] 添加监控和评估工具
- [ ] 支持更多文档格式（Excel、PPT）

---

**让 AI 成为你的工业知识助手！** 🚀
