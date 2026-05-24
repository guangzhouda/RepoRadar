"""Shared exception types."""


class RepoRadarError(Exception):
    """Base exception for RepoRadar failures."""


class ConfigurationError(RepoRadarError):
    """Raised when required runtime configuration is invalid or missing."""

