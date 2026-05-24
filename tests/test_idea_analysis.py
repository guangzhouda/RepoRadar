import unittest

from app.core.config import Settings
from app.services.idea_analysis import IdeaAnalysisOptions, IdeaAnalysisService, build_candidate_markdown


def settings_without_credentials() -> Settings:
    return Settings(
        github_token="",
        github_api_base_url="https://api.github.com",
        github_search_per_page=10,
        llm_provider="deepseek",
        llm_api_key="",
        llm_base_url="",
        llm_model="",
        cache_dir=".reporadar_cache",
        log_level="INFO",
    )


class IdeaAnalysisTests(unittest.TestCase):
    def test_offline_rules_analysis_returns_payload_without_external_calls(self):
        payload = IdeaAnalysisService(settings_without_credentials()).analyze(
            IdeaAnalysisOptions(
                idea="EPUB PDF TTS subtitles",
                max_repos=2,
                max_queries=2,
                offline=True,
                no_cache=True,
                query_mode="rules",
                review_mode="llm",
                extract_cards=True,
                card_limit=1,
                card_decision="keep",
            )
        )

        self.assertEqual(payload["phase"], "1-cli-search")
        self.assertEqual(payload["review_mode"], "none")
        self.assertFalse(payload["extract_cards"])
        self.assertEqual(payload["card_limit"], 0)
        self.assertEqual(payload["candidates"], [])
        self.assertIn("queries", payload)
        self.assertIn("markdown", payload)

    def test_candidate_markdown_preserves_reject_candidates(self):
        markdown = build_candidate_markdown(
            "project idea",
            [
                {
                    "full_name": "owner/repo",
                    "url": "https://github.com/owner/repo",
                    "stars": 10,
                    "forks": 1,
                    "language": "Python",
                    "description": "Example",
                    "relevance_score": 0.2,
                    "decision": "reject",
                    "reject_reason": "not a tool",
                }
            ],
        )

        self.assertIn("owner/repo", markdown)
        self.assertIn("Decision: reject", markdown)
        self.assertIn("Reject reason: not a tool", markdown)


if __name__ == "__main__":
    unittest.main()
