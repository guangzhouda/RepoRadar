"""Bootstrap command for analyzing a project idea.

At phase 0 this command only normalizes the input and previews seed GitHub
queries. It intentionally does not call GitHub or an LLM yet.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.query_understanding import build_bootstrap_queries


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Preview RepoRadar idea analysis.")
    parser.add_argument("--idea", required=True, help="Project idea to analyze.")
    parser.add_argument("--max-repos", type=int, default=10, help="Planned repository limit.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    payload = {
        "phase": "0-bootstrap",
        "idea": args.idea.strip(),
        "max_repos": args.max_repos,
        "status": "GitHub and LLM integrations are not implemented yet.",
        "seed_queries": build_bootstrap_queries(args.idea),
    }
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

