from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://clu:clu_dev@localhost:5432/clu"
    anthropic_api_key: str = ""
    extraction_model: str = "claude-sonnet-4-5-20250929"
    synthesis_model: str = "claude-opus-4-6"
    max_concurrent_extractions: int = 3
    api_v1_prefix: str = "/api/v1"

    # ChromaDB
    chromadb_host: str = "localhost"
    chromadb_port: int = 8001

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Logging
    log_json: bool = False
    log_level: str = "INFO"

    model_config = {"env_prefix": "", "case_sensitive": False}


settings = Settings()
