"""Report data structures."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.models.repo import RepositoryCandidate
from app.models.skill_card import RepoSkillCard


@dataclass(frozen=True)
class ResearchReport:
    idea: str
    candidates: tuple[RepositoryCandidate, ...] = field(default_factory=tuple)
    skill_cards: tuple[RepoSkillCard, ...] = field(default_factory=tuple)
    recommendation: str = ""

