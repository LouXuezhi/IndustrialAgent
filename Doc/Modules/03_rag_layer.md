# RAG层模块文档

## 概述
RAG（Retrieval-Augmented Generation）层是系统的核心，负责文档检索、上下文构建和答案生成。采用混合检索策略（向量检索 + BM25）提升召回率和相关性。

## 模块结构

```
app/rag/
├── pipeline.py      # RAG流水线主控制器
├── retriever.py     # 混合检索器
├── prompts.py       # 提示模板管理
├── ingestion.py     # 文档摄取处理
└── evaluators.py    # 响应评估
```

## 1. RAG Pipeline (`pipeline.py`)

### 功能
RAG Pipeline是RAG流程的编排器，协调检索、提示构建和生成步骤。

### 关键类与依赖

- `RAGPipeline`：编排检索与生成，使用 LangChain `ChatPromptTemplate` + `ChatOpenAI`（OpenAI 或 DashScope 兼容 API）。
- `HybridRetriever`（`LangchainRetriever` 类型）：封装向量检索（Chroma）+ 检索扩展位。
- 配置来自 `Settings`：`llm_provider`（openai/dashscope）、`llm_model`、`openai_api_key`、`dashscope_*_api_key/base_url`。

### `run` 流程（现状）
1) 检索：`retriever.search(query, library_ids, top_k)`，按库过滤。
2) 构建提示：`ChatPromptTemplate` 生成对话模板，填充上下文与问题。
3) 生成：根据 `llm_provider` 选择客户端：
   - OpenAI: 使用 `openai_api_key`。
   - DashScope: 使用 `dashscope_llm_api_key` 或 `dashscope_api_key`，`base_url` 兼容 OpenAI。
4) 输出：返回答案与引用。

### 向量化与检索注意点
- 文档上传仅入库文件与元数据，向量化需调用 `/api/v1/docs/documents/{id}/vectorize` 后才可检索。
- `document.meta["vectorized"]` 反映是否已写入向量库；失败则为 False 并返回错误信息。
- 检索时依赖库 ID 过滤，支持私库/群库隔离。

## 2. 混合检索器 (`retriever.py`)

### 功能
HybridRetriever实现混合检索策略，结合向量检索和BM25检索的优势。

### 类定义

```python
class HybridRetriever:
    def __init__(self, vector_uri: str, embedding_model: str):
        self.vector_uri = vector_uri          # 向量数据库URI
        self.embedding_model = embedding_model # 嵌入模型名称
```

### 方法

#### `async def search(query: str, library_ids: list[uuid.UUID], top_k: int = 5) -> list[RetrievedChunk]`
**描述**: 执行混合检索（按文档库过滤）

**参数**:
- `query`: 查询字符串
- `library_ids`: 文档库ID列表（限制检索范围）
- `top_k`: 返回结果数量

**返回**: `RetrievedChunk` 列表

**RetrievedChunk结构**:
```python
@dataclass
class RetrievedChunk:
    document_id: str          # 文档ID
    library_id: str           # 文档库ID（新增）
    text: str                 # 文档块文本
    score: float              # 相关性分数
    metadata: dict[str, Any]  # 元数据（来源、页码等）
```

**重要变更**: 
- 检索结果必须包含`library_id`字段
- 检索时按`library_ids`过滤，只返回指定文档库中的文档块

### 当前实现状态
- ⚠️ 当前为占位实现，返回模拟数据
- 🔄 需要实现真实的向量检索和BM25检索

### 实现方案

#### 方案1: 向量检索 + BM25融合
```python
async def search(self, query: str, top_k: int = 5) -> list[RetrievedChunk]:
    # 1. 向量检索
    query_embedding = await self._embed_query(query)
    vector_results = await self._vector_search(query_embedding, top_k * 2)
    
    # 2. BM25检索
    bm25_results = await self._bm25_search(query, top_k * 2)
    
    # 3. 结果融合（Reciprocal Rank Fusion）
    fused_results = self._rrf_fusion(vector_results, bm25_results)
    
    # 4. 重排序（可选）
    reranked = await self._rerank(query, fused_results[:top_k * 2])
    
    return reranked[:top_k]
```

#### 方案2: 向量数据库集成（Chroma示例）
```python
import chromadb
from chromadb.config import Settings as ChromaSettings

class HybridRetriever:
    def __init__(self, vector_uri: str, embedding_model: str):
        self.client = chromadb.PersistentClient(path=vector_uri)
        self.collection = self.client.get_or_create_collection("documents")
        self.embedding_model = embedding_model
    
    async def _embed_query(self, query: str) -> list[float]:
        # 调用嵌入模型API
        ...
    
    async def _vector_search(self, embedding: list[float], top_k: int):
        results = self.collection.query(
            query_embeddings=[embedding],
            n_results=top_k
        )
        return results
```

#### 方案3: BM25实现
```python
from rank_bm25 import BM25Okapi

class HybridRetriever:
    def __init__(self, ...):
        ...
        self.bm25_index = None  # 延迟初始化
    
    async def _build_bm25_index(self):
        # 从数据库加载所有文档块
        chunks = await self._load_all_chunks()
        tokenized_corpus = [chunk.split() for chunk in chunks]
        self.bm25_index = BM25Okapi(tokenized_corpus)
    
    async def _bm25_search(self, query: str, top_k: int):
        if self.bm25_index is None:
            await self._build_bm25_index()
        
        tokenized_query = query.split()
        scores = self.bm25_index.get_scores(tokenized_query)
        top_indices = np.argsort(scores)[-top_k:][::-1]
        return [chunks[i] for i in top_indices]
```

### 检索策略对比

| 方法 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| 向量检索 | 语义理解强，支持多语言 | 需要嵌入模型，计算成本高 | 语义相似查询 |
| BM25 | 关键词匹配精确，速度快 | 无法理解语义 | 精确关键词查询 |
| 混合检索 | 兼顾语义和关键词 | 实现复杂，需要融合策略 | 生产环境推荐 |

## 3. 提示模板 (`prompts.py`)

### 功能
管理不同角色和场景的提示模板，支持个性化答案生成。

### 模板定义

#### 基础模板
```python
BASE_PROMPT = """You are an expert {role} for an industrial company.
Answer the user's question using ONLY the provided context.

Context:
{context}

Question: {question}
Helpful answer:"""
```

#### 角色特定模板
- **operator**: 运维技术人员视角 - 技术细节、操作步骤、故障排查
- **maintenance**: 维护工程师视角 - 维护流程、故障排查、预防性维护
- **manager**: 工厂管理者视角 - 决策支持、数据分析、战略规划
- **admin**: 系统管理员视角 - 系统管理、配置优化

### 函数

#### `def get_prompt(role: str | None = None) -> str`
**描述**: 根据角色获取提示模板

**参数**:
- `role`: 用户角色（operator/maintenance/manager/admin）

**返回**: 格式化的提示字符串

**角色与Prompt的关联**:
角色不仅影响权限，还直接影响Agent的回答风格和内容重点：

1. **operator角色**:
   - Prompt强调操作步骤和技术细节
   - 适合回答"如何操作"、"步骤是什么"等问题
   - 示例: "作为运维技术人员，请提供详细的操作步骤..."

2. **maintenance角色**:
   - Prompt强调维护流程和故障排查
   - 适合回答"如何维护"、"故障如何排查"等问题
   - 示例: "作为维护工程师，请提供维护流程和故障排查方法..."

3. **manager角色**:
   - Prompt强调决策支持和数据分析
   - 适合回答"如何决策"、"数据分析"等问题
   - 示例: "作为工厂管理者，请提供决策建议和数据分析..."

4. **admin角色**:
   - Prompt强调系统管理和配置
   - 适合回答系统配置和管理相关问题

### 模板扩展

添加新角色模板：
```python
ROLE_PROMPTS["safety_officer"] = BASE_PROMPT.format(
    role="safety officer",
    context="{context}",
    question="{question}"
)
```

添加场景特定模板：
```python
SCENARIO_PROMPTS = {
    "troubleshooting": """You are troubleshooting an industrial issue.
    Analyze the context and provide step-by-step solutions.
    
    Context: {context}
    Problem: {question}
    Solution:""",
    
    "maintenance_schedule": """Generate a maintenance schedule based on the provided documentation.
    ...
    """
}
```

## 4. 文档摄取 (`ingestion.py`)

### 功能
处理文档上传，进行分块、向量化和存储。

### 类定义

```python
class DocumentIngestor:
    async def ingest_file(self, path: Path, session: AsyncSession) -> IngestionReport
```

### 方法

#### `async def ingest_file(path: Path, session: AsyncSession) -> IngestionReport`
**描述**: 摄取单个文档文件

**参数**:
- `path`: 文档文件路径
- `session`: 数据库会话

**返回** (`IngestionReport`):
```python
@dataclass
class IngestionReport:
    document_id: uuid.UUID    # 文档UUID
    chunk_count: int          # 生成的块数量
```

### 当前实现状态
- ⚠️ 当前为简化占位实现
- 🔄 需要实现完整的分块、向量化和存储流程

### 完整实现方案

```python
class DocumentIngestor:
    def __init__(self, retriever: HybridRetriever):
        self.retriever = retriever
    
    async def ingest_file(self, path: Path, session: AsyncSession) -> IngestionReport:
        # 1. 解析文档
        text = await self._parse_document(path)
        
        # 2. 分块
        chunks = self._chunk_text(text, chunk_size=500, overlap=50)
        
        # 3. 创建文档记录
        document = await crud.create_document(
            session,
            title=path.name,
            source_path=str(path),
            metadata={"file_type": path.suffix}
        )
        
        # 4. 向量化和存储
        chunk_count = 0
        for i, chunk_text in enumerate(chunks):
            # 生成嵌入
            embedding = await self._embed_text(chunk_text)
            
            # 存储到向量库
            await self.retriever._store_chunk(
                document_id=str(document.id),
                chunk_id=f"{document.id}_{i}",
                text=chunk_text,
                embedding=embedding,
                metadata={"chunk_index": i}
            )
            
            # 存储元数据到数据库
            chunk = models.Chunk(
                document_id=document.id,
                content=chunk_text,
                metadata={"chunk_index": i}
            )
            session.add(chunk)
            chunk_count += 1
        
        await session.commit()
        return IngestionReport(document_id=document.id, chunk_count=chunk_count)
    
    def _chunk_text(self, text: str, chunk_size: int, overlap: int) -> list[str]:
        # 使用LangChain的文本分割器
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=overlap
        )
        return splitter.split_text(text)
```

## 5. 响应评估 (`evaluators.py`)

### 功能
评估生成答案的质量，包括忠实度、相关性等指标。

### 函数

#### `async def evaluate_response(answer: str, references: list[dict]) -> EvaluationResult`
**描述**: 评估答案质量

**参数**:
- `answer`: 生成的答案
- `references`: 引用来源列表

**返回** (`EvaluationResult`):
```python
@dataclass
class EvaluationResult:
    faithfulness: float    # 忠实度分数（0-1）
    relevance: float       # 相关性分数（0-1）
    notes: str            # 评估备注
```

### 当前实现状态
- ⚠️ 当前为占位实现
- 🔄 需要集成评估模型（如GPT-4作为Judge）

### 评估实现方案

#### 方案1: LLM作为Judge
```python
async def evaluate_response(answer: str, references: list[dict]) -> EvaluationResult:
    judge_prompt = f"""Evaluate the following answer:
    
    Answer: {answer}
    References: {references}
    
    Rate on a scale of 0-1:
    1. Faithfulness: Does the answer stay true to the references?
    2. Relevance: Does the answer address the question?
    
    Respond in JSON format:
    {{"faithfulness": 0.9, "relevance": 0.8, "notes": "..."}}
    """
    
    response = await llm_client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": judge_prompt}],
        response_format={"type": "json_object"}
    )
    
    result = json.loads(response.choices[0].message.content)
    return EvaluationResult(**result)
```

#### 方案2: 基于规则的评估
```python
def evaluate_response(answer: str, references: list[dict]) -> EvaluationResult:
    # 忠实度：检查答案中的关键信息是否在引用中
    faithfulness = check_faithfulness(answer, references)
    
    # 相关性：检查答案长度、引用数量等
    relevance = check_relevance(answer, references)
    
    return EvaluationResult(
        faithfulness=faithfulness,
        relevance=relevance,
        notes="Rule-based evaluation"
    )
```

## RAG流程优化建议

1. **检索优化**:
   - 实现查询扩展（Query Expansion）
   - 添加重排序（Reranking）步骤
   - 支持多轮对话上下文

2. **生成优化**:
   - 实现流式生成（Streaming）
   - 支持引用标注（Citation）
   - 添加答案置信度评分

3. **评估优化**:
   - 实现A/B测试框架
   - 收集用户反馈并闭环优化
   - 建立评估数据集和基准测试

