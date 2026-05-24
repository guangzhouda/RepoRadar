"""Run the local RepoRadar frontend and JSON API server."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.api.local_server import create_server


def build_parser() -> argparse.ArgumentParser:
    """Build CLI arguments for the local frontend server."""

    parser = argparse.ArgumentParser(description="Serve the RepoRadar frontend with a local JSON API.")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host.")
    parser.add_argument("--port", type=int, default=8787, help="Bind port.")
    parser.add_argument("--frontend-dir", default=str(ROOT / "frontend"), help="Directory containing frontend files.")
    return parser


def main() -> int:
    """Start the local server until interrupted."""

    args = build_parser().parse_args()
    server = create_server(host=args.host, port=args.port, frontend_dir=args.frontend_dir)
    host, port = server.server_address
    print(f"RepoRadar frontend: http://{host}:{port}/")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping RepoRadar frontend server.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
