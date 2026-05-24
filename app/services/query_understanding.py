"""Project idea understanding and GitHub search query generation.

The current implementation is deterministic and dependency-free. It extracts
seed terms from user ideas, including common Chinese product phrases, and turns
them into multiple GitHub repository search queries for phase 1 search.
"""

from __future__ import annotations

import re


_WORD_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_+-]*")
_STOP_TERMS = {
    "a",
    "an",
    "and",
    "build",
    "convert",
    "converts",
    "file",
    "files",
    "for",
    "i",
    "in",
    "into",
    "is",
    "it",
    "of",
    "that",
    "the",
    "to",
    "tool",
    "want",
    "with",
}
_PHRASE_TERMS = (
    ("epub", ("epub",)),
    ("pdf", ("pdf",)),
    ("tts", ("tts", "text-to-speech")),
    ("srt", ("srt", "subtitle")),
    ("字幕", ("subtitle", "srt")),
    ("同步字幕", ("subtitle", "srt")),
    ("音频", ("audio",)),
    ("有声书", ("audiobook",)),
    ("电子书", ("ebook",)),
    ("播客", ("podcast",)),
    ("双人播客", ("podcast", "dialogue")),
    ("网页", ("web",)),
    ("小说", ("novel",)),
    ("游戏", ("game",)),
    ("翻译", ("translation",)),
    ("术语表", ("glossary",)),
    ("格式保留", ("format-preserving",)),
    ("github", ("github", "repository")),
    ("项目发现", ("project-discovery",)),
    ("分类", ("classification",)),
)


def _append_unique(terms: list[str], seen: set[str], values: tuple[str, ...], limit: int) -> None:
    for value in values:
        term = value.lower()
        if len(term) < 2 or term in seen or term in _STOP_TERMS:
            continue
        seen.add(term)
        terms.append(term)
        if len(terms) >= limit:
            return


def extract_seed_terms(idea: str, limit: int = 8) -> list[str]:
    """Extract normalized search seed terms from a project idea.

    Args:
        idea: Natural-language project idea from the user.
        limit: Maximum number of seed terms to return.

    Returns:
        Ordered unique search terms suitable for query generation.

    Raises:
        ValueError: If the idea is empty or only whitespace.
    """

    if not idea.strip():
        raise ValueError("idea must not be empty")

    terms: list[str] = []
    seen: set[str] = set()
    lowered_idea = idea.lower()

    for phrase, mapped_terms in _PHRASE_TERMS:
        if phrase.lower() in lowered_idea:
            _append_unique(terms, seen, mapped_terms, limit)
            if len(terms) >= limit:
                return terms

    for match in _WORD_RE.finditer(idea.lower()):
        term = match.group(0)
        if len(term) < 2 or term in seen or term in _STOP_TERMS:
            continue
        seen.add(term)
        terms.append(term)
        if len(terms) >= limit:
            break
    return terms


def build_search_queries(
    idea: str,
    max_queries: int = 6,
    min_stars: int = 5,
    pushed_after: str = "2025-01-01",
) -> list[str]:
    """Build multiple GitHub repository search queries from an idea.

    The generated queries intentionally combine core capabilities, input/output
    formats, and scenario terms so phase 1 is not dependent on one brittle
    keyword search.
    """

    terms = extract_seed_terms(idea, limit=12)
    core = " ".join(terms[:4])
    filters = f"in:name,description,readme stars:>{min_stars} pushed:>{pushed_after} archived:false fork:false"
    compact_terms = [term for term in terms if term != "text-to-speech"]
    compact_core = " ".join(compact_terms[:3]) or core
    first_format = next((term for term in compact_terms if term in {"epub", "pdf", "ebook", "web", "novel", "game"}), "")
    query_templates = [
        "{compact_core} {filters}",
        "{formats} {capabilities} {filters}",
        "{scenario} {capabilities} {filters}",
        "{first_format} audiobook tts subtitle {filters}",
        "{compact_core} language:Python {filters}",
        "{compact_core} topic:ai {filters}",
        "{compact_core} topic:automation {filters}",
    ]
    formats = " ".join(term for term in compact_terms if term in {"epub", "pdf", "ebook", "web", "novel", "game"}) or compact_core
    capabilities = " ".join(
        term
        for term in compact_terms
        if term
        in {
            "tts",
            "subtitle",
            "srt",
            "audiobook",
            "translation",
            "glossary",
            "podcast",
            "classification",
        }
    ) or compact_core
    scenario = " ".join(term for term in compact_terms if term not in set(formats.split()) and term not in set(capabilities.split())) or compact_core

    queries: list[str] = []
    seen: set[str] = set()
    for template in query_templates:
        query = " ".join(
            template.format(
                core=core,
                compact_core=compact_core,
                first_format=first_format,
                formats=formats,
                capabilities=capabilities,
                scenario=scenario,
                filters=filters,
            ).split()
        )
        if query not in seen:
            seen.add(query)
            queries.append(query)
        if len(queries) >= max_queries:
            break
    return queries


def build_bootstrap_queries(idea: str, max_queries: int = 5) -> list[str]:
    """Backward-compatible alias for the phase 0 preview entry point."""

    return build_search_queries(idea, max_queries=max_queries)
