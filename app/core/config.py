from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # 应用基础配置
    app_name: str = Field(default="Industrial QA Backend")
    app_env: str = Field(default="local")

    # 安全配置
    api_token: str = Field(default="")

    # 数据库配置
    database_url: str = Field(default="")

    # 向量数据库配置
    vector_db_uri: str = Field(default="chroma://./chroma_store")
    storage_dir: str = Field(default="data/uploads")

    # 模型配置
    embedding_model: str = Field(default="bge-large")
    llm_provider: str = Field(default="openai")
    llm_model: str = Field(default="gpt-4o-mini")
    # 重排序配置
    reranker_model: str = Field(default="BAAI/bge-reranker-base", description="重排序模型名称")
    enable_rerank: bool = Field(default=True, description="是否启用重排序")
    rerank_candidate_count: int = Field(default=0, description="重排序候选数量，0表示使用 top_k + 3，>0表示固定数量")
    rerank_cache_enable: bool = Field(default=True, description="是否启用重排序缓存")
    rerank_cache_ttl: int = Field(default=7200, description="重排序缓存过期时间（秒），默认2小时")
    hf_endpoint: str = Field(default="", description="Hugging Face 镜像端点（如 https://hf-mirror.com）")
    # 查询扩展配置
    synonym_dict_path: str = Field(default="", description="同义词词典文件路径（JSON格式）")
    enable_query_expansion: bool = Field(default=True, description="是否启用查询扩展（同义词）")
    use_llm_expansion: bool = Field(default=False, description="是否使用 LLM 生成扩展词（需要 LLM 配置）")
    openai_api_key: str = Field(default="")
    dashscope_api_key: str = Field(default="")  # legacy combined key
    dashscope_base_url: str = Field(default="https://dashscope.aliyuncs.com/compatible-mode/v1")
    dashscope_embedding_api_key: str = Field(default="")
    dashscope_embedding_base_url: str = Field(default="https://dashscope.aliyuncs.com/compatible-mode/v1")
    dashscope_llm_api_key: str = Field(default="")
    dashscope_llm_base_url: str = Field(default="https://dashscope.aliyuncs.com/compatible-mode/v1")

    # CORS
    allowed_origins: list[str] = Field(default_factory=lambda: ["*"])

    # 遥测
    telemetry_sample_rate: float = Field(default=0.0)

    # 缓存（Redis）
    redis_url: str = Field(default="")
    # 搜索缓存配置
    enable_search_cache: bool = Field(default=True, description="是否启用搜索缓存")
    search_cache_ttl: int = Field(default=3600, description="搜索缓存过期时间（秒），默认1小时")

    # JWT
    jwt_secret: str = Field(default="")
    jwt_algorithm: str = Field(default="HS256")
    access_token_expires_minutes: int = Field(default=60)

    # 邮件服务（阿里云邮件推送）
    aliyun_access_key_id: str = Field(default="")
    aliyun_access_key_secret: str = Field(default="")
    aliyun_region: str = Field(default="cn-hangzhou")
    aliyun_smtp_password: str = Field(default="")
    from_email: str = Field(default="noreply@example.com")
    from_name: str = Field(default="Industrial QA System")

    # 前端URL（用于生成验证/重置链接）
    frontend_url: str = Field(default="http://localhost:3000")


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()

