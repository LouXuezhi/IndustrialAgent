import time
from dataclasses import dataclass
from uuid import UUID

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import Runnable
from langchain_openai import ChatOpenAI

from app.core.config import Settings, get_settings
from app.rag.prompts import get_prompt
from app.rag.retriever import LangchainRetriever


@dataclass
class PipelineResult:
    answer: str
    references: list[dict]
    latency_ms: int


class RAGPipeline:
    """LangChain-based RAG pipeline with pluggable retriever."""

    def __init__(self, retriever: LangchainRetriever, settings: Settings | None = None) -> None:
        self.retriever = retriever
        self.settings = settings or get_settings()
        # Choose LLM client based on provider; support DashScope (OpenAI-compatible) and OpenAI.
        self._llm = None
        if self.settings.llm_provider == "dashscope" and (
            self.settings.dashscope_llm_api_key or self.settings.dashscope_api_key
        ):
            self._llm = ChatOpenAI(
                model=self.settings.llm_model,
                api_key=self.settings.dashscope_llm_api_key or self.settings.dashscope_api_key,
                temperature=0.2,
                base_url=self.settings.dashscope_llm_base_url or self.settings.dashscope_base_url,
            )
        elif self.settings.llm_provider == "openai" and self.settings.openai_api_key:
            self._llm = ChatOpenAI(
                model=self.settings.llm_model,
                api_key=self.settings.openai_api_key,
                temperature=0.2,
            )

    async def run(
        self,
        query: str,
        top_k: int = 5,
        library_ids: list[UUID] | None = None,
        role: str | None = None,
    ) -> PipelineResult:
        start = time.perf_counter()
        chunks = await self.retriever.search(query, top_k=top_k, library_ids=library_ids)
        
        if not chunks:
            # No chunks retrieved, return informative message
            answer = "抱歉，未找到相关文档内容。请确保：\n1. 文档已成功向量化\n2. 文档库ID正确\n3. 文档库中有相关内容"
        else:
            context = "\n\n".join(chunk.text for chunk in chunks)
            answer = await self._generate(context=context, question=query, role=role)

        latency_ms = int((time.perf_counter() - start) * 1000)
        references = [
            {"document_id": c.document_id, "score": c.score, "metadata": c.metadata} for c in chunks
        ]

        return PipelineResult(answer=answer, references=references, latency_ms=latency_ms)

    async def _generate(self, *, context: str, question: str, role: str | None) -> str:
        """Generate answer using LangChain LLM chain; fallback to demo."""
        if self._llm:
            try:
                prompt = ChatPromptTemplate.from_template(get_prompt(role=role))
                chain: Runnable = prompt | self._llm | StrOutputParser()
                return await chain.ainvoke({"context": context, "question": question})
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"LLM generation error: {e}")
                # Fallback to demo answer
                return f"基于以下文档内容：\n\n{context[:1000]}\n\n问题：{question}\n\n（注意：LLM 调用失败，这是基于检索内容的摘要）"
        # No LLM configured
        return f"基于以下文档内容：\n\n{context[:1000]}\n\n问题：{question}\n\n（注意：未配置 LLM，请检查环境变量中的 API 密钥）"

