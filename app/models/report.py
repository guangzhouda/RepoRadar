"""Report data structures.

This module holds the plain input shape consumed by the Markdown report
generator. It does not calculate scores or format output; those responsibilities
stay in service modules.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.models.repo import RepositoryCandidate
from app.models.skill_card import RepoSkillCard


@dataclass(frozen=True)
class CandidateAssessment:
    """Review fields attached to a candidate before report generation."""

    full_name: str
    relevance_score: float = 0.0
    decision: str = ""
    reject_reason: str = ""
    rationale: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "CandidateAssessment":
        """Create assessment metadata from analyze CLI JSON."""

        try:
            relevance_score = float(data.get("relevance_score") or 0.0)
        except (TypeError, ValueError):
            relevance_score = 0.0

        return cls(
            full_name=str(data.get("full_name") or ""),
            relevance_score=max(0.0, min(relevance_score, 1.0)),
            decision=str(data.get("decision") or ""),
            reject_reason=str(data.get("reject_reason") or ""),
            rationale=str(data.get("rationale") or ""),
        )


@dataclass(frozen=True)
class ResearchReport:
    """A repository research report request.

    The report combines the original user idea, search strategy, normalized
    candidates, optional skill cards, and an optional human/LLM recommendation.
    Instances are immutable so generation and export paths can reuse them
    without side effects.
    """

    idea: str
    queries: tuple[str, ...] = field(default_factory=tuple)
    candidates: tuple[RepositoryCandidate, ...] = field(default_factory=tuple)
    skill_cards: tuple[RepoSkillCard, ...] = field(default_factory=tuple)
    assessments: tuple[CandidateAssessment, ...] = field(default_factory=tuple)
    recommendation: str = ""

