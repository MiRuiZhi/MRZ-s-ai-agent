from __future__ import annotations

from functools import lru_cache
from typing import List

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except Exception:  # pragma: no cover - import-time fallback for docs/static inspection
    BaseSettings = object  # type: ignore
    SettingsConfigDict = dict  # type: ignore


class Settings(BaseSettings):  # type: ignore[misc]
    if hasattr(BaseSettings, "model_config"):
        model_config = SettingsConfigDict(env_file=".env", env_prefix="REACTOR_", extra="ignore")

    service_name: str = "reactor-agent-api"
    environment: str = "local"
    database_url: str = "mysql+pymysql://reactor:reactor@mysql:3306/reactor_agent"
    tool_runtime_base_url: str = "http://tool-runtime:1601"
    openai_base_url: str = "https://api.openai.com/v1"
    openai_api_key: str = ""
    planner_model: str = "gpt-4o-mini"
    executor_model: str = "gpt-4o-mini"
    react_model: str = "gpt-4o-mini"
    summary_model: str = "gpt-4o-mini"
    fake_llm: bool = False
    ledger_backend: str = "sql"
    run_migrations: bool = True
    run_seed: bool = True
    cors_origins: List[str] = ["*"]
    max_steps: int = 10
    max_parallel_tasks: int = 2


@lru_cache
def get_settings() -> Settings:
    return Settings()
