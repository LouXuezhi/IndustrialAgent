from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

embedding_model = HuggingFaceEmbeddings(
    model_name=r"D:\PycharmProjects\AGENT_BACK-rag\models\BAAI\bge-large-zh",  # 替换为你的模型路径
    model_kwargs={"device": "cpu", "local_files_only": True},
    encode_kwargs={"normalize_embeddings": True}
)

# 2. 初始化 Chroma (持久化层)
chroma_db = Chroma(
    persist_directory="./chroma_store",
    embedding_function=embedding_model,
    collection_name="industrial_qa_docs"
)