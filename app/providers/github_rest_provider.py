"""GitHub REST provider for repository search.

This provider owns HTTP details for GitHub's REST API. Service code should pass
queries in and receive decoded response dictionaries rather than handling URLs,
headers, or HTTP errors directly.
"""

from __future__ import annotations

import json
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class GitHubProviderError(RuntimeError):
    """Raised when the GitHub REST provider cannot complete a request."""


class GitHubRestProvider:
    """Minimal GitHub REST client for repository search."""

    def __init__(
        self,
        token: str = "",
        base_url: str = "https://api.github.com",
        timeout: int = 20,
        opener: Callable[..., object] = urlopen,
    ) -> None:
        self.token = token
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
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
        request = Request(f"{self.base_url}/search/repositories?{params}", headers=self._headers())

        try:
            with self._opener(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            message = exc.read().decode("utf-8", errors="replace")
            raise GitHubProviderError(f"GitHub search failed with HTTP {exc.code}: {message}") from exc
        except URLError as exc:
            raise GitHubProviderError(f"GitHub search failed: {exc.reason}") from exc

        try:
            decoded = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise GitHubProviderError("GitHub search returned invalid JSON") from exc

        if not isinstance(decoded, dict):
            raise GitHubProviderError("GitHub search returned an unexpected response")
        return decoded

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "RepoRadar",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

