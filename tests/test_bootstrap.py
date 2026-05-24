import unittest
from tempfile import TemporaryDirectory
from pathlib import Path

from app.core.config import load_settings, read_env_file
from app.main import build_config_status
from app.services.query_understanding import build_bootstrap_queries


class BootstrapTests(unittest.TestCase):
    def test_load_settings_uses_defaults(self):
        settings = load_settings({})

        self.assertEqual(settings.github_api_base_url, "https://api.github.com")
        self.assertEqual(settings.github_search_per_page, 10)
        self.assertEqual(settings.llm_provider, "deepseek")
        self.assertEqual(settings.llm_base_url, "")
        self.assertEqual(settings.llm_model, "")
        self.assertEqual(settings.cache_dir, ".reporadar_cache")

    def test_build_config_status_is_bootstrap_payload(self):
        status = build_config_status()

        self.assertEqual(status["app"], "RepoRadar")
        self.assertEqual(status["phase"], "1-cli-search")

    def test_read_env_file_supports_llm_base_url_and_model(self):
        with TemporaryDirectory() as directory:
            env_file = Path(directory) / ".env"
            env_file.write_text(
                "\n".join(
                    [
                        "LLM_PROVIDER=deepseek",
                        "LLM_API_KEY='secret'",
                        "LLM_BASE_URL=https://api.deepseek.com",
                        'LLM_MODEL="deepseek-v4-pro"',
                    ]
                ),
                encoding="utf-8",
            )

            parsed = read_env_file(env_file)

        self.assertEqual(parsed["LLM_PROVIDER"], "deepseek")
        self.assertEqual(parsed["LLM_API_KEY"], "secret")
        self.assertEqual(parsed["LLM_BASE_URL"], "https://api.deepseek.com")
        self.assertEqual(parsed["LLM_MODEL"], "deepseek-v4-pro")

    def test_bootstrap_queries_include_core_terms(self):
        queries = build_bootstrap_queries("EPUB PDF TTS subtitles", max_queries=2)

        self.assertEqual(len(queries), 2)
        self.assertIn("epub pdf tts", queries[0])
        self.assertIn("in:name,description,readme", queries[0])


if __name__ == "__main__":
    unittest.main()
