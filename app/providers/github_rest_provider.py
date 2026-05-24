"""GitHub REST provider for repository search and repository files.

This provider owns HTTP details for GitHub's REST API. Service code should pass
queries in and receive decoded response dictionaries rather than handling URLs,
headers, or HTTP errors directly.
"""

from __future__ import annotations

import json
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen


class GitHubProviderError(RuntimeError):
    """Raised when the GitHub REST provider cannot complete a request."""

    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


class GitHubRestProvider:
    """Minimal GitHub REST client for repository search and content lookup."""

    def __init__(
        self,
        token: str = "",
        base_url: str = "https://api.github.com",
        timeout: int = 20,
        max_retries: int = 2,
        opener: Callable[..., object] = urlopen,
    ) -> None:
        self.token = token
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max(0, max_retries)
        self._opener = opener

    def search_repositories(
        self,
        query: str,
        per_page: int = 10,
        sort: str = "stars",
        order: str = "desc",
    ) -> dict[str, object]:
        """Search GitHub repositories and return the decoded JSON response."""

        if not query.strip():
            raise ValueError("query must not be empty")

        params = urlencode(
            {
                "q": query,
                "per_page": max(1, min(per_page, 100)),
                "sort": sort,
                "order": order,
            }
        )
        return self._get_json(f"{self.base_url}/search/repositories?{params}", "GitHub search")

    def get_repository(self, repo_full_name: str) -> dict[str, object]:
        """Return GitHub repository metadata for an ``owner/name`` repository."""

        owner, repo = self._split_repo_name(repo_full_name)
        endpoint = f"{self.base_url}/repos/{quote(owner, safe='')}/{quote(repo, safe='')}"
        return self._get_json(endpoint, f"GitHub repository lookup for {repo_full_name}")

    def get_repository_file(self, repo_full_name: str, path: str) -> dict[str, object]:
        """Return GitHub contents API metadata for a repository file path."""

        if not path.strip():
            raise ValueError("path must not be empty")

        owner, repo = self._split_repo_name(repo_full_name)
        encoded_path = quote(path.strip().lstrip("/"), safe="/")
        endpoint = f"{self.base_url}/repos/{quote(owner, safe='')}/{quote(repo, safe='')}/contents/{encoded_path}"
        return self._get_json(endpoint, f"GitHub file lookup for {repo_full_name}:{path}")

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "RepoRadar",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _get_json(self, url: str, failure_context: str) -> dict[str, object]:
        raw = self._read_url(url, failure_context)

        try:
            decoded = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise GitHubProviderError(f"{failure_context} returned invalid JSON") from exc

        if not isinstance(decoded, dict):
            raise GitHubProviderError(f"{failure_context} returned an unexpected response")
        return decoded

    def _read_url(self, url: str, failure_context: str) -> str:
        """Read a GitHub API URL, retrying transient transport failures only."""

        attempts = self.max_retries + 1
        for attempt in range(1, attempts + 1):
            request = Request(url, headers=self._headers())
            try:
                with self._opener(request, timeout=self.timeout) as response:
                    return response.read().decode("utf-8")
            except HTTPError as exc:
                try:
                    message = exc.read().decode("utf-8", errors="replace")
                finally:
                    exc.close()
                raise GitHubProviderError(
                    f"{failure_context} failed with HTTP {exc.code}: {message}",
                    exc.code,
                ) from exc
            except URLError as exc:
                if attempt < attempts:
                    continue
                raise GitHubProviderError(
                    f"{failure_context} failed after {attempts} attempts: {exc.reason}"
                ) from exc

        raise GitHubProviderError(f"{failure_context} failed unexpectedly")

    def _split_repo_name(self, repo_full_name: str) -> tuple[str, str]:
        parts = repo_full_name.strip().split("/")
        if len(parts) != 2 or not all(parts):
            raise ValueError("repo_full_name must use owner/repo format")
        return parts[0], parts[1]

