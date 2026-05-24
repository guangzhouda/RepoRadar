"""Reuse/build recommendation helpers for reports.

The advisor converts scored candidates and optional skill cards into concise
decision text. Markdown rendering stays in ``report_generator``.
"""

from __future__ import annotations

from app.models.repo import RepositoryCandidate
from app.models.skill_card import RepoSkillCard
from app.services.scoring import ScoreBreakdown


def build_reuse_analysis(
    scored_candidates: list[tuple[RepositoryCandidate, ScoreBreakdown]],
    skill_cards: dict[str, RepoSkillCard],
) -> list[str]:
    """Return reuse/build analysis bullets for the top scored candidate."""

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


def build_default_recommendation(scored_candidates: list[tuple[RepositoryCandidate, ScoreBreakdown]]) -> str:
    """Return the default final recommendation for scored candidates."""

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
