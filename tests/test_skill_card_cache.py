"""Tests for cached Repo Skill Card extraction."""

from __future__ import annotations

import tempfile
import unittest

from app.services.cache import JsonFileCache
from app.services.capability_extractor import CapabilityExtractor
from app.services.skill_card_cache import CachedCapabilityExtractor, build_skill_card_cache_key


class FakeLLMProvider:
    def __init__(self, response: str) -> None:
        self.response = response
        self.calls = 0

    def complete(self, prompt: str) -> str:
        self.calls += 1
        return self.response


def collection_with_readme(text: str) -> dict[str, object]:
    return {
        "repo": "owner/repo",
        "metadata": {"full_name": "owner/repo"},
        "files": {"README.md": {"content": text}},
    }


class SkillCardCacheTests(unittest.TestCase):
    def test_cached_extractor_reuses_card_for_same_repo_model_and_collection(self):
        provider = FakeLLMProvider('{"repo": "owner/repo", "name": "repo", "summary": "cached", "confidence": 0.7}')

        with tempfile.TemporaryDirectory() as cache_dir:
            cache = JsonFileCache(cache_dir)
            extractor = CachedCapabilityExtractor(
                CapabilityExtractor(provider),
                cache=cache,
                model_id="model-a",
            )

            first = extractor.extract("owner/repo", collection_with_readme("README"))
            second = extractor.extract("owner/repo", collection_with_readme("README"))

        self.assertEqual(first.summary, "cached")
        self.assertEqual(second.summary, "cached")
        self.assertEqual(provider.calls, 1)

    def test_cache_key_changes_when_collection_changes(self):
        first = build_skill_card_cache_key("owner/repo", collection_with_readme("A"), "model-a")
        second = build_skill_card_cache_key("owner/repo", collection_with_readme("B"), "model-a")

        self.assertNotEqual(first, second)

    def test_cached_extractor_bypasses_cache_when_disabled(self):
        provider = FakeLLMProvider('{"repo": "owner/repo", "name": "repo", "summary": "fresh", "confidence": 0.7}')

        with tempfile.TemporaryDirectory() as cache_dir:
            extractor = CachedCapabilityExtractor(
                CapabilityExtractor(provider),
                cache=JsonFileCache(cache_dir),
                use_cache=False,
                model_id="model-a",
            )
            extractor.extract("owner/repo", collection_with_readme("README"))
            extractor.extract("owner/repo", collection_with_readme("README"))

        self.assertEqual(provider.calls, 2)


if __name__ == "__main__":
    unittest.main()
