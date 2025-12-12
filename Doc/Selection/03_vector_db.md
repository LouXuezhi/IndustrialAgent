# 向量数据库选型

> 创建时间: 2025-12-07  
> 决策状态: ✅ 已确定（Chroma为默认，支持多方案）

## 选型结果

**默认选择**: Chroma  
**支持方案**: Qdrant, Milvus, pgvector  
**策略**: 多适配器模式，支持运行时切换

## 向量数据库方案

### Chroma (默认选择)

#### 优势
- ✅ **极简部署**: 嵌入式模式，无需单独服务
- ✅ **Python原生**: 专为Python设计，API简洁
- ✅ **快速上手**: 学习曲线平缓，文档清晰
- ✅ **轻量级**: 适合中小规模应用
- ✅ **开源免费**: MIT许可证

#### 使用示例
```python
import chromadb
from chromadb.config import Settings

client = chromadb.Client(Settings(
    chroma_db_impl="duckdb+parquet",
    persist_directory="./chroma_store"
))

collection = client.get_or_create_collection("documents")
collection.add(
    embeddings=vectors,
    documents=texts,
    ids=ids
)
```

### Qdrant (大规模生产)

#### 特性
- **高性能**: Rust实现，性能优异
- **生产就绪**: 成熟稳定，大量生产案例
- **丰富功能**: 支持过滤、混合搜索等
- **云服务**: 提供托管服务

#### 使用示例
```python
from qdrant_client import QdrantClient

client = QdrantClient(host="localhost", port=6333)
client.upsert(
    collection_name="documents",
    points=points
)
```

### Milvus (超大规模)

#### 特性
- **超大规模**: 支持数十亿向量
- **分布式**: 原生支持分布式部署
- **丰富索引**: 多种索引算法支持
- **云原生**: Kubernetes友好

### pgvector (PostgreSQL扩展)

#### 特性
- **统一存储**: 向量和关系数据在同一数据库
- **ACID保证**: 完整的事务支持
- **成熟稳定**: 基于PostgreSQL，久经考验
- **运维简单**: 无需额外服务

#### 使用示例
```sql
CREATE EXTENSION vector;

CREATE TABLE documents (
    id uuid PRIMARY KEY,
    content text,
    embedding vector(1536)
);

CREATE INDEX ON documents USING ivfflat (embedding vector_cosine_ops);
```

## 项目中的实现

### 多适配器模式

项目采用适配器模式，支持运行时切换向量数据库：

```python
# app/rag/retriever.py
class HybridRetriever:
    def __init__(self, vector_uri: str, embedding_model: str):
        self.vector_uri = vector_uri
        self.embedding_model = embedding_model
        # 根据URI自动选择适配器
        self.client = self._create_client(vector_uri)
    
    def _create_client(self, uri: str):
        if uri.startswith("chroma://"):
            return ChromaAdapter(uri)
        elif uri.startswith("qdrant://"):
            return QdrantAdapter(uri)
        elif uri.startswith("milvus://"):
            return MilvusAdapter(uri)
        elif uri.startswith("postgresql://"):
            return PgVectorAdapter(uri)
```

### 配置方式

通过环境变量配置向量数据库：

```bash
# 使用Chroma（默认）
VECTOR_DB_URI=chroma://./chroma_store

# 使用Qdrant
VECTOR_DB_URI=qdrant://localhost:6333

# 使用Milvus
VECTOR_DB_URI=milvus://localhost:19530

# 使用pgvector
VECTOR_DB_URI=postgresql://user:pass@localhost/dbname
```

## 项目中的实现

### 多适配器模式

项目采用适配器模式，支持运行时切换向量数据库：

```python
# app/rag/retriever.py
class HybridRetriever:
    def __init__(self, vector_uri: str, embedding_model: str):
        self.vector_uri = vector_uri
        self.embedding_model = embedding_model
        # 根据URI自动选择适配器
        self.client = self._create_client(vector_uri)
    
    def _create_client(self, uri: str):
        if uri.startswith("chroma://"):
            return ChromaAdapter(uri)
        elif uri.startswith("qdrant://"):
            return QdrantAdapter(uri)
        elif uri.startswith("milvus://"):
            return MilvusAdapter(uri)
        elif uri.startswith("postgresql://"):
            return PgVectorAdapter(uri)
```

### 配置方式

通过环境变量配置向量数据库：

```bash
# 使用Chroma（默认）
VECTOR_DB_URI=chroma://./chroma_store

# 使用Qdrant
VECTOR_DB_URI=qdrant://localhost:6333

# 使用Milvus
VECTOR_DB_URI=milvus://localhost:19530

# 使用pgvector
VECTOR_DB_URI=postgresql://user:pass@localhost/dbname
```

## 总结

- **默认选择Chroma**: 适合快速开发和中小规模应用
- **支持多方案**: 通过适配器模式支持Qdrant、Milvus、pgvector
- **灵活切换**: 根据业务规模选择合适的向量数据库

## 参考资源

- [Chroma文档](https://docs.trychroma.com/)
- [Qdrant文档](https://qdrant.tech/documentation/)
- [Milvus文档](https://milvus.io/docs/)
- [pgvector文档](https://github.com/pgvector/pgvector)

