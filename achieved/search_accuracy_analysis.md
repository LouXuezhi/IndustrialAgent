# 文档搜索不准确问题分析

## 当前实现的问题

### 1. 使用简单的字符串匹配

**当前代码**（`app/api/v1/docs.py:897-910`）：
```python
# Search in title
score = 0.0
if query_lower in doc.title.lower():
    score += 2.0  # Title match has higher weight

# Search in chunks content
for chunk in chunks:
    if query_lower in chunk.content.lower():
        score += 1.0
        break
```

**问题**：
- ❌ 使用简单的 `in` 操作符，无法处理：
  - 部分匹配（如查询"设备维护"匹配"设备维护方法"）
  - 词序无关（如"维护设备"无法匹配"设备维护"）
  - 同义词（如"装置"无法匹配"设备"）
  - 词形变化（如"维护"无法匹配"维护中"）

### 2. 评分系统过于简单

**问题**：
- ❌ 只有两种分数：标题匹配（2.0）和内容匹配（1.0）
- ❌ 没有考虑：
  - 匹配次数（多次出现应该得分更高）
  - 匹配位置（标题开头比中间更重要）
  - 匹配长度（完全匹配比部分匹配更重要）
  - 文档相关性（向量相似度）

### 3. 没有使用向量检索

**问题**：
- ❌ 只使用数据库查询，没有利用已向量化的文档
- ❌ 无法进行语义搜索（理解同义词、相关概念）
- ❌ 无法处理查询意图（如"如何维护"vs"维护方法"）

### 4. 没有使用 BM25 关键词检索

**问题**：
- ❌ 没有利用 BM25 算法进行关键词匹配
- ❌ 无法处理：
  - TF-IDF 权重（常见词权重低，专业词权重高）
  - 词频统计（出现次数多的文档更相关）

### 5. 没有查询扩展

**问题**：
- ❌ 没有使用同义词库扩展查询
- ❌ 无法匹配相关词汇（如"设备"无法匹配"装置"）

### 6. 性能问题

**问题**：
- ❌ 加载所有文档到内存（`all_docs = result.scalars().all()`）
- ❌ 对每个文档查询所有 chunks（N+1 查询问题）
- ❌ 没有索引优化

## 具体不准确的场景

### 场景 1: 部分匹配失败

```
查询: "设备维护"
文档标题: "设备维护方法指南"
结果: ✅ 能匹配（因为 "设备维护" in "设备维护方法指南"）

查询: "维护设备"
文档标题: "设备维护方法指南"
结果: ❌ 无法匹配（因为 "维护设备" not in "设备维护方法指南"）
```

### 场景 2: 同义词无法匹配

```
查询: "装置保养"
文档内容: "设备维护..."
结果: ❌ 无法匹配（"装置" ≠ "设备"，"保养" ≠ "维护"）
```

### 场景 3: 评分不合理

```
文档A: 标题包含查询（2分），内容包含1次（1分）→ 总分3分
文档B: 标题不包含，但内容包含10次（1分）→ 总分1分

结果: 文档A排在前面，但文档B可能更相关
```

### 场景 4: 语义理解缺失

```
查询: "如何检查设备故障"
文档内容: "设备故障检测方法..."
结果: ❌ 可能无法匹配（"检查" ≠ "检测"）
```

## 改进方案

### 方案 1: 使用向量检索（推荐）

**优势**：
- ✅ 支持语义搜索
- ✅ 理解同义词和相关概念
- ✅ 已有基础设施（ChromaDB + 向量化）

**实现**：
```python
# 使用现有的 HybridRetriever
retriever = get_retriever()
chunks = await retriever.search(query, top_k=20, library_ids=[library_id])

# 按文档聚合结果
doc_scores = {}
for chunk in chunks:
    doc_id = chunk.document_id
    if doc_id not in doc_scores:
        doc_scores[doc_id] = []
    doc_scores[doc_id].append(chunk.score)

# 计算文档总分（取最高分或平均分）
for doc_id, scores in doc_scores.items():
    doc_score = max(scores)  # 或 sum(scores) / len(scores)
```

### 方案 2: 使用 BM25 关键词检索

**优势**：
- ✅ 精确的关键词匹配
- ✅ TF-IDF 权重
- ✅ 已有基础设施（HybridRetriever 已实现）

**实现**：
```python
# 使用 BM25 检索
retriever = get_retriever(use_hybrid=True)
chunks = await retriever._bm25_search(query, library_id, top_k=20)
```

### 方案 3: 混合检索（最佳）

**优势**：
- ✅ 结合向量检索和 BM25
- ✅ 使用 RRF 融合结果
- ✅ 已有完整实现

**实现**：
```python
# 使用混合检索（已实现）
retriever = get_retriever(use_hybrid=True)
chunks = await retriever.search(query, top_k=20, library_ids=[library_id])
```

### 方案 4: 改进评分系统

**改进点**：
1. **多因素评分**：
   - 标题完全匹配：5分
   - 标题部分匹配：3分
   - 内容完全匹配：2分
   - 内容部分匹配：1分
   - 向量相似度：0-1分（归一化）

2. **位置权重**：
   - 标题开头匹配：额外 +1分
   - 内容开头匹配：额外 +0.5分

3. **频率权重**：
   - 匹配次数：log(次数 + 1) * 0.5分

### 方案 5: 添加查询扩展

**实现**：
```python
# 使用同义词扩展查询
from app.rag.synonyms import QueryExpander
expander = QueryExpander()
expanded_query = await expander.expand_async(query)

# 使用扩展后的查询进行检索
chunks = await retriever.search(expanded_query, ...)
```

## 推荐实现方案

### 短期改进（快速提升）

1. **使用向量检索替代字符串匹配**
   - 利用已有的向量化文档
   - 支持语义搜索
   - 实现简单

2. **改进评分系统**
   - 结合向量相似度分数
   - 考虑标题匹配权重
   - 多因素评分

### 长期改进（最佳效果）

1. **使用混合检索**
   - 向量检索 + BM25
   - RRF 融合
   - 重排序

2. **添加查询扩展**
   - 同义词扩展
   - 相关词扩展

3. **性能优化**
   - 使用数据库索引
   - 缓存热门查询
   - 分页加载

## 具体改进代码

### 改进后的搜索实现

```python
@router.post("/documents/search", response_model=StandardResponse[list[DocumentSearchResult]])
async def search_documents(
    payload: DocumentSearchRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    retriever: LangchainRetriever = Depends(get_retriever),
) -> StandardResponse[list[DocumentSearchResult]]:
    """Search documents using vector search + keyword search."""
    
    # 1. 使用向量检索获取相关 chunks
    library_ids = [payload.library_id] if payload.library_id else None
    chunks = await retriever.search(
        query=payload.query,
        top_k=payload.limit * 3,  # 获取更多候选
        library_ids=library_ids
    )
    
    # 2. 按文档聚合结果
    doc_scores: dict[str, list[float]] = {}
    doc_chunks: dict[str, list[RetrievedChunk]] = {}
    
    for chunk in chunks:
        doc_id = chunk.document_id
        if doc_id not in doc_scores:
            doc_scores[doc_id] = []
            doc_chunks[doc_id] = []
        doc_scores[doc_id].append(chunk.score)
        doc_chunks[doc_id].append(chunk)
    
    # 3. 计算文档分数（取最高分，或加权平均）
    doc_final_scores = {}
    for doc_id, scores in doc_scores.items():
        # 方案A: 取最高分
        doc_final_scores[doc_id] = max(scores)
        
        # 方案B: 加权平均（考虑匹配次数）
        # doc_final_scores[doc_id] = sum(scores) / len(scores) * (1 + 0.1 * len(scores))
    
    # 4. 获取文档信息并构建响应
    results: list[DocumentSearchResult] = []
    for doc_id, score in sorted(doc_final_scores.items(), key=lambda x: x[1], reverse=True)[:payload.limit]:
        doc = await session.get(Document, doc_id)
        if not doc:
            continue
        
        # 权限检查
        # ... (省略权限检查代码)
        
        # 获取最佳匹配的 chunk 作为 snippet
        best_chunk = max(doc_chunks[doc_id], key=lambda c: c.score)
        snippet = best_chunk.text[:200] + "..." if len(best_chunk.text) > 200 else best_chunk.text
        
        results.append(
            DocumentSearchResult(
                document_id=doc_id,
                title=doc.title,
                snippet=snippet,
                score=score,
                library_id=str(doc.library_id) if doc.library_id else None,
            )
        )
    
    return StandardResponse(data=results)
```

## 总结

**当前问题**：
1. ❌ 简单字符串匹配，无法处理同义词、词序等
2. ❌ 评分系统过于简单
3. ❌ 没有利用向量检索和 BM25
4. ❌ 性能问题（N+1 查询）

**改进方向**：
1. ✅ 使用向量检索（语义搜索）
2. ✅ 使用 BM25（关键词匹配）
3. ✅ 混合检索 + RRF 融合
4. ✅ 改进评分系统
5. ✅ 添加查询扩展

**推荐方案**：
- **短期**：使用向量检索替代字符串匹配
- **长期**：使用混合检索（向量 + BM25 + 重排序）

