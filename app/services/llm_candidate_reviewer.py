"""LLM-backed relevance review for GitHub repository candidates.

The reviewer asks an LLM to score and explain candidates after GitHub search.
This keeps semantic filtering out of local keyword rules while still preserving
deterministic metadata filtering for archived and forked repositories.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

from app.models.repo import RepositoryCandidate
from app.providers.llm_base import LLMProvider
from app.services.llm_json import parse_json_object


@dataclass(frozen=True)
class CandidateReview:
    """LLM relevance judgment for one repository candidate."""

    full_name: str
    relevance_score: float
    decision: str
    reject_reason: str = ""
    rationale: str = ""


class LLMCandidateReviewer:
    """Review candidates semantically with an LLM."""

    def __init__(self, provider: LLMProvider, batch_size: int = 5) -> None:
        self.provider = provider
        self.batch_size = max(1, batch_size)

    def review(self, idea: str, candidates: list[RepositoryCandidate]) -> dict[str, CandidateReview]:
        """Return LLM review results keyed by repository full name."""

        if not candidates:
            return {}

        reviews: dict[str, CandidateReview] = {}
        for batch in _batches(candidates, self.batch_size):
            try:
                reviews.update(self._review_batch(idea, batch))
            except (RuntimeError, ValueError) as exc:
                for candidate in batch:
                    reviews[candidate.full_name] = CandidateReview(
                        full_name=candidate.full_name,
                        relevance_score=0.0,
                        decision="reject",
                        reject_reason=f"LLM review batch failed: {exc}",
                        rationale="",
                    )
        return reviews

    def _review_batch(self, idea: str, candidates: list[RepositoryCandidate]) -> dict[str, CandidateReview]:
        """Return LLM review results for one bounded candidate batch."""

        prompt = f"""
你是 RepoRadar 的候选 GitHub 仓库相关性评审器。

目标：根据用户 idea 判断每个候选 repo 是否是真正相关的工具项目。

要求：
- 只返回严格 JSON，不要解释。
- JSON schema:
  {{"candidates": [
    {{"full_name": "...", "relevance_score": 0.0, "decision": "keep|reject", "reject_reason": "...", "rationale": "..."}}
  ]}}
- relevance_score 范围是 0 到 1。
- 如果 repo 是 awesome list、资源集合、newsletter、daily 推荐、索引页，而不是实际工具，应 decision=reject。
- 如果 repo 明显实现或接近实现用户需要的输入/输出/能力，应 decision=keep。
- 不要因为 stars 很高就认为相关。
- rationale 和 reject_reason 要简短。

用户 idea:
{idea}

候选 repositories:
{json.dumps([candidate.to_dict() for candidate in candidates], ensure_ascii=False, indent=2)}
""".strip()
        response = parse_json_object(self.provider.complete(prompt))
        raw_reviews = response.get("candidates", [])
        if not isinstance(raw_reviews, list):
            raise ValueError("LLM review response must include a candidates list")

        reviews: dict[str, CandidateReview] = {}
        for raw_review in raw_reviews:
            if not isinstance(raw_review, dict):
                continue
            full_name = str(raw_review.get("full_name") or "")
            if not full_name:
                continue
            reviews[full_name] = CandidateReview(
                full_name=full_name,
                relevance_score=_clamp_score(raw_review.get("relevance_score")),
                decision=str(raw_review.get("decision") or "reject"),
                reject_reason=str(raw_review.get("reject_reason") or ""),
                rationale=str(raw_review.get("rationale") or ""),
            )
        return reviews

    def apply_reviews(
        self,
        candidates: list[RepositoryCandidate],
        reviews: dict[str, CandidateReview],
        limit: int,
    ) -> list[dict[str, object]]:
        """Merge LLM review fields into candidate dictionaries and sort by relevance."""

        enriched: list[dict[str, object]] = []
        for candidate in candidates:
            candidate_dict = candidate.to_dict()
            review = reviews.get(candidate.full_name)
            if review is None:
                candidate_dict.update(
                    {
                        "relevance_score": 0.0,
                        "decision": "reject",
                        "reject_reason": "LLM did not review this candidate",
                        "rationale": "",
                    }
                )
            else:
                candidate_dict.update(
                    {
                        "relevance_score": review.relevance_score,
                        "decision": review.decision,
                        "reject_reason": review.reject_reason,
                        "rationale": review.rationale,
                    }
                )
            enriched.append(candidate_dict)

        enriched.sort(
            key=lambda item: (
                item.get("decision") == "keep",
                float(item.get("relevance_score") or 0.0),
                int(item.get("stars") or 0),
            ),
            reverse=True,
        )
        return enriched[:limit]


def _clamp_score(raw_score: object) -> float:
    try:
        score = float(raw_score)
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, score))


def _batches(candidates: list[RepositoryCandidate], batch_size: int) -> list[list[RepositoryCandidate]]:
    return [candidates[index : index + batch_size] for index in range(0, len(candidates), batch_size)]
