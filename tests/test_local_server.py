import json
from pathlib import Path
import tempfile
import threading
import unittest
from urllib import request

from app.api.local_server import create_server
from app.core.config import Settings


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


class LocalServerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        Path(self.temp_dir.name, "index.html").write_text("<h1>RepoRadar</h1>", encoding="utf-8")
        self.server = create_server(
            host="127.0.0.1",
            port=0,
            frontend_dir=self.temp_dir.name,
            settings_factory=settings_without_credentials,
        )
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        host, port = self.server.server_address
        self.base_url = f"http://{host}:{port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temp_dir.cleanup()

    def test_serves_frontend_index(self):
        response = request.urlopen(f"{self.base_url}/", timeout=5)

        self.assertEqual(response.status, 200)
        self.assertIn("RepoRadar", response.read().decode("utf-8"))

    def test_health_endpoint_returns_configuration_status(self):
        payload = self._get_json("/api/health")

        self.assertTrue(payload["ok"])
        self.assertEqual(payload["cache_dir"], ".reporadar_cache")
        self.assertFalse(payload["llm_key_present"])

    def test_analyze_endpoint_can_run_offline_rules_mode(self):
        payload = self._post_json(
            "/api/analyze",
            {
                "idea": "EPUB PDF TTS subtitles",
                "max_repos": 2,
                "max_queries": 2,
                "offline": True,
                "query_mode": "rules",
                "review_mode": "none",
                "extract_cards": True,
                "card_limit": 1,
                "display_language": "zh",
            },
        )

        self.assertTrue(payload["ok"])
        self.assertEqual(payload["payload"]["review_mode"], "none")
        self.assertEqual(payload["payload"]["card_limit"], 0)
        self.assertIn("queries", payload["payload"])
        self.assertNotIn("localization_error", payload["payload"])

    def test_report_endpoint_returns_markdown(self):
        payload = self._post_json(
            "/api/report",
            {
                "payload": {
                    "idea": "Build an EPUB audiobook tool",
                    "queries": ["epub tts audiobook"],
                    "candidates": [
                        {
                            "full_name": "owner/repo",
                            "url": "https://github.com/owner/repo",
                            "stars": 42,
                            "decision": "keep",
                            "relevance_score": 0.9,
                        }
                    ],
                }
            },
        )

        self.assertTrue(payload["ok"])
        self.assertIn("# RepoRadar Research Report", payload["markdown"])
        self.assertIn("owner/repo", payload["markdown"])

    def _get_json(self, path: str) -> dict:
        response = request.urlopen(f"{self.base_url}{path}", timeout=5)
        return json.loads(response.read().decode("utf-8"))

    def _post_json(self, path: str, payload: dict) -> dict:
        data = json.dumps(payload).encode("utf-8")
        req = request.Request(
            f"{self.base_url}{path}",
            data=data,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        response = request.urlopen(req, timeout=5)
        return json.loads(response.read().decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
