"""Configuration helpers that avoid third-party dependencies at bootstrap."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping


@dataclass(frozen=True)
class Settings:
    github_token: str
    github_search_per_page: int
    llm_provider: str
    llm_api_key: str
    openai_api_key: str
    openai_model: str
    cache_dir: str
    log_level: str


def _get_int(env: Mapping[str, str], key: str, default: int) -> int:
    raw_value = env.get(key, "")
    if not raw_value:
        return default

    try:
        return int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{key} must be an integer") from exc


def load_settings(env: Mapping[str, str] | None = None) -> Settings:
    source = os.environ if env is None else env
    return Settings(
        github_token=source.get("GITHUB_TOKEN", ""),
        github_search_per_page=_get_int(source, "GITHUB_SEARCH_PER_PAGE", 10),
        llm_provider=source.get("LLM_PROVIDER", "openai"),
        llm_api_key=source.get("LLM_API_KEY", ""),
        openai_api_key=source.get("OPENAI_API_KEY", ""),
        openai_model=source.get("OPENAI_MODEL", ""),
        cache_dir=source.get("REPORADAR_CACHE_DIR", ".reporadar_cache"),
        log_level=source.get("REPORADAR_LOG_LEVEL", "INFO"),
    )

