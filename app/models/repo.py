"""Repository metadata structures used by search, collection, and reports.

This module defines the internal representation of GitHub repository candidates.
Providers normalize external API responses into these dataclasses before service
and report code consume them.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RepositoryCandidate:
    """A normalized GitHub repository candidate.

    Instances are immutable so search, scoring, and report generation can safely
    pass candidates around without mutating shared state.
    """

    full_name: str
    url: str
    description: str = ""
    stars: int = 0
    forks: int = 0
    language: str = ""
    license: str = ""
    topics: tuple[str, ...] = field(default_factory=tuple)
    pushed_at: str = ""
    created_at: str = ""
    archived: bool = False
    fork: bool = False
    source_queries: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable representation for CLI and cache output."""

        return {
            "full_name": self.full_name,
            "url": self.url,
            "description": self.description,
            "stars": self.stars,
            "forks": self.forks,
            "language": self.language,
            "license": self.license,
            "topics": list(self.topics),
            "pushed_at": self.pushed_at,
            "created_at": self.created_at,
            "archived": self.archived,
            "fork": self.fork,
            "source_queries": list(self.source_queries),
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "RepositoryCandidate":
        """Create a repository candidate from CLI/cache JSON data."""

        topics = data.get("topics", [])
        source_queries = data.get("source_queries", [])
        return cls(
            full_name=str(data.get("full_name") or ""),
            url=str(data.get("url") or ""),
            description=str(data.get("description") or ""),
            stars=int(data.get("stars") or 0),
            forks=int(data.get("forks") or 0),
            language=str(data.get("language") or ""),
            license=str(data.get("license") or ""),
            topics=tuple(str(topic) for topic in topics) if isinstance(topics, list) else (),
            pushed_at=str(data.get("pushed_at") or ""),
            created_at=str(data.get("created_at") or ""),
            archived=bool(data.get("archived") or False),
            fork=bool(data.get("fork") or False),
            source_queries=tuple(str(query) for query in source_queries) if isinstance(source_queries, list) else (),
        )

