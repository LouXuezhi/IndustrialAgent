import types

import pytest

from app.core.config import Settings
from app.rag import ingestion
from app.rag.pipeline import RAGPipeline
from app.rag.retriever import LangchainRetriever


class StubEmbeddingFn:
    def __init__(self, *, api_key: str, model_name: str, api_base: str | None):
        self.api_key = api_key
        self.model_name = model_name
        self.api_base = api_base


class StubLLM:
    def __init__(self, *, model: str, api_key: str, base_url: str | None, temperature: float):
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.temperature = temperature

    async def ainvoke(self, *_args, **_kwargs):
        return "ok"


def test_build_embedding_fn_prefers_dashscope_embedding_key(monkeypatch):
    captured = {}

    def fake_openai_embedding_function(*, api_key, model_name, api_base=None):
        captured.update({"api_key": api_key, "model_name": model_name, "api_base": api_base})
        return StubEmbeddingFn(api_key=api_key, model_name=model_name, api_base=api_base)

    monkeypatch.setattr(ingestion.embedding_functions, "OpenAIEmbeddingFunction", fake_openai_embedding_function)

    settings = Settings(
        llm_provider="dashscope",
        embedding_model="text-embedding-v4",
        dashscope_embedding_api_key="emb-key",
        dashscope_api_key="legacy-key",
        dashscope_embedding_base_url="https://emb-base",
        dashscope_base_url="https://legacy-base",
    )

    fn = ingestion._build_embedding_fn(settings)
    assert isinstance(fn, StubEmbeddingFn)
    assert captured["api_key"] == "emb-key"
    assert captured["api_base"] == "https://emb-base"
    assert captured["model_name"] == "text-embedding-v4"


def test_build_embedding_fn_openai_fallback(monkeypatch):
    captured = {}

    def fake_openai_embedding_function(*, api_key, model_name, api_base=None):
        captured.update({"api_key": api_key, "model_name": model_name, "api_base": api_base})
        return StubEmbeddingFn(api_key=api_key, model_name=model_name, api_base=api_base)

    monkeypatch.setattr(ingestion.embedding_functions, "OpenAIEmbeddingFunction", fake_openai_embedding_function)

    settings = Settings(
        llm_provider="openai",
        embedding_model="text-embedding-3-small",
        openai_api_key="ok-key",
    )

    fn = ingestion._build_embedding_fn(settings)
    assert isinstance(fn, StubEmbeddingFn)
    assert captured["api_key"] == "ok-key"
    assert captured["api_base"] is None
    assert captured["model_name"] == "text-embedding-3-small"


def test_pipeline_llm_dashscope(monkeypatch):
    captured = {}

    def fake_chat_openai(*, model, api_key, temperature, base_url=None):
        captured.update({"model": model, "api_key": api_key, "base_url": base_url, "temperature": temperature})
        return StubLLM(model=model, api_key=api_key, base_url=base_url, temperature=temperature)

    # Patch ChatOpenAI where it is imported
    monkeypatch.setattr("app.rag.pipeline.ChatOpenAI", fake_chat_openai)

    settings = Settings(
        llm_provider="dashscope",
        llm_model="qwen-plus",
        dashscope_llm_api_key="llm-key",
        dashscope_llm_base_url="https://llm-base",
    )

    # retriever is not used in init; pass a dummy
    retriever = types.SimpleNamespace()
    pipeline = RAGPipeline(retriever=retriever, settings=settings)

    assert pipeline._llm is not None
    assert captured["api_key"] == "llm-key"
    assert captured["base_url"] == "https://llm-base"
    assert captured["model"] == "qwen-plus"


def test_pipeline_llm_openai(monkeypatch):
    captured = {}

    def fake_chat_openai(*, model, api_key, temperature, base_url=None):
        captured.update({"model": model, "api_key": api_key, "base_url": base_url, "temperature": temperature})
        return StubLLM(model=model, api_key=api_key, base_url=base_url, temperature=temperature)

    monkeypatch.setattr("app.rag.pipeline.ChatOpenAI", fake_chat_openai)

    settings = Settings(
        llm_provider="openai",
        llm_model="gpt-4o-mini",
        openai_api_key="ok-key",
    )

    retriever = types.SimpleNamespace()
    pipeline = RAGPipeline(retriever=retriever, settings=settings)

    assert pipeline._llm is not None
    assert captured["api_key"] == "ok-key"
    assert captured["base_url"] is None
    assert captured["model"] == "gpt-4o-mini"

