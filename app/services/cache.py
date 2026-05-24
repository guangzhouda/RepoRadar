"""Small JSON cache helpers for service-layer API responses.

The cache is intentionally simple and dependency-free. GitHub search uses it to
avoid repeated API calls while keeping cache mechanics out of provider code.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


class JsonFileCache:
    """File-backed JSON cache keyed by stable strings."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def _path_for_key(self, namespace: str, key: str) -> Path:
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self.root / namespace / f"{digest}.json"

    def get(self, namespace: str, key: str) -> dict[str, Any] | None:
        """Return cached JSON data, or None if the cache entry is missing."""

        path = self._path_for_key(namespace, key)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def set(self, namespace: str, key: str, data: dict[str, Any]) -> None:
        """Persist JSON data for a namespace/key pair."""

        path = self._path_for_key(namespace, key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
