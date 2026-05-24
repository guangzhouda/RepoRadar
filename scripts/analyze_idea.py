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
from app.providers.openai_provider import LLMProviderError, OpenAIProvider
from app.services.cache import JsonFileCache
from app.services.capability_extractor import CapabilityExtractor
from app.services.github_search import GitHubSearchService
from app.services.llm_candidate_reviewer import LLMCandidateReviewer
from app.services.llm_query_planner import LLMQueryPlanner
from app.services.query_understanding import build_search_queries
from app.services.repo_collector import RepositoryCollector


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Preview RepoRadar idea analysis.")
    parser.add_argument("--idea", required=True, help="Project idea to analyze.")
    parser.add_argument("--max-repos", type=int, default=10, help="Planned repository limit.")
    parser.add_argument("--max-queries", type=int, default=6, help="Maximum GitHub search queries to generate.")
    parser.add_argument("--format", choices=("json", "markdown"), default="json", help="Output format.")
    parser.add_argument("--output", help="Optional path for writing the full JSON payload.")
    parser.add_argument("--offline", action="store_true", help="Only generate search queries without calling GitHub.")
    parser.add_argument("--no-cache", action="store_true", help="Disable local GitHub search cache.")
    parser.add_argument(
        "--query-mode",
        choices=("llm", "rules"),
        default="llm",
        help="Use LLM query planning by default; rules mode is only a diagnostic fallback.",
    )
    parser.add_argument(
        "--review-mode",
        choices=("llm", "none"),
        default="llm",
        help="Use LLM relevance review by default after GitHub search.",
    )
    parser.add_argument(
        "--extract-cards",
        action="store_true",
        help="Collect README/docs/config files and generate LLM Repo Skill Cards for selected candidates.",
    )
    parser.add_argument("--card-limit", type=int, default=3, help="Maximum candidates to generate skill cards for.")
    parser.add_argument(
        "--card-decision",
        choices=("keep", "all"),
        default="keep",
        help="Generate cards for LLM-kept candidates by default, or all displayed candidates.",
    )
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
        if "relevance_score" in candidate:
            lines.append(
                f"   - Relevance: {candidate['relevance_score']} | Decision: {candidate.get('decision', '')}"
            )
        if candidate.get("reject_reason"):
            lines.append(f"   - Reject reason: {candidate['reject_reason']}")
        if candidate.get("rationale"):
            lines.append(f"   - Rationale: {candidate['rationale']}")
        skill_card = candidate.get("skill_card")
        if isinstance(skill_card, dict):
            capabilities = skill_card.get("core_capabilities", [])
            if isinstance(capabilities, list) and capabilities:
                lines.append(f"   - Core capabilities: {', '.join(str(item) for item in capabilities[:5])}")
            confidence = skill_card.get("confidence")
            lines.append(f"   - Skill card confidence: {confidence}")
        if candidate.get("skill_card_error"):
            lines.append(f"   - Skill card error: {candidate['skill_card_error']}")
        if candidate["description"]:
            lines.append(f"   - {candidate['description']}")
    return "\n".join(lines)


def attach_skill_cards(
    candidates: list[dict[str, object]],
    provider: GitHubRestProvider,
    llm_provider: OpenAIProvider,
    cache: JsonFileCache,
    use_cache: bool,
    limit: int,
    decision_filter: str,
) -> None:
    """Mutate candidate dictionaries with Repo Skill Cards for selected repos."""

    collector = RepositoryCollector(provider=provider, cache=cache, use_cache=use_cache)
    extractor = CapabilityExtractor(llm_provider)
    attached = 0

    for candidate in candidates:
        if attached >= max(0, limit):
            return
        if decision_filter == "keep" and candidate.get("decision") == "reject":
            continue

        full_name = str(candidate.get("full_name") or "").strip()
        if not full_name:
            continue

        try:
            collection = collector.collect(full_name)
            card = extractor.extract(full_name, collection)
        except (GitHubProviderError, LLMProviderError, ValueError) as exc:
            candidate["skill_card_error"] = str(exc)
            attached += 1
            continue

        files = collection.get("files", {})
        candidate["collected_files"] = list(files.keys()) if isinstance(files, dict) else []
        candidate["skill_card"] = card.to_dict()
        attached += 1


def main() -> int:
    args = build_parser().parse_args()
    settings = load_settings()
    llm_provider = OpenAIProvider(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        model=settings.llm_model,
    )
    try:
        if args.query_mode == "llm":
            queries = LLMQueryPlanner(llm_provider).build_queries(args.idea, max_queries=args.max_queries)
        else:
            queries = build_search_queries(args.idea, max_queries=args.max_queries)
    except (LLMProviderError, ValueError) as exc:
        payload = {
            "phase": "1-cli-search",
            "idea": args.idea.strip(),
            "max_repos": args.max_repos,
            "error": str(exc),
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False), file=sys.stderr)
        return 1

    payload = {
        "phase": "1-cli-search",
        "idea": args.idea.strip(),
        "max_repos": args.max_repos,
        "query_mode": args.query_mode,
        "review_mode": args.review_mode if not args.offline else "none",
        "extract_cards": bool(args.extract_cards and not args.offline),
        "card_limit": args.card_limit if args.extract_cards and not args.offline else 0,
        "card_decision": args.card_decision if args.extract_cards and not args.offline else "none",
        "queries": queries,
        "candidates": [],
    }

    if not args.offline:
        provider = GitHubRestProvider(token=settings.github_token, base_url=settings.github_api_base_url)
        cache = JsonFileCache(settings.cache_dir)
        service = GitHubSearchService(
            provider=provider,
            cache=cache,
            use_cache=not args.no_cache,
        )
        try:
            review_pool_size = min(50, max(args.max_repos * 4, args.max_repos))
            candidates = service.search_many(queries, max_repos=review_pool_size)
            if args.review_mode == "llm":
                reviewer = LLMCandidateReviewer(llm_provider)
                reviews = reviewer.review(args.idea.strip(), candidates)
                payload["candidates"] = reviewer.apply_reviews(candidates, reviews, args.max_repos)
            else:
                payload["candidates"] = [candidate.to_dict() for candidate in candidates[: args.max_repos]]
            if args.extract_cards:
                attach_skill_cards(
                    candidates=payload["candidates"],
                    provider=provider,
                    llm_provider=llm_provider,
                    cache=cache,
                    use_cache=not args.no_cache,
                    limit=args.card_limit,
                    decision_filter=args.card_decision,
                )
        except GitHubProviderError as exc:
            payload["error"] = str(exc)
            print(json.dumps(payload, indent=2, ensure_ascii=False), file=sys.stderr)
            return 1
        except (LLMProviderError, ValueError) as exc:
            payload["error"] = str(exc)
            print(json.dumps(payload, indent=2, ensure_ascii=False), file=sys.stderr)
            return 1

    payload["markdown"] = build_markdown(args.idea.strip(), payload["candidates"])
    output = json.dumps(payload, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")

    if args.format == "markdown":
        print(payload["markdown"])
    else:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

