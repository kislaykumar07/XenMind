"""
App settings, loaded from environment variables or a .env file.

Why this file exists:
- Keeps configuration (ports, allowed frontend URLs, DB URL) out of code.
- pydantic-settings reads values from the environment and validates their types,
  so a typo in .env fails loudly at startup instead of silently later.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Read a .env file in the folder you start the server from (backend/).
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "XenMind API"
    app_version: str = "0.1.0"
    environment: str = "local"  # local | test | production

    # Comma-separated list of frontend origins allowed to call this API from a browser.
    # 5173 = Vite default (Lovable projects use Vite), 3000 = common React dev port.
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    # Not used until Milestone 3, but defined now so the shape of config is settled.
    # SQLite file for local dev; swap to a Postgres/Supabase URL later.
    database_url: str = "sqlite:///./xenmind.db"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Create Settings once and reuse it (lru_cache = remember the result)."""
    return Settings()
