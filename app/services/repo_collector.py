"""Repository content collection service.

The collector is the stage-2 boundary for fetching repository metadata and a
small, planned set of documentation/configuration files. It depends on the
GitHub provider for transport and leaves capability analysis to the LLM-backed
extractor.
"""

from __future__ import annotations

import base64
from typing import Any

from app.providers.github_rest_provider import GitHubProviderError, GitHubRestProvider
from app.services.cache import JsonFileCache


DEFAULT_REPOSITORY_FILES: tuple[str, ...] = (
    "README.md",
    "README_CN.md",
    "README_zh.md",
    "pyproject.toml",
    "package.json",
    "requirements.txt",
    "Dockerfile",
    "docs/index.md",
    "examples/README.md",
)

class RepositoryCollector:
    """Fetch repository metadata plus the MVP documentation/config files."""

    def __init__(
        self,
        provider: GitHubRestProvider,
        cache: JsonFileCache | None = None,
        use_cache: bool = True,
        file_paths: tuple[str, ...] = DEFAULT_REPOSITORY_FILES,
    ) -> None:
        self.provider = provider
        self.cache = cache
        self.use_cache = use_cache
        self.file_paths = file_paths

    def collect(self, repo_full_name: str) -> dict[str, Any]:
        """Collect repository metadata and selected text files.

        Args:
            repo_full_name: GitHub repository name in ``owner/repo`` format.

        Returns:
            A JSON-serializable dictionary with raw metadata, collected files,
            missing file paths, and skipped file paths.

        Raises:
            GitHubProviderError: For non-404 GitHub API failures.
            ValueError: If the repository name is empty or malformed.
        """

        repo = repo_full_name.strip()
        if not repo:
            raise ValueError("repo_full_name must not be empty")

        cache_key = f"{repo}|{','.join(self.file_paths)}|full"
        if self.cache is not None and self.use_cache:
            cached = self.cache.get("repo_collection", cache_key)
            if cached is not None:
                return cached

        collection: dict[str, Any] = {
            "repo": repo,
            "metadata": self.provider.get_repository(repo),
            "files": {},
            "missing_files": [],
            "skipped_files": [],
        }

        for path in self.file_paths:
            try:
                raw_file = self.provider.get_repository_file(repo, path)
            except GitHubProviderError as exc:
                if exc.status_code == 404:
                    collection["missing_files"].append(path)
                    continue
                raise

            decoded_file = decode_github_text_file(raw_file)
            if decoded_file is None:
                collection["skipped_files"].append(path)
                continue
            collection["files"][path] = decoded_file

        if self.cache is not None and self.use_cache:
            self.cache.set("repo_collection", cache_key, collection)
        return collection


def decode_github_text_file(raw_file: dict[str, object]) -> dict[str, object] | None:
    """Decode a GitHub contents API file response into a text payload.

    Args:
        raw_file: GitHub contents API file response.
    """

    if raw_file.get("type") not in (None, "file"):
        return None

    raw_content = raw_file.get("content")
    if not isinstance(raw_content, str):
        return None

    encoding = str(raw_file.get("encoding") or "").lower()
    if encoding != "base64":
        return None

    try:
        raw_bytes = base64.b64decode(raw_content.encode("ascii"), validate=False)
    except (ValueError, UnicodeEncodeError):
        return None

    content = raw_bytes.decode("utf-8", errors="replace")

    return {
        "path": str(raw_file.get("path") or raw_file.get("name") or ""),
        "name": str(raw_file.get("name") or ""),
        "size": int(raw_file.get("size") or len(raw_bytes)),
        "sha": str(raw_file.get("sha") or ""),
        "html_url": str(raw_file.get("html_url") or ""),
        "download_url": str(raw_file.get("download_url") or ""),
        "content": content,
        "truncated": False,
    }

