"""Tests for application configuration."""

from app.config import Settings


class TestSettings:
    def test_defaults(self):
        s = Settings()
        assert s.app_name == "Novel Writing Agent"
        assert s.debug is False
        assert s.openai_model == "gpt-4o"
        assert s.openai_embedding_model == "text-embedding-3-small"

    def test_access_token_default_dev_mode(self):
        s = Settings()
        assert s.access_token == "change-me"

    def test_openai_api_keys_single(self):
        s = Settings(openai_api_key="sk-test123")
        assert s.openai_api_keys == ["sk-test123"]

    def test_openai_api_keys_multiple(self):
        s = Settings(openai_api_key="sk-key1, sk-key2 , sk-key3")
        assert s.openai_api_keys == ["sk-key1", "sk-key2", "sk-key3"]

    def test_openai_api_keys_empty(self):
        s = Settings(openai_api_key="")
        assert s.openai_api_keys == []

    def test_database_url_default(self):
        s = Settings()
        assert "postgresql://" in s.database_url

    def test_redis_url_default(self):
        s = Settings()
        assert s.redis_url.startswith("redis://")
