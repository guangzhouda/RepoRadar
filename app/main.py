"""Minimal command entry point for the RepoRadar bootstrap."""

from __future__ import annotations

import argparse
import json
from typing import Sequence

from app import __version__
from app.core.config import load_settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="reporadar")
    parser.add_argument("--version", action="store_true", help="Print the RepoRadar version.")
    parser.add_argument(
        "--check-config",
        action="store_true",
        help="Print configuration readiness without contacting external services.",
    )
    return parser


def build_config_status() -> dict[str, object]:
    settings = load_settings()
    return {
        "app": "RepoRadar",
        "version": __version__,
        "phase": "0-bootstrap",
        "github_token_configured": bool(settings.github_token),
        "llm_key_configured": bool(settings.llm_api_key or settings.openai_api_key),
        "llm_provider": settings.llm_provider,
        "cache_dir": settings.cache_dir,
        "log_level": settings.log_level,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.version:
        print(__version__)
        return 0

    if args.check_config:
        print(json.dumps(build_config_status(), indent=2, sort_keys=True))
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

