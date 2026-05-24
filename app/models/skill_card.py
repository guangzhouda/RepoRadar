"""Repo Skill Card data structures.

This module is the schema boundary between LLM capability extraction and the
rest of RepoRadar. Extractors produce these immutable objects; CLI and report
code serialize them through ``to_dict``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


def _string_tuple(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        stripped = value.strip()
        return (stripped,) if stripped else ()
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(str(item).strip() for item in value if str(item).strip())


def _float_value(value: object, default: float = 0.0) -> float:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return max(0.0, min(parsed, 1.0))


@dataclass(frozen=True)
class Evidence:
    """Evidence snippet that supports a capability claim in a skill card."""

    source: str
    quote: str
    confidence: float = 0.0

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable evidence representation."""

        return {
            "source": self.source,
            "quote": self.quote,
            "confidence": self.confidence,
        }

    @classmethod
    def from_dict(cls, data: object) -> "Evidence":
        """Create an evidence item from LLM JSON while tolerating missing keys."""

        if not isinstance(data, dict):
            return cls(source="", quote="", confidence=0.0)
        return cls(
            source=str(data.get("source") or "").strip(),
            quote=str(data.get("quote") or data.get("text") or "").strip(),
            confidence=_float_value(data.get("confidence"), 0.0),
        )


@dataclass(frozen=True)
class RepoSkillCard:
    """Structured capability summary for one GitHub repository.

    The card represents what RepoRadar can assert from repository metadata,
    README/docs/config files, and evidence snippets. It is intentionally plain
    dataclasses so the MVP stays dependency-free.
    """

    repo: str
    name: str
    summary: str = ""
    categories: tuple[str, ...] = field(default_factory=tuple)
    input_formats: tuple[str, ...] = field(default_factory=tuple)
    output_formats: tuple[str, ...] = field(default_factory=tuple)
    interfaces: tuple[str, ...] = field(default_factory=tuple)
    core_capabilities: tuple[str, ...] = field(default_factory=tuple)
    optional_capabilities: tuple[str, ...] = field(default_factory=tuple)
    claimed_but_unverified_capabilities: tuple[str, ...] = field(default_factory=tuple)
    model_providers: tuple[str, ...] = field(default_factory=tuple)
    deployment: tuple[str, ...] = field(default_factory=tuple)
    suitable_for: tuple[str, ...] = field(default_factory=tuple)
    not_supported: tuple[str, ...] = field(default_factory=tuple)
    limitations: tuple[str, ...] = field(default_factory=tuple)
    evidence: tuple[Evidence, ...] = field(default_factory=tuple)
    confidence: float = 0.0

    def to_dict(self) -> dict[str, object]:
        """Return a JSON-serializable skill card representation."""

        return {
            "repo": self.repo,
            "name": self.name,
            "summary": self.summary,
            "categories": list(self.categories),
            "input_formats": list(self.input_formats),
            "output_formats": list(self.output_formats),
            "interfaces": list(self.interfaces),
            "core_capabilities": list(self.core_capabilities),
            "optional_capabilities": list(self.optional_capabilities),
            "claimed_but_unverified_capabilities": list(self.claimed_but_unverified_capabilities),
            "model_providers": list(self.model_providers),
            "deployment": list(self.deployment),
            "suitable_for": list(self.suitable_for),
            "not_supported": list(self.not_supported),
            "limitations": list(self.limitations),
            "evidence": [item.to_dict() for item in self.evidence],
            "confidence": self.confidence,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RepoSkillCard":
        """Create a skill card from strict LLM JSON output."""

        evidence_items = data.get("evidence", [])
        if not isinstance(evidence_items, list):
            evidence_items = []

        repo = str(data.get("repo") or "").strip()
        name = str(data.get("name") or "").strip()
        if not name and repo:
            name = repo.split("/", 1)[-1]

        claimed = data.get("claimed_but_unverified_capabilities")
        if claimed is None:
            claimed = data.get("claimed_but_unverified")

        return cls(
            repo=repo,
            name=name,
            summary=str(data.get("summary") or "").strip(),
            categories=_string_tuple(data.get("categories")),
            input_formats=_string_tuple(data.get("input_formats")),
            output_formats=_string_tuple(data.get("output_formats")),
            interfaces=_string_tuple(data.get("interfaces")),
            core_capabilities=_string_tuple(data.get("core_capabilities")),
            optional_capabilities=_string_tuple(data.get("optional_capabilities")),
            claimed_but_unverified_capabilities=_string_tuple(claimed),
            model_providers=_string_tuple(data.get("model_providers")),
            deployment=_string_tuple(data.get("deployment")),
            suitable_for=_string_tuple(data.get("suitable_for")),
            not_supported=_string_tuple(data.get("not_supported")),
            limitations=_string_tuple(data.get("limitations")),
            evidence=tuple(
                item for item in (Evidence.from_dict(raw_item) for raw_item in evidence_items) if item.source or item.quote
            ),
            confidence=_float_value(data.get("confidence"), 0.0),
        )

