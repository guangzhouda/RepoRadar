"""Command-line entry point for RepoRadar repository collection.

The script implements MVP phase 2: fetch a single repository's metadata and
planned README/docs/config files, then optionally ask the configured LLM to
extract a Repo Skill Card.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import load_settings
from app.providers.github_rest_provider import GitHubProviderError, GitHubRestProvider
from app.providers.openai_provider import LLMProviderError, OpenAIProvider
from app.services.cache import JsonFileCache
from app.services.capability_extractor import CapabilityExtractor
from app.services.repo_collector import RepositoryCollector
from app.services.skill_card_cache import CachedCapabilityExtractor


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fetch repository evidence and optionally extract a skill card.")
    parser.add_argument("--repo", required=True, help="GitHub repository in owner/repo format.")
    parser.add_argument("--extract-card", action="store_true", help="Use the configured LLM to generate a Repo Skill Card.")
    parser.add_argument("--include-content", action="store_true", help="Include collected file content in stdout JSON.")
    parser.add_argument("--no-cache", action="store_true", help="Disable local repository collection cache.")
    parser.add_argument("--output", help="Optional path for writing the full JSON payload.")
    return parser


def summarize_collection(collection: dict[str, object]) -> dict[str, object]:
    """Return a compact collection summary for terminal output."""

    metadata = collection.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}
    files = collection.get("files", {})
    if not isinstance(files, dict):
        files = {}

    return {
        "repo": collection.get("repo", ""),
        "metadata": {
            "full_name": metadata.get("full_name"),
            "description": metadata.get("description"),
            "html_url": metadata.get("html_url"),
            "language": metadata.get("language"),
            "stargazers_count": metadata.get("stargazers_count"),
            "forks_count": metadata.get("forks_count"),
            "pushed_at": metadata.get("pushed_at"),
        },
        "collected_files": list(files.keys()),
        "missing_files": collection.get("missing_files", []),
        "skipped_files": collection.get("skipped_files", []),
    }

def main() -> int:
    args = build_parser().parse_args()
    settings = load_settings()
    provider = GitHubRestProvider(token=settings.github_token, base_url=settings.github_api_base_url)
    cache = JsonFileCache(settings.cache_dir)
    collector = RepositoryCollector(
        provider=provider,
        cache=cache,
        use_cache=not args.no_cache,
    )

    payload: dict[str, object] = {
        "phase": "2-repo-collection",
        "repo": args.repo.strip(),
    }

    try:
        collection = collector.collect(args.repo)
        payload["collection"] = collection if args.include_content else summarize_collection(collection)

        if args.extract_card:
            llm_provider = OpenAIProvider(
                api_key=settings.llm_api_key,
                base_url=settings.llm_base_url,
                model=settings.llm_model,
            )
            extractor = CachedCapabilityExtractor(
                CapabilityExtractor(llm_provider),
                cache=cache,
                use_cache=not args.no_cache,
                model_id=settings.llm_model,
            )
            card = extractor.extract(args.repo.strip(), collection)
            payload["skill_card"] = card.to_dict()
    except (GitHubProviderError, LLMProviderError, ValueError) as exc:
        payload["error"] = str(exc)
        print(json.dumps(payload, indent=2, ensure_ascii=False), file=sys.stderr)
        return 1

    output = json.dumps(payload, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

