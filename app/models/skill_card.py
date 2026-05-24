"""Repo Skill Card bootstrap schema."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Evidence:
    source: str
    quote: str
    confidence: float = 0.0


@dataclass(frozen=True)
class RepoSkillCard:
    repo: str
    name: str
    summary: str = ""
    categories: tuple[str, ...] = field(default_factory=tuple)
    core_capabilities: tuple[str, ...] = field(default_factory=tuple)
    evidence: tuple[Evidence, ...] = field(default_factory=tuple)

