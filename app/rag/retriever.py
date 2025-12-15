from dataclasses import dataclass
from typing import Any
from uuid import UUID
import asyncio
import logging

from langchain_community.vectorstores import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from chromadb.utils import embedding_functions
import chromadb
import numpy as np

from app.core.config import get_settings, Settings
from app.rag.ingestion import _resolve_chroma_path
from app.rag.reranker import Reranker
from app.rag.synonyms import QueryExpander, SynonymDict

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    document_id: str
    text: str
    score: float
    metadata: dict[str, Any]
    source_type: str = "vector"  # "vector", "bm25", or "hybrid"


def _build_embedding_fn(settings: Settings):
    # Prefer configured embedding provider; fallback to default.
    if settings.llm_provider == "dashscope" and (
        settings.dashscope_embedding_api_key or settings.dashscope_api_key
    ):
        # DashScope provides an OpenAI-compatible endpoint; use api_base to direct traffic.
        return embedding_functions.OpenAIEmbeddingFunction(
            api_key=settings.dashscope_embedding_api_key or settings.dashscope_api_key,
            model_name=settings.embedding_model,
            api_base=settings.dashscope_embedding_base_url or settings.dashscope_base_url,
        )
    if settings.llm_provider == "openai" and settings.openai_api_key:
        return embedding_functions.OpenAIEmbeddingFunction(
            api_key=settings.openai_api_key,
            model_name=settings.embedding_model,
        )
    return embedding_functions.DefaultEmbeddingFunction()


class LangchainRetriever:
    """LangChain-based Chroma retriever with library scoping."""

    def __init__(self, vector_uri: str, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.chroma_path = _resolve_chroma_path(vector_uri)
        self.embedding_fn = _build_embedding_fn(self.settings)

    def _collection_name(self, library_id: UUID | None) -> str:
        return f"library_{library_id}" if library_id else "library_default"

    def _get_vectorstore(self, library_id: UUID | None) -> Chroma:
        return Chroma(
            collection_name=self._collection_name(library_id),
            embedding_function=self.embedding_fn,
            persist_directory=self.chroma_path,
        )
    
    def _get_chroma_collection(self, library_id: UUID | None):
        """Get ChromaDB collection directly (bypassing LangChain).
        
        Uses the collection's existing embedding function if available,
        otherwise uses the configured embedding function.
        
        Returns None if collection doesn't exist and cannot be created.
        """
        import chromadb.errors
        client = chromadb.PersistentClient(path=self.chroma_path)
        collection_name = self._collection_name(library_id)
        try:
            # Try to get existing collection (will use its original embedding function)
            collection = client.get_collection(name=collection_name)
            # If collection exists, it will use its original embedding function
            # We need to ensure we use the same one for queries
            return collection
        except chromadb.errors.NotFoundError:
            # Collection doesn't exist - return None instead of creating
            # Collections should be created during document vectorization
            logger.debug(f"Collection {collection_name} does not exist (library_id: {library_id})")
            return None
        except Exception as e:
            logger.error(f"Error getting ChromaDB collection {collection_name}: {e}", exc_info=True)
            return None

    async def search(
        self,
        query: str,
        top_k: int = 5,
        library_ids: list[UUID] | None = None
    ) -> list[RetrievedChunk]:
        library_ids_to_search = library_ids if library_ids else [None]
        results: list[RetrievedChunk] = []

        async def _search_collection(lib_id: UUID | None):
            try:
                import logging
                logger = logging.getLogger(__name__)
                logger.debug(f"Searching collection for library_id: {lib_id}")
                
                # Use ChromaDB directly to avoid LangChain embedding format issues
                collection = self._get_chroma_collection(lib_id)
                
                # Query using ChromaDB's native API
                query_results = await asyncio.to_thread(
                    collection.query,
                    query_texts=[query],
                    n_results=top_k
                )
                
                if not query_results or not query_results.get('ids') or not query_results['ids'][0]:
                    logger.warning(f"No documents found in collection for library_id: {lib_id}")
                    return
                
                # Extract results
                ids = query_results['ids'][0]
                documents = query_results['documents'][0]
                metadatas = query_results['metadatas'][0] if query_results.get('metadatas') else [{}] * len(ids)
                distances = query_results['distances'][0] if query_results.get('distances') else [0.0] * len(ids)
                
                logger.debug(f"Found {len(ids)} documents in collection for library_id: {lib_id}")
                
                for i, (doc_id, doc_text, meta, distance) in enumerate(zip(ids, documents, metadatas, distances)):
                    # Convert distance to similarity (lower distance = higher similarity)
                    similarity = 1.0 / (1.0 + abs(distance)) if distance != 0 else 1.0
                    
                    results.append(
            RetrievedChunk(
                            document_id=str(meta.get("document_id", doc_id)),
                            text=doc_text,
                            score=similarity,
                            metadata=meta,
                        )
                    )
            except Exception as e:
                # Log error but continue to allow partial results from other stores
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error searching vector store for library_id {lib_id}: {e}", exc_info=True)
                return

        await asyncio.gather(*[_search_collection(lib_id) for lib_id in library_ids_to_search])
        
        if not results:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"No results found for query: {query}, library_ids: {library_ids}")
            return []
        
        # Sort by similarity (descending)
        results.sort(key=lambda c: c.score, reverse=True)
        return results[:top_k]


def _weighted_reciprocal_rank(
    vector_results: list[RetrievedChunk],
    bm25_results: list[RetrievedChunk],
    k: int = 60
) -> list[RetrievedChunk]:
    """
    RRF (倒数排名融合) 算法核心
    公式: Score = 1 / (k + rank)
    
    Args:
        vector_results: 向量检索结果
        bm25_results: BM25 检索结果
        k: RRF 常数，默认 60（常见值）
    
    Returns:
        融合后的检索结果，按 RRF 分数降序排列
    """
    fused_scores: dict[str, float] = {}
    chunk_map: dict[str, RetrievedChunk] = {}
    
    # 处理向量检索结果
    for rank, chunk in enumerate(vector_results):
        # 使用 document_id + text 的前50字符作为唯一键（避免重复）
        chunk_key = f"{chunk.document_id}:{chunk.text[:50]}"
        
        if chunk_key not in chunk_map:
            chunk_map[chunk_key] = chunk
            fused_scores[chunk_key] = 0.0
        
        # RRF 分数累加：排名越靠前(rank小)，分数越高
        fused_scores[chunk_key] += 1.0 / (k + rank + 1)
    
    # 处理 BM25 检索结果
    for rank, chunk in enumerate(bm25_results):
        chunk_key = f"{chunk.document_id}:{chunk.text[:50]}"
        
        if chunk_key not in chunk_map:
            chunk_map[chunk_key] = chunk
            fused_scores[chunk_key] = 0.0
        
        # RRF 分数累加
        fused_scores[chunk_key] += 1.0 / (k + rank + 1)
    
    # 按 RRF 分数降序排列
    sorted_keys = sorted(fused_scores.keys(), key=lambda x: fused_scores[x], reverse=True)
    
    # 转换为最终的 RetrievedChunk 列表
    final_chunks = []
    for chunk_key in sorted_keys:
        chunk = chunk_map[chunk_key]
        # 更新分数为 RRF 融合分数，标记来源为混合
        final_chunk = RetrievedChunk(
            document_id=chunk.document_id,
            text=chunk.text,
            score=fused_scores[chunk_key],
            metadata=chunk.metadata,
            source_type="hybrid"
        )
        final_chunks.append(final_chunk)
    
    return final_chunks


class HybridRetriever(LangchainRetriever):
    """
    混合检索器：结合向量检索（ChromaDB）和关键词检索（BM25）
    使用 RRF（倒数排名融合）算法合并结果，提升检索质量。
    
    支持 BM25 索引的增量更新：
    - 跟踪每个库的文档变更（添加/删除/更新）
    - 延迟重建：仅在检索时检查是否需要重建
    - 智能重建：只重建有变更的库的索引
    """
    
    def __init__(self, vector_uri: str, settings: Settings | None = None, enable_rerank: bool = True) -> None:
        super().__init__(vector_uri, settings)
        # BM25 检索器缓存：{library_id: BM25Retriever}
        self._bm25_retrievers: dict[str | None, BM25Retriever | None] = {}
        # 文档变更跟踪：{library_id: set(chunk_ids)} - 记录已变更的文档ID
        self._dirty_libraries: dict[str | None, set[str]] = {}
        # 文档计数缓存：{library_id: count} - 用于检测文档数量变化
        self._document_counts: dict[str | None, int] = {}
        # 重排序器
        self.reranker = Reranker(
            enable=enable_rerank,
            enable_cache=settings.rerank_cache_enable
        )
        # 查询扩展器
        self.settings = settings or get_settings()
        synonym_dict_path = self.settings.synonym_dict_path if self.settings.synonym_dict_path else None
        synonym_dict = SynonymDict(dict_path=synonym_dict_path) if synonym_dict_path else None
        enable_expansion = self.settings.enable_query_expansion if self.settings else True
        self.query_expander = QueryExpander(
            synonym_dict=synonym_dict,
            enable=enable_expansion
        )
        logger.info("🔄 初始化混合检索器（向量 + BM25 + 重排序 + 查询扩展，支持增量更新）")
    
    def _reload_bm25_index(self, library_id: UUID | None, force: bool = False) -> BM25Retriever | None:
        """
        从 ChromaDB 加载指定库的所有文档并构建 BM25 索引。
        
        Args:
            library_id: 文档库ID，None 表示默认库
            force: 是否强制重建（忽略变更检测）
        
        Returns:
            BM25Retriever 实例，如果库为空或出错则返回 None
        """
        try:
            collection = self._get_chroma_collection(library_id)
            
            # Collection doesn't exist - cannot build BM25 index
            if collection is None:
                logger.debug(f"Collection for library {library_id} does not exist, skipping BM25 index build")
                lib_key = str(library_id) if library_id else None
                self._bm25_retrievers[lib_key] = None
                return None
            
            # 获取所有文档
            all_docs_data = collection.get()
            
            if not all_docs_data.get('documents') or not all_docs_data['documents']:
                logger.debug(f"Library {library_id} 为空，跳过 BM25 索引构建")
                return None
            
            # 检查是否需要重建（通过文档数量变化）
            lib_key = str(library_id) if library_id else None
            current_count = len(all_docs_data['documents'])
            cached_count = self._document_counts.get(lib_key, 0)
            
            # 如果文档数量没变且不是强制重建，且没有标记为脏数据，尝试复用现有索引
            if not force and current_count == cached_count and lib_key not in self._dirty_libraries:
                existing_retriever = self._bm25_retrievers.get(lib_key)
                if existing_retriever is not None:
                    logger.debug(f"Library {library_id} 索引未变更，复用现有索引")
                    return existing_retriever
            
            # 需要重建索引
            logger.info(f"🔄 重建 BM25 索引 (library_id: {library_id}), 文档数: {cached_count} → {current_count}")
            
            # 重组为 LangChain Document 对象列表
            docs = []
            documents = all_docs_data['documents']
            metadatas = all_docs_data.get('metadatas', [{}] * len(documents))
            ids = all_docs_data.get('ids', [])
            
            for i, text in enumerate(documents):
                meta = metadatas[i] if i < len(metadatas) else {}
                # 确保 id 存在
                doc_id = ids[i] if i < len(ids) else f"doc_{i}"
                meta['id'] = doc_id
                docs.append(Document(page_content=text, metadata=meta))
            
            # 构建 BM25 检索器
            bm25_retriever = BM25Retriever.from_documents(docs)
            # 设置返回数量（稍大于 top_k，以便后续融合时有更多候选）
            bm25_retriever.k = 20
            
            # 更新缓存
            self._document_counts[lib_key] = current_count
            # 清除脏数据标记
            if lib_key in self._dirty_libraries:
                del self._dirty_libraries[lib_key]
            
            logger.info(f"✅ BM25 索引构建完成 (library_id: {library_id}), 共 {len(docs)} 条文档")
            return bm25_retriever
            
        except Exception as e:
            logger.error(f"❌ BM25 索引构建失败 (library_id: {library_id}): {e}", exc_info=True)
            return None
    
    def _get_bm25_retriever(self, library_id: UUID | None, force_rebuild: bool = False) -> BM25Retriever | None:
        """
        获取指定库的 BM25 检索器，如果不存在或需要更新则构建。
        
        Args:
            library_id: 文档库ID
            force_rebuild: 是否强制重建索引
        
        Returns:
            BM25Retriever 实例，如果失败则返回 None
        """
        lib_key = str(library_id) if library_id else None
        
        # 检查是否需要重建
        needs_rebuild = (
            force_rebuild or
            lib_key not in self._bm25_retrievers or
            self._bm25_retrievers[lib_key] is None or
            lib_key in self._dirty_libraries
        )
        
        if needs_rebuild:
            # 重建索引（会自动检测文档数量变化）
            bm25_retriever = self._reload_bm25_index(library_id, force=force_rebuild)
            self._bm25_retrievers[lib_key] = bm25_retriever
            return bm25_retriever
        else:
            # 复用现有索引
            return self._bm25_retrievers[lib_key]
    
    async def _vector_search(
        self,
        query: str,
        library_id: UUID | None,
        top_k: int
    ) -> list[RetrievedChunk]:
        """执行向量检索（复用父类逻辑）"""
        results: list[RetrievedChunk] = []
        
        try:
            collection = self._get_chroma_collection(library_id)
            
            # Collection doesn't exist - return empty results
            if collection is None:
                logger.debug(f"Collection for library {library_id} does not exist, returning empty results")
                return results
            
            query_results = await asyncio.to_thread(
                collection.query,
                query_texts=[query],
                n_results=top_k
            )
            
            if not query_results or not query_results.get('ids') or not query_results['ids'][0]:
                return results
            
            ids = query_results['ids'][0]
            documents = query_results['documents'][0]
            metadatas = query_results['metadatas'][0] if query_results.get('metadatas') else [{}] * len(ids)
            distances = query_results['distances'][0] if query_results.get('distances') else [0.0] * len(ids)
            
            for doc_id, doc_text, meta, distance in zip(ids, documents, metadatas, distances):
                similarity = 1.0 / (1.0 + abs(distance)) if distance != 0 else 1.0
                results.append(
                    RetrievedChunk(
                        document_id=str(meta.get("document_id", doc_id)),
                        text=doc_text,
                        score=similarity,
                        metadata=meta,
                        source_type="vector"
                    )
                )
        except Exception as e:
            logger.error(f"向量检索失败 (library_id: {library_id}): {e}", exc_info=True)
        
        return results
    
    async def _bm25_search(
        self,
        query: str,
        library_id: UUID | None,
        top_k: int
    ) -> list[RetrievedChunk]:
        """执行 BM25 关键词检索"""
        results: list[RetrievedChunk] = []
        
        try:
            # 检查是否需要重建（如果有脏数据标记）
            lib_key = str(library_id) if library_id else None
            force_rebuild = lib_key in self._dirty_libraries
            
            bm25_retriever = self._get_bm25_retriever(library_id, force_rebuild=force_rebuild)
            if not bm25_retriever:
                return results
            
            # 执行 BM25 检索（同步调用，使用 asyncio.to_thread）
            bm25_docs = await asyncio.to_thread(bm25_retriever.invoke, query)
            
            # 转换为 RetrievedChunk
            for doc in bm25_docs[:top_k]:
                results.append(
                    RetrievedChunk(
                        document_id=str(doc.metadata.get("document_id", doc.metadata.get("id", "unknown"))),
                        text=doc.page_content,
                        score=1.0,  # BM25 分数在 RRF 中通过排名体现
                        metadata=doc.metadata,
                        source_type="bm25"
                    )
                )
        except Exception as e:
            logger.error(f"BM25 检索失败 (library_id: {library_id}): {e}", exc_info=True)
        
        return results
    
    async def search(
        self,
        query: str,
        top_k: int = 5,
        library_ids: list[UUID] | None = None,
        use_hybrid: bool = True
    ) -> list[RetrievedChunk]:
        """
        执行混合检索（向量 + BM25）或纯向量检索。
        
        Args:
            query: 查询文本
            top_k: 返回结果数量
            library_ids: 要搜索的文档库ID列表，None 表示搜索所有库
            use_hybrid: 是否使用混合检索（默认 True），False 则仅使用向量检索
        
        Returns:
            检索结果列表，按 RRF 分数降序排列
        """
        library_ids_to_search = library_ids if library_ids else [None]
        all_results: list[RetrievedChunk] = []
        
        # 查询扩展（如果启用）
        expanded_query = await self.query_expander.expand_async(
            query,
            use_llm=self.settings.use_llm_expansion if hasattr(self, 'settings') and self.settings else False
        )
        if expanded_query != query:
            logger.debug(f"查询扩展: '{query}' → '{expanded_query}'")
            query = expanded_query  # 使用扩展后的查询
        
        # 对每个库执行检索
        for lib_id in library_ids_to_search:
            if use_hybrid:
                # 混合检索：并行执行向量检索和 BM25 检索
                vector_results, bm25_results = await asyncio.gather(
                    self._vector_search(query, lib_id, top_k),
                    self._bm25_search(query, lib_id, top_k)
                )
                
                logger.debug(
                    f"Library {lib_id}: 向量检索 {len(vector_results)} 条, "
                    f"BM25 检索 {len(bm25_results)} 条"
                )
                
                # RRF 融合
                if vector_results or bm25_results:
                    merged = _weighted_reciprocal_rank(vector_results, bm25_results)
                    all_results.extend(merged)
            else:
                # 仅向量检索（回退到父类行为）
                vector_results = await self._vector_search(query, lib_id, top_k)
                all_results.extend(vector_results)
        
        if not all_results:
            logger.warning(f"未找到任何结果: query={query}, library_ids={library_ids}")
            return []
        
        # 去重并排序（按 RRF 分数或相似度分数）
        # 使用 document_id + text 前50字符作为去重键
        seen = set()
        unique_results = []
        for chunk in all_results:
            chunk_key = f"{chunk.document_id}:{chunk.text[:50]}"
            if chunk_key not in seen:
                seen.add(chunk_key)
                unique_results.append(chunk)
        
        # 按分数降序排列
        unique_results.sort(key=lambda c: c.score, reverse=True)
        
        # 重排序：使用 Cross-Encoder 对筛选后的候选结果重新排序
        # 这样可以先通过 RRF 融合筛选出候选，再用重排序精排
        if self.reranker.is_enabled() and len(unique_results) > 1:
            # 计算重排序候选数量
            # 如果配置了固定数量，使用配置值；否则使用 top_k + 3（适度减少）
            if self.settings.rerank_candidate_count > 0:
                candidate_count = min(self.settings.rerank_candidate_count, len(unique_results))
            else:
                # 默认使用 top_k + 3，比原来的 top_k * 2 更少，提升速度
                candidate_count = min(top_k + 3, len(unique_results))
            
            rerank_candidates = unique_results[:candidate_count]
            # 使用异步重排序（支持缓存）
            reranked = await self.reranker.rerank_async(query, rerank_candidates, top_k=top_k)
            logger.debug(
                f"重排序: {len(rerank_candidates)} 条候选 → {len(reranked)} 条结果"
            )
            return reranked
        
        return unique_results[:top_k]
    
    def invalidate_bm25_cache(self, library_id: UUID | None = None, chunk_ids: list[str] | None = None):
        """
        标记指定库的 BM25 索引需要更新（增量更新标记）。
        在文档添加/更新/删除后调用此方法。
        
        Args:
            library_id: 文档库ID，None 表示标记所有库
            chunk_ids: 变更的 chunk ID 列表（可选，用于细粒度跟踪）
        """
        if library_id is None:
            # 标记所有库为脏数据
            self._dirty_libraries.clear()
            # 清除所有缓存（下次检索时会重建）
            for lib_key in list(self._bm25_retrievers.keys()):
                self._dirty_libraries[lib_key] = set()
            logger.info("已标记所有 BM25 索引需要更新")
        else:
            lib_key = str(library_id)
            # 标记为脏数据（不立即删除，延迟到下次检索时重建）
            if lib_key not in self._dirty_libraries:
                self._dirty_libraries[lib_key] = set()
            if chunk_ids:
                self._dirty_libraries[lib_key].update(chunk_ids)
            logger.debug(f"已标记 library {library_id} 的 BM25 索引需要更新 (变更 chunk 数: {len(chunk_ids) if chunk_ids else 'unknown'})")
    
    def force_rebuild_bm25_index(self, library_id: UUID | None = None):
        """
        强制重建指定库的 BM25 索引（立即重建，不延迟）。
        适用于需要立即更新索引的场景。
        
        Args:
            library_id: 文档库ID，None 表示重建所有库
        """
        if library_id is None:
            # 重建所有库
            for lib_key in list(self._bm25_retrievers.keys()):
                lib_id = UUID(lib_key) if lib_key else None
                self._reload_bm25_index(lib_id, force=True)
            logger.info("已强制重建所有 BM25 索引")
        else:
            lib_key = str(library_id)
            # 强制重建指定库
            bm25_retriever = self._reload_bm25_index(library_id, force=True)
            self._bm25_retrievers[lib_key] = bm25_retriever
            # 清除脏数据标记
            if lib_key in self._dirty_libraries:
                del self._dirty_libraries[lib_key]
            logger.info(f"已强制重建 library {library_id} 的 BM25 索引")

