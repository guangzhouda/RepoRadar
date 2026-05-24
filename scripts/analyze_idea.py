"""Command-line entry point for RepoRadar idea analysis.

The script builds multiple GitHub search queries, runs repository search unless
offline preview is requested, and emits either JSON or a basic Markdown list.
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
from app.services.cache import JsonFileCache
from app.services.github_search import GitHubSearchService
from app.services.query_understanding import build_search_queries


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Preview RepoRadar idea analysis.")
    parser.add_argument("--idea", required=True, help="Project idea to analyze.")
    parser.add_argument("--max-repos", type=int, default=10, help="Planned repository limit.")
    parser.add_argument("--max-queries", type=int, default=6, help="Maximum GitHub search queries to generate.")
    parser.add_argument("--format", choices=("json", "markdown"), default="json", help="Output format.")
    parser.add_argument("--offline", action="store_true", help="Only generate search queries without calling GitHub.")
    parser.add_argument("--no-cache", action="store_true", help="Disable local GitHub search cache.")
    return parser


def build_markdown(idea: str, candidates: list[dict[str, object]]) -> str:
    """Build a compact Markdown candidate list for human review."""

    lines = ["# RepoRadar Candidate Repositories", "", f"Idea: {idea}", ""]
    if not candidates:
        lines.append("No candidates found.")
        return "\n".join(lines)

    for index, candidate in enumerate(candidates, start=1):
        lines.append(f"{index}. [{candidate['full_name']}]({candidate['url']})")
        lines.append(f"   - Stars: {candidate['stars']} | Forks: {candidate['forks']} | Language: {candidate['language']}")
        if candidate["description"]:
            lines.append(f"   - {candidate['description']}")
    return "\n".join(lines)


def main() -> int:
    args = build_parser().parse_args()
    settings = load_settings()
    queries = build_search_queries(args.idea, max_queries=args.max_queries)

    payload = {
        "phase": "1-cli-search",
        "idea": args.idea.strip(),
        "max_repos": args.max_repos,
        "queries": queries,
        "candidates": [],
    }

    if not args.offline:
        provider = GitHubRestProvider(token=settings.github_token, base_url=settings.github_api_base_url)
        service = GitHubSearchService(
            provider=provider,
            cache=JsonFileCache(settings.cache_dir),
            use_cache=not args.no_cache,
        )
        try:
            payload["candidates"] = [candidate.to_dict() for candidate in service.search_many(queries, max_repos=args.max_repos)]
        except GitHubProviderError as exc:
            payload["error"] = str(exc)
            print(json.dumps(payload, indent=2, ensure_ascii=False), file=sys.stderr)
            return 1

    payload["markdown"] = build_markdown(args.idea.strip(), payload["candidates"])
    if args.format == "markdown":
        print(payload["markdown"])
    else:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

