"""GitHub REST provider boundary."""


class GitHubRestProvider:
    """Placeholder until GitHub Search API integration is implemented."""

    def search_repositories(self, query: str, per_page: int = 10) -> dict[str, object]:
        raise NotImplementedError("GitHub REST integration belongs to MVP phase 1")

