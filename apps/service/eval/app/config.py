from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    anthropic_api_key: str
    openai_api_key: str
    ragas_judge_model: str = "claude-haiku-4-5"
    ragas_embeddings_model: str = "text-embedding-3-small"
    rag_bot_base_url: str
    rag_bot_api_key: str
    eval_timeout_seconds: int = 120
    log_level: str = "INFO"


settings = Settings()
