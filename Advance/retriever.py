from dataclasses import dataclass
from typing import Any, List, Optional, Dict

# 新增依赖
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from vectorDB.Chroma import chroma_db,embedding_model

@dataclass
class RetrievedChunk:
    document_id: str
    text: str
    score: float
    metadata: dict[str, Any]
    source_type: str = "hybrid"  # 标识来源：vector, bm25, or hybrid


def _weighted_reciprocal_rank(doc_lists: List[List[Document]], k=60) -> List[RetrievedChunk]:
    """
    RRF (倒数排名融合) 算法核心
    公式: Score = 1 / (k + rank)
    """
    fused_scores = {}
    doc_map = {}

    # 遍历每一路检索结果（Vector路, BM25路）
    for doc_list in doc_lists:
        for rank, doc in enumerate(doc_list):
            # 使用 page_content 作为临时唯一键 (最好是用 doc_id，但需确保 Chroma 和 BM25 id 一致)
            # 这里我们假设 metadata 里有 id，或者 fallback 到 content
            doc_id = doc.metadata.get("id") or doc.page_content[:50]  # 简化的 ID 获取

            if doc_id not in doc_map:
                doc_map[doc_id] = doc
                fused_scores[doc_id] = 0

            # 累加分数：排名越靠前(rank小)，分数越高
            fused_scores[doc_id] += 1 / (k + rank + 1)

    # 按分数降序排列
    sorted_ids = sorted(fused_scores.keys(), key=lambda x: fused_scores[x], reverse=True)

    # 转换为 RetrievedChunk
    final_chunks = []
    for doc_id in sorted_ids:
        doc = doc_map[doc_id]
        final_chunks.append(RetrievedChunk(
            document_id=str(doc.metadata.get("id", "unknown")),
            text=doc.page_content,
            score=fused_scores[doc_id],  # 这里是 RRF 分数
            metadata=doc.metadata
        ))

    return final_chunks


def _build_filters(plant_id: Optional[str] = None, filters: Optional[Dict] = None) -> Optional[Dict]:
    """构建 Chroma 过滤条件"""
    conditions = []
    if plant_id: conditions.append({"plant_id": plant_id})
    if filters and isinstance(filters, dict):
        for k, v in filters.items(): conditions.append({k: v})

    if not conditions:
        return None
    elif len(conditions) == 1:
        return conditions[0]
    else:
        return {"$and": conditions}


class HybridRetriever:
    """
    真正的混合检索器：Chroma (向量) + BM25 (关键词)
    使用 RRF (倒数排名融合) 合并结果。
    """

    def __init__(self):
        print("🔄 初始化混合检索器...")

        # 1. 初始化嵌入模型
        self.embedding_model = embedding_model

        # 2. 初始化 Chroma (持久化层)
        self.chroma_db = chroma_db

        # 3. 初始化 BM25 (内存层)
        # 注意：BM25 需要从 Chroma 中加载所有现存文档来构建索引
        self.bm25_retriever = None
        self._reload_bm25()

    def _reload_bm25(self):
        """从 Chroma 加载所有文档并重建 BM25 索引"""
        try:
            # 获取所有文档（注意：如果数据量巨大，这里需要优化，不能全量加载）
            # Chroma 的 get() 方法如果不传参，默认返回所有数据
            all_docs_data = self.chroma_db.get()

            if not all_docs_data['documents']:
                print("⚠️ Chroma 为空，跳过 BM25 初始化")
                self.bm25_retriever = None
                return

            # 重组为 Document 对象列表
            docs = []
            for i, text in enumerate(all_docs_data['documents']):
                meta = all_docs_data['metadatas'][i] if all_docs_data['metadatas'] else {}
                # 确保 id 存在
                doc_id = all_docs_data['ids'][i]
                meta['id'] = doc_id
                docs.append(Document(page_content=text, metadata=meta))

            # 构建 BM25 检索器
            self.bm25_retriever = BM25Retriever.from_documents(docs)
            # 设置 BM25 返回的数量与 search 保持一致或稍多
            self.bm25_retriever.k = 10
            print(f"✅ BM25 索引构建完成，共 {len(docs)} 条文档。")

        except Exception as e:
            print(f"❌ BM25 初始化失败: {e}")

    async def search(
            self,
            query: str,
            plant_id: Optional[str] = None,
            filters: Optional[Dict] = None,
            top_k: int = 5
    ) -> List[RetrievedChunk]:
        """执行混合检索"""

        # 1. 执行 向量检索 (Vector Search)
        chroma_filter = _build_filters(plant_id, filters)
        vector_docs = self.chroma_db.similarity_search(
            query=query, k=top_k, filter=chroma_filter
        )
        print(f"DEBUG: 向量检索找到 {len(vector_docs)} 条")

        # 2. 执行 BM25 检索 (Keyword Search)
        # 注意：简单的 BM25Retriever 不支持元数据过滤(filter)。
        # 如果必须要在 BM25 里也支持过滤，需要在内存中手动 filter，这里简化处理：
        # 先搜多一点，再人工过滤（Production 方案通常用 ElasticSearch 解决这个问题）
        bm25_docs = []
        if self.bm25_retriever:
            raw_bm25_docs = self.bm25_retriever.invoke(query)
            # 简单的后处理过滤 (Post-filtering)
            for doc in raw_bm25_docs:
                # 检查 plant_id
                if plant_id and doc.metadata.get("plant_id") != plant_id:
                    continue
                # 检查其他 filters
                if filters:
                    match = True
                    for k, v in filters.items():
                        if doc.metadata.get(k) != v:
                            match = False
                            break
                    if not match: continue

                bm25_docs.append(doc)

            # 截取前 top_k (因为后面要做融合，其实可以保留更多参与融合)
            bm25_docs = bm25_docs[:top_k]
            print(f"DEBUG: BM25 检索找到 {len(bm25_docs)} 条")

        # 3. RRF 融合 (Merge)
        # 将两路结果放入 RRF 算法
        merged_results = _weighted_reciprocal_rank([vector_docs, bm25_docs])

        # 4. 返回最终 Top K
        return merged_results[:top_k]

    def add_documents(self, texts: List[str], metadatas: List[Dict]) -> None:
        """插入数据并刷新索引"""
        try:
            # 1. 存入 Chroma
            self.chroma_db.add_texts(texts=texts, metadatas=metadatas)
            print(f"✅ Vector: 成功插入 {len(texts)} 条文档")

            # 2. 刷新 BM25 (简单粗暴版：重新读取)
            # 在生产环境中，应该只增量更新，但 rank_bm25 是静态的，所以得重载
            self._reload_bm25()

        except Exception as e:
            print(f"❌ 插入失败: {e}")