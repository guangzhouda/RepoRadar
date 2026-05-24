import base64
import unittest

from app.providers.github_rest_provider import GitHubProviderError
from app.services.repo_collector import RepositoryCollector, decode_github_text_file


def encoded_file(path, content):
    return {
        "type": "file",
        "path": path,
        "name": path.rsplit("/", 1)[-1],
        "size": len(content.encode("utf-8")),
        "sha": "abc123",
        "encoding": "base64",
        "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
        "html_url": f"https://github.com/owner/repo/blob/main/{path}",
        "download_url": f"https://raw.githubusercontent.com/owner/repo/main/{path}",
    }


class FakeGitHubProvider:
    def __init__(self):
        self.requested_files = []

    def get_repository(self, repo_full_name):
        return {
            "full_name": repo_full_name,
            "description": "Example repository",
            "html_url": f"https://github.com/{repo_full_name}",
        }

    def get_repository_file(self, repo_full_name, path):
        self.requested_files.append((repo_full_name, path))
        if path == "README.md":
            return encoded_file(path, "Repo README content")
        raise GitHubProviderError("missing", status_code=404)


class RepositoryCollectorTests(unittest.TestCase):
    def test_decode_github_text_file_returns_full_text_by_default(self):
        decoded = decode_github_text_file(encoded_file("README.md", "abcdef"))

        self.assertEqual(decoded["content"], "abcdef")
        self.assertFalse(decoded["truncated"])
        self.assertEqual(decoded["path"], "README.md")

    def test_collect_fetches_metadata_files_and_records_missing_paths(self):
        provider = FakeGitHubProvider()
        collector = RepositoryCollector(
            provider=provider,
            file_paths=("README.md", "package.json"),
            cache=None,
        )

        collection = collector.collect("owner/repo")

        self.assertEqual(collection["repo"], "owner/repo")
        self.assertEqual(collection["metadata"]["full_name"], "owner/repo")
        self.assertEqual(collection["files"]["README.md"]["content"], "Repo README content")
        self.assertEqual(collection["missing_files"], ["package.json"])
        self.assertEqual(provider.requested_files, [("owner/repo", "README.md"), ("owner/repo", "package.json")])


if __name__ == "__main__":
    unittest.main()
