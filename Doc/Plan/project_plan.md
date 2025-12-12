# 工业问答后端项目计划

## 目标
- 提供面向工业场景的问答 API，支持多工具 Agent + RAG 流水线。
- 集成向量检索（Chroma/Qdrant 等）与 BM25 组合检索，提升召回与相关性。
- 通过可配置的提示与角色模板，满足运维/管理等不同用户画像。
- 提供文档摄取与反馈回流能力，闭环优化知识库质量。

## 架构概览
- 参考 `Doc/diagram/graph/graph.001.jpeg` 与 `graph.002.jpeg`：前端 → FastAPI 网关 → Agent 编排 → RAG → 存储。
- 代码对应关系：
  - API 层：`app/api/v1/*.py`，入口 `app/main.py`。
  - 依赖注入：`app/deps.py`，集中管理设置、DB 会话、检索器、流水线。
  - Agent 层：`app/agents/qa_agent.py` + `app/agents/tools.py`，负责意图分类、工具选择与调用。
  - RAG 层：`app/rag/`（ingestion/retriever/pipeline/prompts/evaluators）。
  - 数据与会话：`app/db/`（SQLAlchemy 异步栈），向量库默认 Chroma，可换 Qdrant/Milvus/pgvector。

## 近期里程碑
1) 最小可用版本（MVP）
   - 配置 `.env`，跑通 `uvicorn app.main:app --reload`。
   - 完成基础问答路由 `/ask`（`app/api/v1/qa.py`）联通 Agent + RAG 流。
   - 跑通 `pytest -q`，通过 smoke 测试。
2) 检索与摄取增强
   - 完成 `scripts/ingest_docs.py` 配置与样例数据导入。
   - 在 `app/rag/retriever.py` 启用 BM25 + 向量融合，评估召回质量。
   - 增加 rerank/过滤策略，记录评估数据到 `app/rag/evaluators.py`。
3) 生成与提示优化
   - 在 `app/rag/prompts.py` 添加多角色模板与上下文压缩策略。
   - 支持可切换的 LLM/Embedding 提供方（OpenAI / 本地 vLLM）。
4) 可靠性与安全
   - 接入 API-key 校验与基础审计（`app/core/security.py`）。
   - 增加日志与追踪（`app/core/logging.py`），对接监控出口（可选）。
   - 增加反馈存储与回流链路（DB + 向量库同步）。
5) 部署与运维
   - 容器化（Dockerfile/compose），定义健康检查。
   - CI: 格式/静态检查（ruff）+ 测试（pytest）。
   - 可选：灰度开关与配额控制。

## 依赖与环境
- Python ≥ 3.10；安装：`pip install -e .` 或 `pip install -r requirements.txt`。
- 复制 `env.example` 为 `.env`，填写数据库、向量库、LLM/Embedding 密钥。
- 本地开发：`uvicorn app.main:app --reload`。

## 风险与待决策
- 检索底座选择（Chroma vs Qdrant/Milvus/pgvector）需结合规模与运维成本。
- LLM/Embedding 供应商与费用控制策略。
- 多租户与访问控制需求范围（`admin` 路由的权限模型）。
- 评估体系：离线评估基准、在线反馈如何闭环优化。

## 后续行动（本周优先级）
- [ ] 落地 `.env`，启动本地 API。
- [ ] 跑通 ingest 脚本与样例文档，确认向量入库流程。
- [ ] 以 `tests/test_smoke.py` 为基线补充更多查询样例与断言。

