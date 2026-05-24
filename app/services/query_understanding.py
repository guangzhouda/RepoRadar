"""Project idea understanding helpers for the bootstrap CLI preview."""

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


def extract_seed_terms(idea: str, limit: int = 8) -> list[str]:
    if not idea.strip():
        raise ValueError("idea must not be empty")

    terms: list[str] = []
    seen: set[str] = set()
    for match in _WORD_RE.finditer(idea.lower()):
        term = match.group(0)
        if len(term) < 2 or term in seen or term in _STOP_TERMS:
            continue
        seen.add(term)
        terms.append(term)
        if len(terms) >= limit:
            break
    return terms


def build_bootstrap_queries(idea: str, max_queries: int = 5) -> list[str]:
    terms = extract_seed_terms(idea)
    core = " ".join(terms[:4])
    query_templates = [
        "{core} in:name,description,readme",
        "{core} stars:>10",
        "{core} language:Python",
        "{core} topic:ai",
        "{core} topic:automation",
    ]
    return [template.format(core=core) for template in query_templates[:max_queries]]
