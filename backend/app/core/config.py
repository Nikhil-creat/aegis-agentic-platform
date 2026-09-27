"""
Environment-based configuration for the Aegis platform.
Designed and Developed by NIKHIL CHARY SRIRAMOJU
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "Aegis Autonomous Agentic Platform"
    ENV: str = "production"
    DEBUG: bool = False

    # Security
    JWT_SECRET: str = "change_me_super_secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    # Datastores
    DATABASE_URL: str = "postgresql+asyncpg://aegis:aegis_pw@postgres:5432/aegis"
    REDIS_URL: str = "redis://redis:6379/0"
    QDRANT_URL: str = "http://qdrant:6333"

    # LLM Providers
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    DEFAULT_LLM_MODEL: str = "gpt-4o-mini"

    # RAG
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    RERANKER_MODEL: str = "BAAI/bge-reranker-base"
    SEMANTIC_CACHE_THRESHOLD: float = 0.92
    TOP_K_RETRIEVAL: int = 20
    TOP_K_RERANKED: int = 5

    # Code Execution Sandbox
    SANDBOX_CPU_LIMIT: str = "0.5"
    SANDBOX_MEM_LIMIT: str = "256m"
    SANDBOX_TIMEOUT_SECONDS: int = 15
    SANDBOX_NETWORK_DISABLED: bool = True

    # Observability
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://otel-collector:4317"
    LANGCHAIN_TRACING_V2: bool = True

    AUTHOR: str = "Nikhil Chary Sriramoju"


@lru_cache
def get_settings() -> Settings:
    return Settings()
