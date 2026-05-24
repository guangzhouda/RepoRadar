"""Skill-card extraction cache service.

This module keeps LLM-generated Repo Skill Cards out of the hot path when the
same repository content and model are analyzed repeatedly. It wraps the
capability extractor while leaving collection, prompting, and CLI output in
their existing modules.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from app.models.skill_card import RepoSkillCard
from app.services.cache import JsonFileCache
from app.services.capability_extractor import CapabilityExtractor


SKILL_CARD_CACHE_VERSION = "repo-skill-card-v1"


class CachedCapabilityExtractor:
    """Cache wrapper around LLM-backed Repo Skill Card extraction.

    The cache key includes repository name, model identifier, and a fingerprint
    of the collected repository content so stale cards are not reused after
    evidence changes.
    """

    def __init__(
        self,
        extractor: CapabilityExtractor,
        cache: JsonFileCache | None,
        use_cache: bool = True,
        model_id: str = "",
    ) -> None:
        self.extractor = extractor
        self.cache = cache
        self.use_cache = use_cache
        self.model_id = model_id

    def extract(self, repo_full_name: str, collection: dict[str, Any]) -> RepoSkillCard:
        """Return a cached or freshly extracted skill card for one repository."""

        cache_key = build_skill_card_cache_key(repo_full_name, collection, self.model_id)
        if self.cache is not None and self.use_cache:
            cached = self.cache.get("skill_card", cache_key)
            if cached is not None:
                return RepoSkillCard.from_dict(cached)

        card = self.extractor.extract(repo_full_name, collection)
        if self.cache is not None and self.use_cache:
            self.cache.set("skill_card", cache_key, card.to_dict())
        return card


def build_skill_card_cache_key(repo_full_name: str, collection: dict[str, Any], model_id: str = "") -> str:
    """Return a stable cache key for a repo/model/content combination."""

    fingerprint = hashlib.sha256(
        json.dumps(collection, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()
    return "|".join(
        [
            SKILL_CARD_CACHE_VERSION,
            repo_full_name.strip(),
            model_id.strip(),
            fingerprint,
        ]
    )
