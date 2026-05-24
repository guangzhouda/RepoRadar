"""Repository metadata structures."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RepositoryCandidate:
    full_name: str
    url: str
    description: str = ""
    stars: int = 0
    forks: int = 0
    language: str = ""
    topics: tuple[str, ...] = field(default_factory=tuple)

