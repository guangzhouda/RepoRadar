"""Repository content collection boundary."""


class RepositoryCollector:
    """Placeholder for README, docs, and metadata fetching."""

    def collect(self, repo_full_name: str) -> dict[str, str]:
        raise NotImplementedError("Repository collection belongs to MVP phase 2")

