"""Direct tests for GitHub REST transport behavior.

The search service covers provider integration indirectly; these tests pin the
provider's URL construction, headers, decoding, and retry/error boundaries.
"""

import io
import json
import unittest
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse

from app.providers.github_rest_provider import GitHubProviderError, GitHubRestProvider


class FakeResponse:
    def __init__(self, body):
        self.body = body

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self):
        return self.body.encode("utf-8")


class RecordingOpener:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = []

    def __call__(self, request, timeout):
        self.calls.append((request, timeout))
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return FakeResponse(outcome)


def http_error(url, code=404, body='{"message": "not found"}'):
    return HTTPError(url=url, code=code, msg="Not Found", hdrs=None, fp=io.BytesIO(body.encode("utf-8")))


class GitHubRestProviderTests(unittest.TestCase):
    def test_search_repositories_builds_search_url_and_headers(self):
        opener = RecordingOpener([json.dumps({"items": []})])
        provider = GitHubRestProvider(token="token", base_url="https://example.test", opener=opener)

        response = provider.search_repositories("epub tts", per_page=250)

        self.assertEqual(response, {"items": []})
        request, timeout = opener.calls[0]
        parsed = urlparse(request.full_url)
        query = parse_qs(parsed.query)
        self.assertEqual(parsed.path, "/search/repositories")
        self.assertEqual(query["q"], ["epub tts"])
        self.assertEqual(query["per_page"], ["100"])
        self.assertEqual(timeout, 20)
        self.assertEqual(request.headers["Authorization"], "Bearer token")

    def test_get_repository_builds_repo_endpoint(self):
        opener = RecordingOpener([json.dumps({"full_name": "owner/repo"})])
        provider = GitHubRestProvider(base_url="https://example.test", opener=opener)

        provider.get_repository("owner/repo")

        request, _timeout = opener.calls[0]
        self.assertEqual(request.full_url, "https://example.test/repos/owner/repo")

    def test_get_repository_file_encodes_path_segments(self):
        opener = RecordingOpener([json.dumps({"path": "docs/read me.md"})])
        provider = GitHubRestProvider(base_url="https://example.test", opener=opener)

        provider.get_repository_file("owner/repo", "docs/read me.md")

        request, _timeout = opener.calls[0]
        self.assertEqual(request.full_url, "https://example.test/repos/owner/repo/contents/docs/read%20me.md")

    def test_invalid_repo_name_raises_value_error(self):
        provider = GitHubRestProvider(opener=RecordingOpener([]))

        with self.assertRaises(ValueError):
            provider.get_repository("owner/repo/extra")

    def test_http_error_preserves_status_code_and_does_not_retry(self):
        opener = RecordingOpener([http_error("https://example.test/repos/owner/repo")])
        provider = GitHubRestProvider(base_url="https://example.test", max_retries=3, opener=opener)

        with self.assertRaises(GitHubProviderError) as context:
            provider.get_repository("owner/repo")

        self.assertEqual(context.exception.status_code, 404)
        self.assertIn("HTTP 404", str(context.exception))
        self.assertEqual(len(opener.calls), 1)

    def test_invalid_json_raises_provider_error(self):
        opener = RecordingOpener(["not json"])
        provider = GitHubRestProvider(base_url="https://example.test", opener=opener)

        with self.assertRaises(GitHubProviderError) as context:
            provider.search_repositories("epub tts")

        self.assertIn("invalid JSON", str(context.exception))

    def test_url_error_retries_then_succeeds(self):
        opener = RecordingOpener([URLError("temporary ssl eof"), json.dumps({"items": []})])
        provider = GitHubRestProvider(base_url="https://example.test", max_retries=2, opener=opener)

        response = provider.search_repositories("epub tts")

        self.assertEqual(response, {"items": []})
        self.assertEqual(len(opener.calls), 2)

    def test_url_error_fails_after_retry_budget(self):
        opener = RecordingOpener([URLError("temporary ssl eof"), URLError("temporary ssl eof")])
        provider = GitHubRestProvider(base_url="https://example.test", max_retries=1, opener=opener)

        with self.assertRaises(GitHubProviderError) as context:
            provider.search_repositories("epub tts")

        self.assertIn("failed after 2 attempts", str(context.exception))
        self.assertEqual(len(opener.calls), 2)


if __name__ == "__main__":
    unittest.main()
