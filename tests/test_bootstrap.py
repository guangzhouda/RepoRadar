import unittest

from app.core.config import load_settings
from app.main import build_config_status
from app.services.query_understanding import build_bootstrap_queries


class BootstrapTests(unittest.TestCase):
    def test_load_settings_uses_defaults(self):
        settings = load_settings({})

        self.assertEqual(settings.github_search_per_page, 10)
        self.assertEqual(settings.llm_provider, "openai")
        self.assertEqual(settings.cache_dir, ".reporadar_cache")

    def test_build_config_status_is_bootstrap_payload(self):
        status = build_config_status()

        self.assertEqual(status["app"], "RepoRadar")
        self.assertEqual(status["phase"], "0-bootstrap")

    def test_bootstrap_queries_include_core_terms(self):
        queries = build_bootstrap_queries("EPUB PDF TTS subtitles", max_queries=2)

        self.assertEqual(len(queries), 2)
        self.assertIn("epub pdf tts subtitles", queries[0])


if __name__ == "__main__":
    unittest.main()
