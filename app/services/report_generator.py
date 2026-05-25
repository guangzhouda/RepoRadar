"""Markdown report generation service.

The generator turns a structured ResearchReport into a readable comparison
report. It owns presentation and lightweight recommendation wording while
delegating numeric scoring to the scoring service.
"""

from __future__ import annotations

from app.models.report import CandidateAssessment, ResearchReport
from app.models.repo import RepositoryCandidate
from app.models.skill_card import RepoSkillCard
from app.services.reuse_advisor import build_default_recommendation, build_reuse_analysis
from app.services.scoring import ScoreBreakdown, ScoringEngine


class ReportGenerator:
    """Generate Markdown comparison reports from research results."""

    def __init__(self, scoring_engine: ScoringEngine | None = None) -> None:
        self.scoring_engine = scoring_engine or ScoringEngine()

    def generate_markdown(self, report: ResearchReport) -> str:
        """Return a Markdown report for candidates, skill cards, and scores."""

        idea = report.idea.strip() or "Unknown idea"
        skill_cards = {card.repo: card for card in report.skill_cards}
        assessments = {assessment.full_name: assessment for assessment in report.assessments}
        scored_candidates = self._score_candidates(report.candidates, skill_cards, assessments)

        lines: list[str] = [
            "# RepoRadar Research Report",
            "",
            "## User Idea",
            "",
            idea,
            "",
            "## Search Strategy",
            "",
        ]

        if report.queries:
            lines.extend(f"- `{query}`" for query in report.queries)
        else:
            lines.append("- Search queries were not provided.")

        lines.extend(["", "## Candidate Overview", ""])
        if not scored_candidates:
            lines.extend(
                [
                    "No candidate repositories were provided.",
                    "",
                    "## Recommendation",
                    "",
                    report.recommendation.strip() or "Run repository search and capability extraction before making a reuse decision.",
                ]
            )
            return "\n".join(lines).rstrip() + "\n"

        lines.extend(_candidate_table(scored_candidates, assessments))
        lines.extend(["", "## Top Project Skill Cards", ""])
        lines.extend(_skill_card_sections(scored_candidates, skill_cards, assessments))
        lines.extend(["", "## Capability Comparison", ""])
        lines.extend(_capability_table(scored_candidates, skill_cards))
        lines.extend(["", "## Implementation Signals", ""])
        lines.extend(_implementation_table(scored_candidates, skill_cards))
        lines.extend(["", "## Reuse vs Build Analysis", ""])
        lines.extend(build_reuse_analysis(scored_candidates, skill_cards))
        lines.extend(["", "## Recommendation", ""])
        lines.append(report.recommendation.strip() or build_default_recommendation(scored_candidates))
        return "\n".join(lines).rstrip() + "\n"

    def _score_candidates(
        self,
        candidates: tuple[RepositoryCandidate, ...],
        skill_cards: dict[str, RepoSkillCard],
        assessments: dict[str, CandidateAssessment],
    ) -> list[tuple[RepositoryCandidate, ScoreBreakdown]]:
        scored: list[tuple[RepositoryCandidate, ScoreBreakdown]] = []
        for candidate in candidates:
            assessment = assessments.get(candidate.full_name)
            relevance_score = assessment.relevance_score if assessment else None
            score = self.scoring_engine.score(candidate, skill_cards.get(candidate.full_name), relevance_score)
            scored.append((candidate, score))
        return sorted(scored, key=lambda item: item[1].overall, reverse=True)


def _candidate_table(
    scored_candidates: list[tuple[RepositoryCandidate, ScoreBreakdown]],
    assessments: dict[str, CandidateAssessment],
) -> list[str]:
    lines = [
        "| Repo | Decision | Review | Score | Relevance | Maturity | Activity | Reuse | Docs | License | Notes |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |",
    ]
    for candidate, score in scored_candidates:
        assessment = assessments.get(candidate.full_name)
        decision = assessment.decision if assessment and assessment.decision else "unreviewed"
        review = _review_note(assessment)
        notes = _join_or_unknown(score.notes, limit=4) if score.notes else ""
        lines.append(
            " | ".join(
                [
                    f"| [{_cell(candidate.full_name)}]({_cell(candidate.url)})",
                    _cell(decision),
                    _cell(review),
                    f"{score.overall:.3f}",
                    f"{score.relevance:.3f}",
                    f"{score.maturity:.3f}",
                    f"{score.activity:.3f}",
                    f"{score.reusability:.3f}",
                    f"{score.documentation:.3f}",
                    f"{score.license:.3f}",
                    f"{_cell(notes)} |",
                ]
            )
        )
    return lines


def _skill_card_sections(
    scored_candidates: list[tuple[RepositoryCandidate, ScoreBreakdown]],
    skill_cards: dict[str, RepoSkillCard],
    assessments: dict[str, CandidateAssessment],
) -> list[str]:
    lines: list[str] = []
    candidates_with_cards = [
        (candidate, score, skill_cards[candidate.full_name])
        for candidate, score in scored_candidates
        if candidate.full_name in skill_cards
    ]
    missing_candidates = [candidate for candidate, _score in scored_candidates if candidate.full_name not in skill_cards]

    if not candidates_with_cards:
        lines.append("No skill cards were generated for this analysis.")
        lines.extend(_missing_skill_card_lines(missing_candidates, assessments))
        return lines

    for candidate, score, card in candidates_with_cards[:3]:
        lines.append(f"### {_cell(candidate.full_name)}")
        lines.append("")
        lines.append(card.summary or "No summary available.")
        lines.append("")
        lines.append(f"- Score: `{score.overall:.3f}`")
        lines.append(f"- Confidence: `{card.confidence:.3f}`")
        lines.append(f"- Categories: {_join_or_unknown(card.categories)}")
        lines.append(f"- Interfaces: {_join_or_unknown(card.interfaces)}")
        lines.append(f"- Inputs: {_join_or_unknown(card.input_formats)}")
        lines.append(f"- Outputs: {_join_or_unknown(card.output_formats)}")
        lines.append(f"- Core capabilities: {_join_or_unknown(card.core_capabilities)}")
        lines.append(f"- Optional capabilities: {_join_or_unknown(card.optional_capabilities)}")
        lines.append(f"- Model providers: {_join_or_unknown(card.model_providers)}")
        lines.append(f"- Deployment: {_join_or_unknown(card.deployment)}")
        lines.append(f"- Suitable for: {_join_or_unknown(card.suitable_for)}")
        lines.append(f"- Not supported: {_join_or_unknown(card.not_supported)}")
        if score.notes:
            lines.append(f"- Evidence notes: {_join_or_unknown(score.notes)}")
        if card.limitations:
            lines.append(f"- Limitations: {_join_or_unknown(card.limitations)}")
        if card.evidence:
            evidence = card.evidence[0]
            quote = _truncate(evidence.quote, 160)
            lines.append(f"- Evidence: `{evidence.source}` - \"{_cell(quote)}\"")
        lines.append("")
    lines.extend(_missing_skill_card_lines(missing_candidates, assessments))
    return lines


def _capability_table(
    scored_candidates: list[tuple[RepositoryCandidate, ScoreBreakdown]],
    skill_cards: dict[str, RepoSkillCard],
) -> list[str]:
    candidates_with_cards = [
        (candidate, score)
        for candidate, score in scored_candidates
        if candidate.full_name in skill_cards
    ]
    missing_candidates = [candidate for candidate, _score in scored_candidates if candidate.full_name not in skill_cards]

    if not candidates_with_cards:
        return [
            "No generated skill cards are available for capability comparison.",
            *_missing_skill_card_lines(missing_candidates, {}),
        ]

    lines = [
        "| Repo | Inputs | Outputs | Interfaces | Core Capabilities | Limitations |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for candidate, _score in candidates_with_cards:
        card = skill_cards[candidate.full_name]
        lines.append(
            " | ".join(
                [
                    f"| {_cell(candidate.full_name)}",
                    _cell(_join_or_unknown(card.input_formats, limit=3)),
                    _cell(_join_or_unknown(card.output_formats, limit=3)),
                    _cell(_join_or_unknown(card.interfaces, limit=3)),
                    _cell(_join_or_unknown(card.core_capabilities, limit=3)),
                    f"{_cell(_join_or_unknown(card.limitations, limit=2))} |",
                ]
            )
        )
    lines.extend(["", *_missing_skill_card_lines(missing_candidates, {})])
    return lines


def _implementation_table(
    scored_candidates: list[tuple[RepositoryCandidate, ScoreBreakdown]],
    skill_cards: dict[str, RepoSkillCard],
) -> list[str]:
    candidates_with_cards = [
        (candidate, score)
        for candidate, score in scored_candidates
        if candidate.full_name in skill_cards
    ]
    missing_candidates = [candidate for candidate, _score in scored_candidates if candidate.full_name not in skill_cards]

    if not candidates_with_cards:
        return [
            "No generated skill cards are available for implementation signals.",
            *_missing_skill_card_lines(missing_candidates, {}),
        ]

    lines = [
        "| Repo | Model Providers | Deployment | Suitable For | Not Supported |",
        "| --- | --- | --- | --- | --- |",
    ]
    for candidate, _score in candidates_with_cards:
        card = skill_cards[candidate.full_name]
        lines.append(
            " | ".join(
                [
                    f"| {_cell(candidate.full_name)}",
                    _cell(_join_or_unknown(card.model_providers, limit=3)),
                    _cell(_join_or_unknown(card.deployment, limit=3)),
                    _cell(_join_or_unknown(card.suitable_for, limit=3)),
                    f"{_cell(_join_or_unknown(card.not_supported, limit=3))} |",
                ]
            )
        )
    lines.extend(["", *_missing_skill_card_lines(missing_candidates, {})])
    return lines


def _join_or_unknown(items: tuple[str, ...], limit: int = 5) -> str:
    values = [item for item in items if item]
    if not values:
        return "not extracted"
    return ", ".join(values[:limit])


def _missing_skill_card_lines(
    candidates: list[RepositoryCandidate],
    assessments: dict[str, CandidateAssessment],
) -> list[str]:
    if not candidates:
        return []

    names = ", ".join(_cell(candidate.full_name) for candidate in candidates)
    lines = ["", f"Skill card not generated for: {names}."]
    for candidate in candidates:
        assessment = assessments.get(candidate.full_name)
        if assessment and assessment.skill_card_error:
            lines.append(f"Skill card error: {_cell(assessment.skill_card_error)}")
    lines.append("")
    return lines


def _review_note(assessment: CandidateAssessment | None) -> str:
    if assessment is None:
        return ""
    return assessment.reject_reason or assessment.rationale or assessment.skill_card_error


def _cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


def _truncate(value: str, limit: int) -> str:
    stripped = value.strip()
    if len(stripped) <= limit:
        return stripped
    return stripped[: limit - 3].rstrip() + "..."
