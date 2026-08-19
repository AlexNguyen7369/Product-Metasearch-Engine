"""
Centralized settings, loaded from environment variables / .env.

Everything that varies between local, docker, and (eventually) deployed
environments belongs here — no module should read os.environ directly.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    serpapi_api_key: str = ""
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = 1800  # 30 min — prices don't change second-to-second
    rate_limit: str = "10/minute"  # applied to the /api/search endpoint


settings = Settings()
