"""GitHub search service boundary."""

from __future__ import annotations

from app.models.repo import RepositoryCandidate


class GitHubSearchService:
    """Placeholder for the phase 1 GitHub Search API implementation."""

    def search(self, query: str, max_repos: int = 10) -> list[RepositoryCandidate]:
        raise NotImplementedError("GitHub Search API integration belongs to MVP phase 1")

