"""Export a Markdown research report from RepoRadar analysis JSON.

The CLI reads the JSON produced by ``scripts/analyze_idea.py`` and converts its
candidates, optional LLM review metadata, and optional skill cards into a
Markdown comparison report.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.report_payload import build_report_from_payload
from app.services.report_generator import ReportGenerator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export a Markdown report from RepoRadar analysis JSON.")
    parser.add_argument("--input", required=True, help="Path to JSON output from scripts/analyze_idea.py.")
    parser.add_argument("--output", help="Optional Markdown output path. Defaults to stdout.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload_path = Path(args.input)

    try:
        payload = json.loads(payload_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("input JSON must be an object")
        report = build_report_from_payload(payload)
        markdown = ReportGenerator().generate_markdown(report)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"export_report error: {exc}", file=sys.stderr)
        return 1

    if args.output:
        Path(args.output).write_text(markdown, encoding="utf-8")
    else:
        print(markdown, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
