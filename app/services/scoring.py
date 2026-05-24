"""Repository scoring service.

The scoring engine converts normalized repository metadata, optional LLM review
signals, and optional Repo Skill Cards into comparable score dimensions. It is
heuristic by design for the MVP and keeps the documented weighting formula in
one place for report generation.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
import math

from app.models.repo import RepositoryCandidate
from app.models.skill_card import RepoSkillCard
from app.services.evidence_verifier import EvidenceVerification, EvidenceVerifier


SCORING_WEIGHTS: dict[str, float] = {
    "relevance": 0.35,
    "maturity": 0.20,
    "activity": 0.15,
    "reusability": 0.15,
    "documentation": 0.10,
    "license": 0.05,
}


@dataclass(frozen=True)
class ScoreBreakdown:
    """Comparable repository score with dimension-level evidence."""

    repo: str
    overall: float
    relevance: float
    maturity: float
    activity: float
    reusability: float
    documentation: float
    license: float
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable score representation."""

        return {
            "repo": self.repo,
            "overall": self.overall,
            "relevance": self.relevance,
            "maturity": self.maturity,
            "activity": self.activity,
            "reusability": self.reusability,
            "documentation": self.documentation,
            "license": self.license,
            "notes": list(self.notes),
        }


class ScoringEngine:
    """Score candidates across relevance, maturity, activity, and reuse signals."""

    def __init__(self, today: date | None = None, evidence_verifier: EvidenceVerifier | None = None) -> None:
        self.today = today or datetime.now(timezone.utc).date()
        self.evidence_verifier = evidence_verifier or EvidenceVerifier()

    def score(
        self,
        candidate: RepositoryCandidate,
        skill_card: RepoSkillCard | None = None,
        relevance_score: float | None = None,
    ) -> ScoreBreakdown:
        """Return a weighted score breakdown for one candidate repository.

        Args:
            candidate: Normalized GitHub repository metadata.
            skill_card: Optional structured capability card for the repository.
            relevance_score: Optional LLM candidate-review score in the 0-1 range.

        Returns:
            A score breakdown using the documented MVP weights. Missing fields
            default to conservative low scores rather than optimistic guesses.
        """

        relevance = self._score_relevance(skill_card, relevance_score)
        maturity = self._score_maturity(candidate)
        activity = self._score_activity(candidate)
        license_score = self._score_license(candidate)
        reusability = self._score_reusability(skill_card, license_score)
        evidence_verification = self.evidence_verifier.verify_card(skill_card) if skill_card is not None else None
        documentation = self._score_documentation(skill_card, evidence_verification)

        dimensions = {
            "relevance": relevance,
            "maturity": maturity,
            "activity": activity,
            "reusability": reusability,
            "documentation": documentation,
            "license": license_score,
        }
        overall = sum(dimensions[name] * weight for name, weight in SCORING_WEIGHTS.items())

        return ScoreBreakdown(
            repo=candidate.full_name,
            overall=_round_score(overall),
            relevance=_round_score(relevance),
            maturity=_round_score(maturity),
            activity=_round_score(activity),
            reusability=_round_score(reusability),
            documentation=_round_score(documentation),
            license=_round_score(license_score),
            notes=tuple(_score_notes(candidate, skill_card, evidence_verification)),
        )

    def _score_relevance(self, skill_card: RepoSkillCard | None, relevance_score: float | None) -> float:
        if relevance_score is not None:
            return _clamp(relevance_score)
        if skill_card is None:
            return 0.0
        if skill_card.core_capabilities:
            return max(0.55, skill_card.confidence)
        if skill_card.claimed_but_unverified_capabilities:
            return min(0.45, max(0.25, skill_card.confidence))
        return 0.0

    def _score_maturity(self, candidate: RepositoryCandidate) -> float:
        star_score = _log_score(candidate.stars, scale=4.0)
        fork_score = _log_score(candidate.forks, scale=3.0)
        return (0.7 * star_score) + (0.3 * fork_score)

    def _score_activity(self, candidate: RepositoryCandidate) -> float:
        pushed_date = _parse_github_date(candidate.pushed_at)
        if pushed_date is None:
            return 0.0

        age_days = max(0, (self.today - pushed_date).days)
        if age_days <= 180:
            return 1.0
        if age_days <= 365:
            return 0.8
        if age_days <= 730:
            return 0.5
        if age_days <= 1095:
            return 0.25
        return 0.1

    def _score_reusability(
        self,
        skill_card: RepoSkillCard | None,
        license_score: float,
    ) -> float:
        if skill_card is None:
            return 0.25 * license_score

        interface_score = 1.0 if skill_card.interfaces else 0.0
        deployment_score = 1.0 if skill_card.deployment else 0.0
        capability_score = 1.0 if skill_card.core_capabilities else 0.0
        format_score = 1.0 if skill_card.input_formats or skill_card.output_formats else 0.0
        return (
            0.25 * license_score
            + 0.25 * interface_score
            + 0.20 * deployment_score
            + 0.20 * capability_score
            + 0.10 * format_score
        )

    def _score_documentation(
        self,
        skill_card: RepoSkillCard | None,
        evidence_verification: EvidenceVerification | None,
    ) -> float:
        if skill_card is None:
            return 0.0

        evidence_score = evidence_verification.score if evidence_verification is not None else 0.0
        summary_score = 1.0 if skill_card.summary else 0.0
        capability_score = 1.0 if skill_card.core_capabilities else 0.0
        return (0.45 * evidence_score) + (0.25 * summary_score) + (0.30 * capability_score)

    def _score_license(self, candidate: RepositoryCandidate) -> float:
        normalized = candidate.license.strip().lower()
        if not normalized:
            return 0.0
        if normalized in {"noassertion", "none", "unknown", "other"}:
            return 0.3
        return 1.0


def _clamp(value: float) -> float:
    return max(0.0, min(float(value), 1.0))


def _round_score(value: float) -> float:
    return round(_clamp(value), 3)


def _log_score(value: int, scale: float) -> float:
    if value <= 0:
        return 0.0
    return _clamp(math.log10(value + 1) / scale)


def _parse_github_date(value: str) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def _score_notes(
    candidate: RepositoryCandidate,
    skill_card: RepoSkillCard | None,
    evidence_verification: EvidenceVerification | None,
) -> list[str]:
    notes: list[str] = []
    if not candidate.license:
        notes.append("license missing")
    if not candidate.pushed_at:
        notes.append("activity unknown")
    if skill_card is None:
        notes.append("skill card missing")
    elif evidence_verification is not None:
        notes.extend(evidence_verification.warnings)
    return notes
