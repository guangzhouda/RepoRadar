"""Helpers for parsing strict JSON objects from LLM responses."""

from __future__ import annotations

import json
from typing import Any


def parse_json_object(text: str) -> dict[str, Any]:
    """Parse a JSON object, accepting fenced JSON blocks when providers add them."""

    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    decoded = json.loads(cleaned)
    if not isinstance(decoded, dict):
        raise ValueError("LLM response must be a JSON object")
    return decoded
