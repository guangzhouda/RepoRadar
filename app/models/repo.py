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

