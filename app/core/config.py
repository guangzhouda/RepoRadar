"""Configuration helpers that avoid third-party dependencies at bootstrap."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True)
class Settings:
    github_token: str
    github_api_base_url: str
    github_search_per_page: int
    llm_provider: str
    llm_api_key: str
    llm_base_url: str
    llm_model: str
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


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def read_env_file(path: str | Path = ".env") -> dict[str, str]:
    env_path = Path(path)
    if not env_path.exists():
        return {}

    parsed: dict[str, str] = {}
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        parsed[key] = _strip_quotes(value.strip())

    return parsed


def load_settings(env: Mapping[str, str] | None = None) -> Settings:
    source: Mapping[str, str]
    if env is None:
        source = {**read_env_file(), **os.environ}
    else:
        source = env

    return Settings(
        github_token=source.get("GITHUB_TOKEN", ""),
        github_api_base_url=source.get("GITHUB_API_BASE_URL", "https://api.github.com"),
        github_search_per_page=_get_int(source, "GITHUB_SEARCH_PER_PAGE", 10),
        llm_provider=source.get("LLM_PROVIDER", "deepseek"),
        llm_api_key=source.get("LLM_API_KEY", ""),
        llm_base_url=source.get("LLM_BASE_URL", ""),
        llm_model=source.get("LLM_MODEL", ""),
        cache_dir=source.get("REPORADAR_CACHE_DIR", ".reporadar_cache"),
        log_level=source.get("REPORADAR_LOG_LEVEL", "INFO"),
    )

