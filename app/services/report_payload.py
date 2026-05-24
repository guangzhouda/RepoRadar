"""Helpers for turning analysis payloads into report models.

The CLI exporter and local HTTP API both receive the JSON shape produced by
``IdeaAnalysisService``. This module is the shared conversion boundary from
that JSON payload into ``ResearchReport`` so scripts and API code do not need to
duplicate model-normalization logic.
"""

from __future__ import annotations

from typing import Any

from app.models.report import CandidateAssessment, ResearchReport
from app.models.repo import RepositoryCandidate
from app.models.skill_card import RepoSkillCard


def build_report_from_payload(payload: dict[str, Any]) -> ResearchReport:
    """Build a ``ResearchReport`` from analyze JSON output.

    Args:
        payload: JSON-ready dictionary produced by ``IdeaAnalysisService``.

    Returns:
        A normalized immutable ``ResearchReport`` instance.

    Raises:
        ValueError: If the payload does not contain a candidates list.
    """

    raw_candidates = payload.get("candidates", [])
    if not isinstance(raw_candidates, list):
        raise ValueError("input JSON must include a candidates list")

    candidates: list[RepositoryCandidate] = []
    assessments: list[CandidateAssessment] = []
    skill_cards: list[RepoSkillCard] = []

    for raw_candidate in raw_candidates:
        if not isinstance(raw_candidate, dict):
            continue
        candidates.append(RepositoryCandidate.from_dict(raw_candidate))

        if "relevance_score" in raw_candidate or "decision" in raw_candidate:
            assessments.append(CandidateAssessment.from_dict(raw_candidate))

        raw_card = raw_candidate.get("skill_card")
        if isinstance(raw_card, dict):
            skill_cards.append(RepoSkillCard.from_dict(raw_card))

    raw_queries = payload.get("queries", [])
    queries = tuple(str(query) for query in raw_queries) if isinstance(raw_queries, list) else ()

    return ResearchReport(
        idea=str(payload.get("idea") or ""),
        queries=queries,
        candidates=tuple(candidates),
        skill_cards=tuple(skill_cards),
        assessments=tuple(assessments),
        recommendation=str(payload.get("recommendation") or ""),
    )
