"""Deterministic evidence verification for Repo Skill Cards.

The verifier checks whether LLM-extracted evidence is present, specific, and
free of obvious prompt-injection-like instructions. It does not prove the claim
is true; it gives scoring and reporting a conservative signal for evidence
quality without adding another LLM call.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.models.skill_card import Evidence, RepoSkillCard


SUSPICIOUS_EVIDENCE_PHRASES: tuple[str, ...] = (
    "ignore previous instructions",
    "ignore all previous instructions",
    "system prompt",
    "developer message",
    "return json",
    "do not follow",
    "forget the above",
)


@dataclass(frozen=True)
class EvidenceCheck:
    """Verification result for one evidence snippet."""

    source: str
    quote: str
    confidence: float
    warnings: tuple[str, ...] = ()

    @property
    def passed(self) -> bool:
        """Return whether this evidence has no warnings."""

        return not self.warnings

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable evidence check."""

        return {
            "source": self.source,
            "quote": self.quote,
            "confidence": self.confidence,
            "warnings": list(self.warnings),
            "passed": self.passed,
        }


@dataclass(frozen=True)
class EvidenceVerification:
    """Aggregate evidence quality signal for a Repo Skill Card."""

    repo: str
    score: float
    checks: tuple[EvidenceCheck, ...] = ()
    warnings: tuple[str, ...] = ()

    @property
    def passed(self) -> bool:
        """Return whether card-level and evidence-level checks are warning-free."""

        return not self.warnings and all(check.passed for check in self.checks)

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable verification result."""

        return {
            "repo": self.repo,
            "score": self.score,
            "warnings": list(self.warnings),
            "checks": [check.to_dict() for check in self.checks],
            "passed": self.passed,
        }


class EvidenceVerifier:
    """Verify evidence snippets attached to a Repo Skill Card."""

    def __init__(self, min_confidence: float = 0.5) -> None:
        self.min_confidence = min_confidence

    def verify(self, extracted_capability: object) -> float:
        """Backward-compatible confidence score for older call sites."""

        if isinstance(extracted_capability, RepoSkillCard):
            return self.verify_card(extracted_capability).score
        if isinstance(extracted_capability, Evidence):
            return self._check_evidence(extracted_capability, duplicate=False).confidence
        return 0.0

    def verify_card(self, card: RepoSkillCard) -> EvidenceVerification:
        """Return deterministic evidence quality checks for one skill card."""

        if not card.evidence:
            return EvidenceVerification(repo=card.repo, score=0.0, warnings=("evidence missing",))

        seen: set[tuple[str, str]] = set()
        checks: list[EvidenceCheck] = []
        for evidence in card.evidence:
            key = (evidence.source.strip().lower(), evidence.quote.strip().lower())
            duplicate = key in seen
            if key != ("", ""):
                seen.add(key)
            checks.append(self._check_evidence(evidence, duplicate))

        all_warnings = tuple(dict.fromkeys(warning for check in checks for warning in check.warnings))
        score = _round_score(sum(_check_score(check) for check in checks) / len(checks))
        return EvidenceVerification(repo=card.repo, score=score, checks=tuple(checks), warnings=all_warnings)

    def _check_evidence(self, evidence: Evidence, duplicate: bool) -> EvidenceCheck:
        warnings: list[str] = []
        source = evidence.source.strip()
        quote = evidence.quote.strip()

        if not source:
            warnings.append("evidence source missing")
        if not quote:
            warnings.append("evidence quote missing")
        if evidence.confidence < self.min_confidence:
            warnings.append("low evidence confidence")
        if duplicate:
            warnings.append("duplicate evidence")
        if _contains_suspicious_text(quote):
            warnings.append("suspicious evidence text")

        return EvidenceCheck(
            source=source,
            quote=quote,
            confidence=_round_score(evidence.confidence),
            warnings=tuple(warnings),
        )


def _check_score(check: EvidenceCheck) -> float:
    score = check.confidence
    if "evidence source missing" in check.warnings:
        score -= 0.25
    if "evidence quote missing" in check.warnings:
        score -= 0.35
    if "low evidence confidence" in check.warnings:
        score -= 0.20
    if "duplicate evidence" in check.warnings:
        score -= 0.10
    if "suspicious evidence text" in check.warnings:
        score -= 0.35
    return max(0.0, min(score, 1.0))


def _contains_suspicious_text(value: str) -> bool:
    normalized = " ".join(value.lower().split())
    return any(phrase in normalized for phrase in SUSPICIOUS_EVIDENCE_PHRASES)


def _round_score(value: float) -> float:
    return round(max(0.0, min(float(value), 1.0)), 3)
