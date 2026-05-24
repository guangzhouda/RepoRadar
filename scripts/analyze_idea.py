"""Command-line entry point for RepoRadar idea analysis."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import load_settings
from app.services.idea_analysis import IdeaAnalysisOptions, IdeaAnalysisService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Preview RepoRadar idea analysis.")
    parser.add_argument("--idea", required=True, help="Project idea to analyze.")
    parser.add_argument("--max-repos", type=int, default=10, help="Planned repository limit.")
    parser.add_argument("--max-queries", type=int, default=6, help="Maximum GitHub search queries to generate.")
    parser.add_argument("--format", choices=("json", "markdown"), default="json", help="Output format.")
    parser.add_argument("--output", help="Optional path for writing the full JSON payload.")
    parser.add_argument("--offline", action="store_true", help="Only generate search queries without calling GitHub.")
    parser.add_argument("--no-cache", action="store_true", help="Disable local GitHub search cache.")
    parser.add_argument(
        "--query-mode",
        choices=("llm", "rules"),
        default="llm",
        help="Use LLM query planning by default; rules mode is only a diagnostic fallback.",
    )
    parser.add_argument(
        "--review-mode",
        choices=("llm", "none"),
        default="llm",
        help="Use LLM relevance review by default after GitHub search.",
    )
    parser.add_argument(
        "--extract-cards",
        action="store_true",
        help="Collect README/docs/config files and generate LLM Repo Skill Cards for selected candidates.",
    )
    parser.add_argument("--card-limit", type=int, default=3, help="Maximum candidates to generate skill cards for.")
    parser.add_argument(
        "--card-decision",
        choices=("keep", "all"),
        default="keep",
        help="Generate cards for LLM-kept candidates by default, or all displayed candidates.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    payload = IdeaAnalysisService(load_settings()).analyze(
        IdeaAnalysisOptions(
            idea=args.idea,
            max_repos=args.max_repos,
            max_queries=args.max_queries,
            offline=args.offline,
            no_cache=args.no_cache,
            query_mode=args.query_mode,
            review_mode=args.review_mode,
            extract_cards=args.extract_cards,
            card_limit=args.card_limit,
            card_decision=args.card_decision,
        )
    )
    output = json.dumps(payload, indent=2, ensure_ascii=False)
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")

    if "error" in payload:
        print(output, file=sys.stderr)
    elif args.format == "markdown":
        print(payload["markdown"])
    else:
        print(output)
    return 1 if "error" in payload else 0


if __name__ == "__main__":
    raise SystemExit(main())

