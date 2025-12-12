# RAG框架选型：LangChain

> 创建时间: 2025-12-07  
> 决策状态: ✅ 已确定

## 选型结果

**选择**: LangChain  
**应用范围**: Agent和RAG层  
**版本**: LangChain >= 0.2.0

## 技术特性

- **统一框架**: Agent和RAG使用同一框架，降低学习成本
- **丰富集成**: 支持Qwen、DeepSeek、本地模型等多种LLM和Embedding
- **组件化设计**: 清晰的组件划分，易于组合和扩展
- **活跃社区**: 70k+ GitHub stars，持续更新和维护

## LangChain在项目中的应用

### 1. RAG Pipeline实现

```python
# app/rag/pipeline.py
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.vectorstores import Chroma, Qdrant
from langchain.retrievers import BM25Retriever, EnsembleRetriever
from langchain_community.llms import Tongyi, DeepSeek
from langchain_community.embeddings import DashScopeEmbeddings

class RAGPipeline:
    def __init__(
        self,
        llm: BaseLLM,
        embeddings: Embeddings,
        vector_store: VectorStore
    ):
        self.llm = llm
        self.embeddings = embeddings
        self.vector_store = vector_store
        
        # 创建混合检索器
        self.retriever = self._create_hybrid_retriever()
        
        # 创建RAG链
        self.qa_chain = self._create_qa_chain()
    
    def _create_hybrid_retriever(self):
        # 向量检索器
        vector_retriever = self.vector_store.as_retriever(
            search_kwargs={"k": 10}
        )
        
        # BM25检索器
        bm25_retriever = BM25Retriever.from_texts(
            texts=self._get_all_texts(),
            k=10
        )
        
        # 混合检索器
        ensemble_retriever = EnsembleRetriever(
            retrievers=[vector_retriever, bm25_retriever],
            weights=[0.5, 0.5]
        )
        
        return ensemble_retriever
    
    def _create_qa_chain(self):
        prompt_template = """基于以下上下文回答问题。如果不知道答案，就说不知道。

上下文：
{context}

问题：{question}

答案："""
        
        prompt = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        
        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.retriever,
            chain_type_kwargs={"prompt": prompt},
            return_source_documents=True
        )
        
        return qa_chain
    
    async def run(self, query: str, top_k: int = 5) -> PipelineResult:
        # 执行RAG查询
        result = self.qa_chain.invoke({"query": query})
        
        return PipelineResult(
            answer=result["result"],
            references=self._format_references(result["source_documents"]),
            latency_ms=result.get("latency_ms", 0)
        )
```

### 2. Agent实现

```python
# app/agents/qa_agent.py
from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import Tool
from langchain.prompts import PromptTemplate
from langchain_community.llms import Tongyi

class QAAgent:
    def __init__(
        self,
        llm: BaseLLM,
        tools: list[Tool],
        rag_pipeline: RAGPipeline
    ):
        self.llm = llm
        self.tools = tools
        self.rag_pipeline = rag_pipeline
        
        # 创建Agent
        self.agent = self._create_agent()
    
    def _create_agent(self):
        # 定义工具
        tools = [
            Tool(
                name="KnowledgeBase",
                func=self._search_knowledge_base,
                description="搜索知识库获取相关信息"
            ),
            Tool(
                name="Calculator",
                func=self._calculate,
                description="执行数学计算"
            ),
            # 更多工具...
        ]
        
        # ReAct提示模板
        prompt = PromptTemplate.from_template("""
你是一个有用的AI助手。你可以使用以下工具：

{tools}

使用以下格式：
Question: 需要回答的问题
Thought: 你应该思考要做什么
Action: 要采取的行动，应该是[{tool_names}]中的一个
Action Input: 行动的输入
Observation: 行动的结果
... (这个思考/行动/行动输入/观察可以重复N次)
Thought: 我现在知道最终答案了
Final Answer: 原始问题的最终答案

Question: {input}
Thought: {agent_scratchpad}
""")
        
        # 创建Agent
        agent = create_react_agent(
            llm=self.llm,
            tools=tools,
            prompt=prompt
        )
        
        # 创建Agent执行器
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=5
        )
        
        return agent_executor
    
    def _search_knowledge_base(self, query: str) -> str:
        """搜索知识库"""
        result = self.rag_pipeline.run(query)
        return result.answer
    
    def _calculate(self, expression: str) -> str:
        """执行计算"""
        try:
            result = eval(expression)
            return str(result)
        except:
            return "计算错误"
    
    async def run(self, query: str, **kwargs) -> dict:
        """执行Agent查询"""
        result = await self.agent.ainvoke({"input": query})
        return {
            "answer": result["output"],
            "intermediate_steps": result.get("intermediate_steps", [])
        }
```

### 3. 向量存储集成

```python
# app/rag/vector_store.py
from langchain.vectorstores import Chroma, Qdrant, Milvus
from langchain_community.embeddings import DashScopeEmbeddings, HuggingFaceEmbeddings

def create_vector_store(
    vector_db_uri: str,
    embeddings: Embeddings,
    collection_name: str = "documents"
):
    """根据URI创建向量存储"""
    if vector_db_uri.startswith("chroma://"):
        path = vector_db_uri.replace("chroma://", "")
        return Chroma(
            persist_directory=path,
            embedding_function=embeddings,
            collection_name=collection_name
        )
    elif vector_db_uri.startswith("qdrant://"):
        url = vector_db_uri.replace("qdrant://", "")
        host, port = url.split(":")
        return Qdrant.from_existing_collection(
            host=host,
            port=int(port),
            collection_name=collection_name,
            embeddings=embeddings
        )
    elif vector_db_uri.startswith("milvus://"):
        # Milvus集成
        pass
    else:
        raise ValueError(f"Unsupported vector DB URI: {vector_db_uri}")
```

### 4. 文档加载和处理

```python
# app/rag/ingestion.py
from langchain.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma

class DocumentIngestor:
    def __init__(
        self,
        vector_store: VectorStore,
        embeddings: Embeddings
    ):
        self.vector_store = vector_store
        self.embeddings = embeddings
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
    
    async def ingest_document(self, file_path: str, library_id: str):
        # 1. 加载文档
        loader = self._get_loader(file_path)
        documents = loader.load()
        
        # 2. 分块
        chunks = self.text_splitter.split_documents(documents)
        
        # 3. 添加元数据
        for chunk in chunks:
            chunk.metadata["library_id"] = library_id
            chunk.metadata["source"] = file_path
        
        # 4. 向量化并存储
        await self.vector_store.add_documents(chunks)
        
        return len(chunks)
    
    def _get_loader(self, file_path: str):
        """根据文件类型获取加载器"""
        if file_path.endswith(".pdf"):
            return PyPDFLoader(file_path)
        elif file_path.endswith(".docx"):
            return Docx2txtLoader(file_path)
        elif file_path.endswith(".txt"):
            return TextLoader(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_path}")
```

## LangChain核心组件

### 1. LLM集成

```python
# 支持多种LLM
from langchain_community.llms import (
    Tongyi,      # 通义千问
    DeepSeek,    # DeepSeek
    OpenAI,      # OpenAI
    VLLM,        # 本地vLLM
    Ollama       # 本地Ollama
)
```

### 2. Embedding集成

```python
# 支持多种Embedding
from langchain_community.embeddings import (
    DashScopeEmbeddings,    # Qwen Embedding
    HuggingFaceEmbeddings,  # 本地模型（BGE/Qwen）
    OpenAIEmbeddings        # OpenAI
)
```

### 3. 向量存储集成

```python
# 支持多种向量数据库
from langchain.vectorstores import (
    Chroma,      # Chroma
    Qdrant,      # Qdrant
    Milvus,      # Milvus
    PGVector     # pgvector
)
```

### 4. 检索器

```python
# 多种检索器
from langchain.retrievers import (
    VectorStoreRetriever,  # 向量检索
    BM25Retriever,         # BM25检索
    EnsembleRetriever      # 混合检索
)
```

### 5. 链（Chains）

```python
# RAG链
from langchain.chains import (
    RetrievalQA,           # 问答链
    ConversationalRetrievalChain,  # 对话式检索链
    LLMChain               # LLM链
)
```

### 6. Agent

```python
# Agent工具
from langchain.agents import (
    AgentExecutor,
    create_react_agent,
    Tool
)
```

## 最佳实践

### 1. 组件复用

```python
# 共享LLM和Embedding实例
llm = get_llm(settings)
embeddings = get_embeddings(settings)

# 在多个地方复用
rag_pipeline = RAGPipeline(llm, embeddings, vector_store)
agent = QAAgent(llm, tools, rag_pipeline)
```

### 2. 异步支持

```python
# 使用异步方法
result = await qa_chain.ainvoke({"query": query})
```

### 3. 错误处理

```python
try:
    result = agent.invoke({"input": query})
except Exception as e:
    logger.error(f"Agent execution failed: {e}")
    return {"error": str(e)}
```

### 4. 性能优化

```python
# 使用缓存
from langchain.cache import InMemoryCache
from langchain.globals import set_llm_cache

set_llm_cache(InMemoryCache())
```

## 总结

LangChain作为Agent和RAG层的统一框架：
- ✅ **统一框架**: Agent和RAG使用同一框架
- ✅ **丰富集成**: 支持多种LLM、Embedding、向量数据库
- ✅ **组件化**: 清晰的组件设计，易于组合
- ✅ **活跃社区**: 持续更新和完善
- ✅ **生产就绪**: 大量生产环境验证

## 参考资源

- [LangChain官方文档](https://python.langchain.com/)
- [LangChain GitHub](https://github.com/langchain-ai/langchain)
- [LangChain中文文档](https://python.langchain.com.cn/)

