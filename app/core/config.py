from functools import lru_cache
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    app_name: str = Field(default="Industrial QA Backend")
    app_env: str = Field(default="local")
    api_token: str = Field(default="very-secret-token")
    database_url: str = Field(default="sqlite+aiosqlite:///./industrial_qa.db")
    vector_db_uri: str = Field(default="chroma://./chroma_store")
    embedding_model: str = Field(default="bge-large")
    llm_provider: str = Field(default="openai")
    llm_model: str = Field(default="gpt-4o-mini")
    openai_api_key: str = Field(default="")
    allowed_origins: list[str] = Field(default_factory=lambda: ["*"])
    telemetry_sample_rate: float = Field(default=0.0)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]


settings = get_settings()

