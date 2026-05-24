"""GitHub search orchestration service.

The service coordinates provider calls, optional JSON caching, candidate
normalization, deduplication, and sorting. It keeps CLI scripts free of GitHub
response-shape details.
"""

from __future__ import annotations

from app.models.repo import RepositoryCandidate
from app.providers.github_rest_provider import GitHubRestProvider
from app.services.cache import JsonFileCache


class GitHubSearchService:
    """Search GitHub repositories and normalize candidates."""

    def __init__(
        self,
        provider: GitHubRestProvider,
        cache: JsonFileCache | None = None,
        use_cache: bool = True,
    ) -> None:
        self.provider = provider
        self.cache = cache
        self.use_cache = use_cache

    def search(self, query: str, max_repos: int = 10) -> list[RepositoryCandidate]:
        """Search a single GitHub query and return normalized candidates."""

        response = self._search_raw(query, max_repos)
        return [candidate for candidate in normalize_repository_response(response, query) if not candidate.archived and not candidate.fork]

    def search_many(self, queries: list[str], max_repos: int = 10) -> list[RepositoryCandidate]:
        """Search multiple queries, deduplicate by full name, and sort candidates."""

        candidates_by_name: dict[str, RepositoryCandidate] = {}
        for query in queries:
            for candidate in self.search(query, max_repos=max_repos):
                existing = candidates_by_name.get(candidate.full_name)
                if existing is None:
                    candidates_by_name[candidate.full_name] = candidate
                else:
                    merged_queries = tuple(dict.fromkeys((*existing.source_queries, *candidate.source_queries)))
                    if candidate.stars > existing.stars:
                        candidates_by_name[candidate.full_name] = candidate_with_queries(candidate, merged_queries)
                    else:
                        candidates_by_name[candidate.full_name] = candidate_with_queries(existing, merged_queries)

        sorted_candidates = sorted(
            candidates_by_name.values(),
            key=lambda candidate: (candidate.stars, candidate.forks, candidate.pushed_at),
            reverse=True,
        )
        return sorted_candidates[:max_repos]

    def _search_raw(self, query: str, max_repos: int) -> dict[str, object]:
        cache_key = f"{query}|{max_repos}"
        if self.cache is not None and self.use_cache:
            cached = self.cache.get("github_search", cache_key)
            if cached is not None:
                return cached

        response = self.provider.search_repositories(query, per_page=max_repos)
        if self.cache is not None and self.use_cache:
            self.cache.set("github_search", cache_key, response)
        return response


def normalize_repository_response(response: dict[str, object], source_query: str) -> list[RepositoryCandidate]:
    """Normalize a GitHub repository search response into internal candidates."""

    raw_items = response.get("items", [])
    if not isinstance(raw_items, list):
        return []

    candidates: list[RepositoryCandidate] = []
    for item in raw_items:
        if isinstance(item, dict):
            candidates.append(normalize_repository_item(item, source_query))
    return candidates


def normalize_repository_item(item: dict[str, object], source_query: str) -> RepositoryCandidate:
    """Normalize one GitHub API repository item."""

    license_info = item.get("license")
    license_name = ""
    if isinstance(license_info, dict):
        license_name = str(license_info.get("spdx_id") or license_info.get("name") or "")

    topics = item.get("topics", [])
    normalized_topics = tuple(str(topic) for topic in topics) if isinstance(topics, list) else ()

    return RepositoryCandidate(
        full_name=str(item.get("full_name") or ""),
        url=str(item.get("html_url") or item.get("url") or ""),
        description=str(item.get("description") or ""),
        stars=int(item.get("stargazers_count") or 0),
        forks=int(item.get("forks_count") or 0),
        language=str(item.get("language") or ""),
        license=license_name,
        topics=normalized_topics,
        pushed_at=str(item.get("pushed_at") or ""),
        created_at=str(item.get("created_at") or ""),
        archived=bool(item.get("archived") or False),
        fork=bool(item.get("fork") or False),
        source_queries=(source_query,),
    )


def candidate_with_queries(candidate: RepositoryCandidate, source_queries: tuple[str, ...]) -> RepositoryCandidate:
    """Return a candidate copy with merged source queries."""

    return RepositoryCandidate(
        full_name=candidate.full_name,
        url=candidate.url,
        description=candidate.description,
        stars=candidate.stars,
        forks=candidate.forks,
        language=candidate.language,
        license=candidate.license,
        topics=candidate.topics,
        pushed_at=candidate.pushed_at,
        created_at=candidate.created_at,
        archived=candidate.archived,
        fork=candidate.fork,
        source_queries=source_queries,
    )

