# 检索策略选型：混合检索

> 创建时间: 2025-12-07  
> 决策状态: ✅ 已确定

## 选型结果

**选择**: 混合检索（Hybrid Retrieval）  
**组成**: 向量检索 + BM25关键词检索  
**融合策略**: Reciprocal Rank Fusion (RRF)

## 混合检索方案

### 架构设计

```
用户查询
    │
    ├─→ 向量检索 (语义相似度)
    │   └─→ 向量数据库查询
    │
    ├─→ BM25检索 (关键词匹配)
    │   └─→ 倒排索引查询
    │
    └─→ 结果融合
        └─→ RRF融合算法
            └─→ 最终结果
```

### 1. 向量检索（语义相似度）

#### 原理
- 将查询文本转换为向量
- 在向量空间中计算余弦相似度
- 返回最相似的文档块

#### 特性
- **语义理解**: 理解同义词和语义关系
- **多语言**: 支持跨语言检索
- **上下文**: 理解上下文语义

#### 实现示例
```python
async def vector_search(
    query: str,
    top_k: int = 5,
    library_ids: list[UUID] | None = None
) -> list[RetrievedChunk]:
    # 1. 查询向量化
    query_embedding = await embedding_provider.embed([query])[0]
    
    # 2. 向量数据库检索
    results = await vector_db.search(
        query_vector=query_embedding,
        top_k=top_k * 2,  # 检索更多候选
        library_ids=library_ids
    )
    
    return results
```

### 2. BM25检索（关键词匹配）

#### 原理
- 基于TF-IDF的改进算法
- 考虑词频和逆文档频率
- 对精确关键词匹配效果好

#### 特性
- **精确匹配**: 对精确关键词匹配优秀
- **快速**: 基于倒排索引，查询快速
- **可解释**: 结果可解释性强

#### 实现示例
```python
from rank_bm25 import BM25Okapi

class BM25Retriever:
    def __init__(self, documents: list[str]):
        # 分词
        tokenized_docs = [self._tokenize(doc) for doc in documents]
        self.bm25 = BM25Okapi(tokenized_docs)
        self.documents = documents
    
    def search(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
        # 分词查询
        tokenized_query = self._tokenize(query)
        
        # BM25评分
        scores = self.bm25.get_scores(tokenized_query)
        
        # 排序并返回top_k
        top_indices = np.argsort(scores)[::-1][:top_k]
        return [
            RetrievedChunk(
                document_id=str(i),
                text=self.documents[i],
                score=scores[i],
                metadata={}
            )
            for i in top_indices
        ]
```

### 3. 结果融合（RRF）

#### Reciprocal Rank Fusion (RRF)

RRF是一种简单有效的融合算法：

```
RRF_score(doc) = Σ 1 / (k + rank_i(doc))

其中：
- k: 常数（通常为60）
- rank_i(doc): 文档在第i个检索结果中的排名
```

#### 优势
- ✅ **简单有效**: 算法简单，效果优秀
- ✅ **无参数**: 不需要训练参数
- ✅ **鲁棒性**: 对单个检索器失效有容错

#### 实现示例
```python
def reciprocal_rank_fusion(
    results_list: list[list[RetrievedChunk]],
    k: int = 60
) -> list[RetrievedChunk]:
    """融合多个检索结果"""
    doc_scores = {}
    
    # 计算每个文档的RRF分数
    for results in results_list:
        for rank, chunk in enumerate(results, 1):
            doc_id = chunk.document_id
            if doc_id not in doc_scores:
                doc_scores[doc_id] = {
                    'chunk': chunk,
                    'score': 0.0
                }
            doc_scores[doc_id]['score'] += 1 / (k + rank)
    
    # 按分数排序
    fused_results = sorted(
        doc_scores.values(),
        key=lambda x: x['score'],
        reverse=True
    )
    
    return [item['chunk'] for item in fused_results]
```

## 完整实现流程

```python
class HybridRetriever:
    def __init__(
        self,
        vector_db: VectorDB,
        bm25_retriever: BM25Retriever,
        embedding_provider: EmbeddingProvider
    ):
        self.vector_db = vector_db
        self.bm25_retriever = bm25_retriever
        self.embedding_provider = embedding_provider
    
    async def search(
        self,
        query: str,
        top_k: int = 5,
        library_ids: list[UUID] | None = None
    ) -> list[RetrievedChunk]:
        # 1. 并行执行两种检索
        vector_results, bm25_results = await asyncio.gather(
            self._vector_search(query, top_k * 2, library_ids),
            self._bm25_search(query, top_k * 2)
        )
        
        # 2. RRF融合
        fused_results = reciprocal_rank_fusion(
            [vector_results, bm25_results],
            k=60
        )
        
        # 3. 返回top_k
        return fused_results[:top_k]
```

## 性能优化策略

### 1. 缓存机制

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_embedding(text: str) -> list[float]:
    """缓存查询向量化结果"""
    return embedding_provider.embed([text])[0]
```

### 2. 异步并行

```python
# 并行执行向量检索和BM25检索
vector_task = asyncio.create_task(vector_search(query))
bm25_task = asyncio.create_task(bm25_search(query))
vector_results, bm25_results = await asyncio.gather(vector_task, bm25_task)
```

### 3. 早期终止

```python
# 如果向量检索结果足够好，可以跳过BM25
if vector_results[0].score > 0.9:
    return vector_results[:top_k]
```

## 性能表现

混合检索相比单一检索方法的优势：
- **召回率**: 提升约10-15%
- **精确度**: 提升约8-12%
- **鲁棒性**: 对单一方法失效有容错能力

## 最佳实践

1. **参数调优**: 根据数据特点调整RRF的k值
2. **权重调整**: 可以为不同检索器设置权重
3. **缓存策略**: 缓存常见查询的检索结果
4. **监控指标**: 监控检索质量和性能

## 总结

混合检索方案：
- ✅ **高召回率**: 结合两种检索方法的优势
- ✅ **高精确度**: RRF融合提升结果质量
- ✅ **鲁棒性**: 对单一方法失效有容错
- ✅ **可扩展**: 易于添加新的检索方法

## 参考资源

- [BM25算法](https://en.wikipedia.org/wiki/Okapi_BM25)
- [RRF论文](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf)
- [混合检索最佳实践](https://www.pinecone.io/learn/hybrid-search/)

