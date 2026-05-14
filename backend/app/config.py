from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://novel_user:novel_pass@localhost:5432/novel_agent"
    redis_url: str = "redis://localhost:6379/0"
    openai_api_key: str = ""
    openai_base_url: str = ""
    openai_model: str = "gpt-4o"
    openai_fallback_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    access_token: str = "change-me"
    app_name: str = "Novel Writing Agent"
    llm_cache_enabled: bool = True
    content_moderation_enabled: bool = True
    content_moderation_blocked_words: str = ""
    debug: bool = False

    @property
    def openai_api_keys(self) -> list[str]:
        return [k.strip() for k in self.openai_api_key.split(",") if k.strip()]

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
