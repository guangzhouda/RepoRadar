import unittest

from app.services.github_search import GitHubSearchService, normalize_repository_item


class FakeProvider:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    def search_repositories(self, query, per_page=10):
        self.calls.append((query, per_page))
        return self.responses[query]


class GitHubSearchTests(unittest.TestCase):
    def test_normalize_repository_item_maps_github_fields(self):
        candidate = normalize_repository_item(
            {
                "full_name": "owner/repo",
                "html_url": "https://github.com/owner/repo",
                "description": "Example",
                "stargazers_count": 42,
                "forks_count": 7,
                "language": "Python",
                "license": {"spdx_id": "MIT"},
                "topics": ["tts", "audiobook"],
                "pushed_at": "2026-05-20T00:00:00Z",
                "created_at": "2025-01-01T00:00:00Z",
                "archived": False,
                "fork": False,
            },
            "tts query",
        )

        self.assertEqual(candidate.full_name, "owner/repo")
        self.assertEqual(candidate.stars, 42)
        self.assertEqual(candidate.license, "MIT")
        self.assertEqual(candidate.topics, ("tts", "audiobook"))
        self.assertEqual(candidate.source_queries, ("tts query",))

    def test_search_many_deduplicates_filters_and_sorts_candidates(self):
        responses = {
            "query one": {
                "items": [
                    {"full_name": "a/low", "html_url": "https://github.com/a/low", "stargazers_count": 5},
                    {"full_name": "b/high", "html_url": "https://github.com/b/high", "stargazers_count": 100},
                    {"full_name": "c/archive", "html_url": "https://github.com/c/archive", "stargazers_count": 200, "archived": True},
                ]
            },
            "query two": {
                "items": [
                    {"full_name": "a/low", "html_url": "https://github.com/a/low", "stargazers_count": 10},
                    {"full_name": "d/fork", "html_url": "https://github.com/d/fork", "stargazers_count": 300, "fork": True},
                ]
            },
        }
        service = GitHubSearchService(provider=FakeProvider(responses), cache=None)

        candidates = service.search_many(["query one", "query two"], max_repos=10)

        self.assertEqual([candidate.full_name for candidate in candidates], ["b/high", "a/low"])
        self.assertEqual(candidates[1].stars, 10)
        self.assertEqual(candidates[1].source_queries, ("query one", "query two"))


if __name__ == "__main__":
    unittest.main()
