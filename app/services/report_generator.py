"""Markdown report generation service.

The generator turns a structured ResearchReport into a readable comparison
report. It owns presentation and lightweight recommendation wording while
delegating numeric scoring to the scoring service.
"""

from __future__ import annotations

from app.models.report import CandidateAssessment, ResearchReport
from app.models.repo import RepositoryCandidate
from app.models.skill_card import RepoSkillCard
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
        lines.extend(_skill_card_sections(scored_candidates, skill_cards))
        lines.extend(["", "## Capability Comparison", ""])
        lines.extend(_capability_table(scored_candidates, skill_cards))
        lines.extend(["", "## Reuse vs Build Analysis", ""])
        lines.extend(_reuse_analysis(scored_candidates, skill_cards))
        lines.extend(["", "## Recommendation", ""])
        lines.append(report.recommendation.strip() or _default_recommendation(scored_candidates))
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
        "| Repo | Decision | Score | Relevance | Maturity | Activity | Reuse | Docs | License |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for candidate, score in scored_candidates:
        assessment = assessments.get(candidate.full_name)
        decision = assessment.decision if assessment and assessment.decision else "unreviewed"
        lines.append(
            " | ".join(
                [
                    f"| [{_cell(candidate.full_name)}]({_cell(candidate.url)})",
                    _cell(decision),
                    f"{score.overall:.3f}",
                    f"{score.relevance:.3f}",
                    f"{score.maturity:.3f}",
                    f"{score.activity:.3f}",
                    f"{score.reusability:.3f}",
                    f"{score.documentation:.3f}",
                    f"{score.license:.3f} |",
                ]
            )
        )
    return lines


def _skill_card_sections(
    scored_candidates: list[tuple[RepositoryCandidate, ScoreBreakdown]],
    skill_cards: dict[str, RepoSkillCard],
) -> list[str]:
    lines: list[str] = []
    for candidate, score in scored_candidates[:3]:
        card = skill_cards.get(candidate.full_name)
        lines.append(f"### {_cell(candidate.full_name)}")
        lines.append("")
        if card is None:
            lines.append("No skill card was generated for this repository.")
            lines.append("")
            continue

        lines.append(card.summary or "No summary available.")
        lines.append("")
        lines.append(f"- Score: `{score.overall:.3f}`")
        lines.append(f"- Confidence: `{card.confidence:.3f}`")
        lines.append(f"- Interfaces: {_join_or_unknown(card.interfaces)}")
        lines.append(f"- Inputs: {_join_or_unknown(card.input_formats)}")
        lines.append(f"- Outputs: {_join_or_unknown(card.output_formats)}")
        lines.append(f"- Core capabilities: {_join_or_unknown(card.core_capabilities)}")
        if card.limitations:
            lines.append(f"- Limitations: {_join_or_unknown(card.limitations)}")
        if card.evidence:
            evidence = card.evidence[0]
            quote = _truncate(evidence.quote, 160)
            lines.append(f"- Evidence: `{evidence.source}` - \"{_cell(quote)}\"")
        lines.append("")
    return lines


def _capability_table(
    scored_candidates: list[tuple[RepositoryCandidate, ScoreBreakdown]],
    skill_cards: dict[str, RepoSkillCard],
) -> list[str]:
    lines = [
        "| Repo | Inputs | Outputs | Interfaces | Core Capabilities | Limitations |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for candidate, _score in scored_candidates:
        card = skill_cards.get(candidate.full_name)
        if card is None:
            lines.append(f"| {_cell(candidate.full_name)} | unknown | unknown | unknown | unknown | skill card missing |")
            continue
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
    return lines


def _reuse_analysis(
    scored_candidates: list[tuple[RepositoryCandidate, ScoreBreakdown]],
    skill_cards: dict[str, RepoSkillCard],
) -> list[str]:
    top_candidate, top_score = scored_candidates[0]
    top_card = skill_cards.get(top_candidate.full_name)
    lines = [
        f"- Top candidate: `{top_candidate.full_name}` with score `{top_score.overall:.3f}`.",
        f"- Reuse signals: maturity `{top_score.maturity:.3f}`, activity `{top_score.activity:.3f}`, reusability `{top_score.reusability:.3f}`.",
    ]

    if top_card and top_card.core_capabilities:
        lines.append(f"- Reusable modules: {_join_or_unknown(top_card.core_capabilities, limit=4)}.")
    else:
        lines.append("- Reusable modules are unclear because no evidence-backed skill card is available.")

    gaps: list[str] = []
    if top_card:
        gaps.extend(top_card.not_supported)
        gaps.extend(top_card.limitations)
    if gaps:
        lines.append(f"- Differentiation opportunities: {_join_or_unknown(tuple(gaps), limit=4)}.")
    else:
        lines.append("- Differentiation opportunities need deeper evidence review.")

    if top_score.overall >= 0.70:
        lines.append("- Duplicate-wheel risk is high; inspect integration or fork paths before starting from scratch.")
    elif top_score.overall >= 0.45:
        lines.append("- Duplicate-wheel risk is moderate; reuse selected modules and build around missing requirements.")
    else:
        lines.append("- Duplicate-wheel risk is low from current evidence; custom implementation remains plausible.")
    return lines


def _default_recommendation(scored_candidates: list[tuple[RepositoryCandidate, ScoreBreakdown]]) -> str:
    top_candidate, top_score = scored_candidates[0]
    if top_score.overall >= 0.70:
        return f"Prefer reuse or fork of `{top_candidate.full_name}` first, then validate gaps with manual review."
    if top_score.overall >= 0.45:
        return f"Use `{top_candidate.full_name}` as a reference or partial integration target, but plan custom work for gaps."
    return "Current candidates do not strongly cover the idea; continue discovery or proceed with a custom build."


def _join_or_unknown(items: tuple[str, ...], limit: int = 5) -> str:
    values = [item for item in items if item]
    if not values:
        return "unknown"
    return ", ".join(values[:limit])


def _cell(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


def _truncate(value: str, limit: int) -> str:
    stripped = value.strip()
    if len(stripped) <= limit:
        return stripped
    return stripped[: limit - 3].rstrip() + "..."
