"""Compatibility entry point for the frontend MVP.

The current UI is dependency-free static HTML/CSS/JavaScript in
``frontend/index.html`` and connects to the backend through
``scripts/serve_frontend.py``. This module remains as a small pointer for users
who still run the old Streamlit placeholder path.
"""

from __future__ import annotations

from pathlib import Path


def main() -> None:
    """Print the static frontend entry file path."""

    entry = Path(__file__).with_name("index.html")
    print(f"RepoRadar frontend demo: open {entry}")
    print("RepoRadar frontend with backend API: py -3.14 scripts\\serve_frontend.py")


if __name__ == "__main__":
    main()
