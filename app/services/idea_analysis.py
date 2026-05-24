"""Idea analysis orchestration service.

This module owns the Phase 1/2 analysis workflow behind ``scripts/analyze_idea``:
query planning, GitHub search, LLM candidate review, optional skill-card
attachment, and compact candidate Markdown. CLI code should pass parsed options
in and handle only output concerns.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.config import Settings
from app.providers.github_rest_provider import GitHubProviderError, GitHubRestProvider
from app.providers.openai_provider import LLMProviderError, OpenAIProvider
from app.services.cache import JsonFileCache
from app.services.capability_extractor import CapabilityExtractor
from app.services.github_search import GitHubSearchService
from app.services.llm_candidate_reviewer import LLMCandidateReviewer
from app.services.llm_query_planner import LLMQueryPlanner
from app.services.query_understanding import build_search_queries
from app.services.repo_collector import RepositoryCollector


@dataclass(frozen=True)
class IdeaAnalysisOptions:
    """User-selected options for one idea analysis run."""

    idea: str
    max_repos: int
    max_queries: int
    offline: bool
    no_cache: bool
    query_mode: str
    review_mode: str
    extract_cards: bool
    card_limit: int
    card_decision: str


class IdeaAnalysisService:
    """Run the CLI idea-analysis workflow and return a JSON-ready payload."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def analyze(self, options: IdeaAnalysisOptions) -> dict[str, Any]:
        """Return the analysis payload for one project idea."""

        llm_provider = _build_llm_provider(self.settings)
        try:
            queries = _build_queries(options, llm_provider)
        except (LLMProviderError, ValueError) as exc:
            return {
                "phase": "1-cli-search",
                "idea": options.idea.strip(),
                "max_repos": options.max_repos,
                "error": str(exc),
            }

        payload = _base_payload(options, queries)
        if not options.offline:
            try:
                payload["candidates"] = self._search_and_review(options, queries, llm_provider)
                if options.extract_cards:
                    self._attach_skill_cards(payload["candidates"], llm_provider, options)
            except (GitHubProviderError, LLMProviderError, ValueError) as exc:
                payload["error"] = str(exc)
                return payload

        payload["markdown"] = build_candidate_markdown(options.idea.strip(), payload["candidates"])
        return payload

    def _search_and_review(
        self,
        options: IdeaAnalysisOptions,
        queries: list[str],
        llm_provider: OpenAIProvider,
    ) -> list[dict[str, object]]:
        provider = _build_github_provider(self.settings)
        cache = JsonFileCache(self.settings.cache_dir)
        service = GitHubSearchService(provider=provider, cache=cache, use_cache=not options.no_cache)
        review_pool_size = min(50, max(options.max_repos * 4, options.max_repos))
        candidates = service.search_many(queries, max_repos=review_pool_size)

        if options.review_mode == "llm":
            reviewer = LLMCandidateReviewer(llm_provider)
            reviews = reviewer.review(options.idea.strip(), candidates)
            return reviewer.apply_reviews(candidates, reviews, options.max_repos)
        return [candidate.to_dict() for candidate in candidates[: options.max_repos]]

    def _attach_skill_cards(
        self,
        candidates: list[dict[str, object]],
        llm_provider: OpenAIProvider,
        options: IdeaAnalysisOptions,
    ) -> None:
        provider = _build_github_provider(self.settings)
        cache = JsonFileCache(self.settings.cache_dir)
        collector = RepositoryCollector(provider=provider, cache=cache, use_cache=not options.no_cache)
        extractor = CapabilityExtractor(llm_provider)
        attached = 0

        for candidate in candidates:
            if attached >= max(0, options.card_limit):
                return
            if options.card_decision == "keep" and candidate.get("decision") == "reject":
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


def build_candidate_markdown(idea: str, candidates: list[dict[str, object]]) -> str:
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
            lines.append(f"   - Skill card confidence: {skill_card.get('confidence')}")
        if candidate.get("skill_card_error"):
            lines.append(f"   - Skill card error: {candidate['skill_card_error']}")
        if candidate["description"]:
            lines.append(f"   - {candidate['description']}")
    return "\n".join(lines)


def _build_llm_provider(settings: Settings) -> OpenAIProvider:
    return OpenAIProvider(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        model=settings.llm_model,
    )


def _build_github_provider(settings: Settings) -> GitHubRestProvider:
    return GitHubRestProvider(token=settings.github_token, base_url=settings.github_api_base_url)


def _build_queries(options: IdeaAnalysisOptions, llm_provider: OpenAIProvider) -> list[str]:
    if options.query_mode == "llm":
        return LLMQueryPlanner(llm_provider).build_queries(options.idea, max_queries=options.max_queries)
    return build_search_queries(options.idea, max_queries=options.max_queries)


def _base_payload(options: IdeaAnalysisOptions, queries: list[str]) -> dict[str, Any]:
    return {
        "phase": "1-cli-search",
        "idea": options.idea.strip(),
        "max_repos": options.max_repos,
        "query_mode": options.query_mode,
        "review_mode": options.review_mode if not options.offline else "none",
        "extract_cards": bool(options.extract_cards and not options.offline),
        "card_limit": options.card_limit if options.extract_cards and not options.offline else 0,
        "card_decision": options.card_decision if options.extract_cards and not options.offline else "none",
        "queries": queries,
        "candidates": [],
    }
