Industrial QA Backend
======================

An opinionated FastAPI backend for industrial knowledge assistants that combine classical multi-tool agents with Retrieval-Augmented Generation (RAG). The structure follows the reference architecture:

Front-end → API → Agent orchestration → RAG stack → Storage

Quick Start
-----------

1. Install Python 3.10+ and create a virtual environment.
2. `pip install -e .` (or `pip install -r requirements.txt` if you prefer `requirements` files).
3. Copy `env.example` to `.env` and fill in secrets.
4. `uvicorn app.main:app --reload`.

Key Technologies
----------------

- FastAPI + Pydantic for the API surface and dependency injection.
- SQLAlchemy async stack for the operational database (documents, users, feedback).
- Chroma for the default vector store; adapters provided for Qdrant / Milvus / pgvector.
- LangChain + LlamaIndex ready abstractions inside `app/rag`.
- Tool-enabled Agent layer orchestrating intent classification, retrieval, reranking, and generation with either hosted or self-hosted LLMs.

Project Layout
--------------

```
industrial-qa-backend/
  app/
    main.py          # FastAPI entrypoint
    deps.py          # dependency injection helpers
    api/v1/*.py      # versioned routers
    core/*.py        # config, logging, security
    rag/*.py         # retrieval + generation pipeline
    agents/*.py      # QA agent + tools
    db/*.py          # SQLAlchemy models/session
  scripts/           # CLI helpers (ingestion, maintenance)
  tests/             # pytest suite
```

Architecture Diagram (Logical)
------------------------------

```
Frontend
  │
  ▼
FastAPI Gateway (app/api)
  │
  ▼
Agent Orchestrator (app/agents)
  │
  ▼
RAG Layer (retriever → reranker → prompt builder → LLM)
  │
  ▼
Storage
  ├─ Vector DB (Chroma / Qdrant / Milvus / pgvector)
  ├─ Object Storage (raw PDFs, Office docs)
  └─ Relational DB (metadata, feedback, audit)
```

Scripts
-------

- `scripts/ingest_docs.py` – parses source documents, chunks them, and writes vectors + metadata.

Testing
-------

Run the smoke tests with:

```
pytest -q
```

Next Steps
----------

- Plug in real LLM + embedding providers (OpenAI, Moonshot, DashScope, local vLLM).
- Replace the baseline BM25 + cosine retriever with production-ready services (pgvector, Milvus, etc.).
- Add tenancy-aware auth, monitoring, and offline evaluators in `app/rag/evaluators.py`.

Framework Logic Walkthrough
---------------------------

1. **API Surface (`app/api`)** – FastAPI routers expose `/ask`, `/docs`, `/admin`. Every request passes through CORS + API-key guards defined in `app/core`.
2. **Dependency Layer (`app/deps`)** – centralizes lifecycle-managed dependencies (settings, DB session, retriever, pipeline) so they can be injected anywhere.
3. **Agent Layer (`app/agents`)** – `QAAgent` orchestrates retrieval + generation, and `tools.py` is the registry for domain tools (knowledge base search, calculator, ticketing, etc.).
4. **RAG Layer (`app/rag`)** – contains ingestion, retriever, prompts, pipeline, and evaluators. Retrieval merges vector + BM25, prompts adapt to operator/maintenance/manager personas, and `pipeline.py` sequences retrieval → rerank → prompt → LLM.
5. **Storage (`app/db` + Vector Store)** – SQLAlchemy models store metadata, users, and feedback while the vector database (Chroma by default) holds embeddings. `scripts/ingest_docs.py` keeps the two in sync.
6. **Operations** – `tests/` houses pytest smoke checks, `scripts/` contains CLI helpers, and the root `pyproject.toml` plus `env.example` define the runtime contract.

This layered flow mirrors the logical diagram: front-end calls the API layer, which delegates to the agent for tool + intent orchestration, which invokes the RAG pipeline, which in turn talks to the storage substrates.

