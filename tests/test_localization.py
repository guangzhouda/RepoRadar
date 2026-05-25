import tempfile
import unittest

from app.services.cache import JsonFileCache
from app.services.localization import PayloadLocalizer, TextLocalizer, normalize_display_language


class FakeProvider:
    def __init__(self, response: str) -> None:
        self.response = response
        self.calls: list[str] = []

    def complete(self, prompt: str) -> str:
        self.calls.append(prompt)
        return self.response


class PayloadLocalizerTests(unittest.TestCase):
    def test_normalize_display_language_accepts_zh_and_en_aliases(self):
        self.assertEqual(normalize_display_language("zh-CN"), "zh")
        self.assertEqual(normalize_display_language("english"), "en")
        self.assertIsNone(normalize_display_language("ja"))

    def test_localize_payload_adds_candidate_i18n_fields(self):
        payload = {
            "candidates": [
                {
                    "full_name": "owner/repo",
                    "description": "A curated list of open source repositories.",
                    "rationale": "Matches open source discovery.",
                }
            ]
        }
        provider = FakeProvider(
            """
            {
              "items": [
                {
                  "full_name": "owner/repo",
                  "description": "开源仓库精选列表。",
                  "rationale": "匹配开源发现需求。"
                }
              ]
            }
            """
        )

        with tempfile.TemporaryDirectory() as cache_dir:
            localizer = PayloadLocalizer(provider, JsonFileCache(cache_dir), model_id="test-model")
            localized = localizer.localize_payload(payload, "zh")

        candidate = localized["candidates"][0]
        self.assertEqual(candidate["description_i18n"]["zh"], "开源仓库精选列表。")
        self.assertEqual(candidate["rationale_i18n"]["zh"], "匹配开源发现需求。")
        self.assertEqual(candidate["description"], "A curated list of open source repositories.")
        self.assertEqual(localized["localization_status"], "translated")
        self.assertEqual(len(provider.calls), 1)

    def test_localize_payload_adds_skill_card_i18n_fields(self):
        payload = {
            "candidates": [
                {
                    "full_name": "owner/repo",
                    "description": "A curated list of open source repositories.",
                    "skill_card": {
                        "repo": "owner/repo",
                        "summary": "Finds reusable open source repositories.",
                        "categories": ["repository discovery", "reuse analysis"],
                        "core_capabilities": ["search GitHub candidates", "compare implementation signals"],
                        "input_formats": ["GitHub repository"],
                    },
                }
            ]
        }
        provider = FakeProvider(
            """
            {
              "items": [
                {
                  "full_name": "owner/repo",
                  "description": "开源仓库精选列表。",
                  "skill_card": {
                    "summary": "发现可复用的开源仓库。",
                    "categories": ["仓库发现", "复用分析"],
                    "core_capabilities": ["搜索 GitHub 候选仓库", "比较实现信号"]
                  }
                }
              ]
            }
            """
        )

        with tempfile.TemporaryDirectory() as cache_dir:
            localizer = PayloadLocalizer(provider, JsonFileCache(cache_dir), model_id="test-model")
            localized = localizer.localize_payload(payload, "zh")

        card = localized["candidates"][0]["skill_card"]
        self.assertEqual(card["summary_i18n"]["zh"], "发现可复用的开源仓库。")
        self.assertEqual(card["categories_i18n"]["zh"], ["仓库发现", "复用分析"])
        self.assertEqual(card["core_capabilities_i18n"]["zh"], ["搜索 GitHub 候选仓库", "比较实现信号"])
        self.assertNotIn("input_formats_i18n", card)

    def test_localize_payload_uses_cache_for_same_texts(self):
        payload = {
            "candidates": [
                {
                    "full_name": "owner/repo",
                    "description": "A curated list of open source repositories.",
                }
            ]
        }
        provider = FakeProvider(
            """
            {
              "items": [
                {
                  "full_name": "owner/repo",
                  "description": "开源仓库精选列表。"
                }
              ]
            }
            """
        )

        with tempfile.TemporaryDirectory() as cache_dir:
            cache = JsonFileCache(cache_dir)
            PayloadLocalizer(provider, cache, model_id="test-model").localize_payload(payload, "zh")
            second_payload = {
                "candidates": [
                    {
                        "full_name": "owner/repo",
                        "description": "A curated list of open source repositories.",
                    }
                ]
            }
            PayloadLocalizer(provider, cache, model_id="test-model").localize_payload(second_payload, "zh")

        self.assertEqual(second_payload["candidates"][0]["description_i18n"]["zh"], "开源仓库精选列表。")
        self.assertEqual(len(provider.calls), 1)

    def test_localize_payload_skips_text_already_in_target_language(self):
        payload = {"candidates": [{"full_name": "owner/repo", "description": "中文描述"}]}
        provider = FakeProvider('{"items":[]}')

        with tempfile.TemporaryDirectory() as cache_dir:
            PayloadLocalizer(provider, JsonFileCache(cache_dir), model_id="test-model").localize_payload(payload, "zh")

        self.assertNotIn("description_i18n", payload["candidates"][0])
        self.assertEqual(payload["localization_status"], "not_needed")
        self.assertEqual(provider.calls, [])

    def test_text_localizer_translates_and_caches_one_description(self):
        provider = FakeProvider('{"text":"一个开源仓库发现工具。"}')

        with tempfile.TemporaryDirectory() as cache_dir:
            cache = JsonFileCache(cache_dir)
            first = TextLocalizer(provider, cache, model_id="test-model").localize_text(
                "An open source repository discovery tool.",
                "zh",
                scope="candidate_description",
            )
            second = TextLocalizer(provider, cache, model_id="test-model").localize_text(
                "An open source repository discovery tool.",
                "zh",
                scope="candidate_description",
            )

        self.assertEqual(first["text"], "一个开源仓库发现工具。")
        self.assertEqual(first["status"], "translated")
        self.assertFalse(first["cached"])
        self.assertEqual(second["text"], "一个开源仓库发现工具。")
        self.assertTrue(second["cached"])
        self.assertEqual(len(provider.calls), 1)

    def test_text_localizer_skips_text_already_in_target_language(self):
        provider = FakeProvider('{"text":"unused"}')

        with tempfile.TemporaryDirectory() as cache_dir:
            result = TextLocalizer(provider, JsonFileCache(cache_dir), model_id="test-model").localize_text(
                "中文描述",
                "zh",
                scope="candidate_description",
            )

        self.assertEqual(result["text"], "中文描述")
        self.assertEqual(result["status"], "not_needed")
        self.assertFalse(result["cached"])
        self.assertEqual(provider.calls, [])


if __name__ == "__main__":
    unittest.main()
