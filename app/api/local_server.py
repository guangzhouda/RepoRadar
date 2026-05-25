"""Dependency-free local HTTP server for the RepoRadar frontend.

The server is intentionally small and standard-library only. It serves the
static files in ``frontend/`` and exposes JSON endpoints that call the existing
service layer:

- ``GET /api/health``
- ``POST /api/analyze``
- ``POST /api/localize``
- ``POST /api/report``

It is meant for local MVP usage, not as a production web server.
"""

from __future__ import annotations

from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import mimetypes
from pathlib import Path
from typing import Any, Callable
from urllib.parse import unquote, urlparse

from app.core.config import Settings, load_settings
from app.providers.openai_provider import LLMProviderError, OpenAIProvider
from app.services.cache import JsonFileCache
from app.services.idea_analysis import IdeaAnalysisOptions, IdeaAnalysisService
from app.services.localization import PayloadLocalizer, TextLocalizer, normalize_display_language
from app.services.report_generator import ReportGenerator
from app.services.report_payload import build_report_from_payload


SettingsFactory = Callable[[], Settings]


def create_server(
    host: str = "127.0.0.1",
    port: int = 8787,
    frontend_dir: str | Path | None = None,
    settings_factory: SettingsFactory = load_settings,
) -> ThreadingHTTPServer:
    """Create a configured local HTTP server.

    Args:
        host: Interface to bind.
        port: Port to bind. Use ``0`` in tests for an ephemeral port.
        frontend_dir: Directory containing ``index.html`` and static assets.
        settings_factory: Callable used to load runtime settings per request.

    Returns:
        A ``ThreadingHTTPServer`` ready for ``serve_forever``.
    """

    root = Path(__file__).resolve().parents[2]
    static_dir = Path(frontend_dir) if frontend_dir is not None else root / "frontend"
    handler = _make_handler(static_dir.resolve(), settings_factory)
    return ThreadingHTTPServer((host, port), handler)


def _make_handler(frontend_dir: Path, settings_factory: SettingsFactory) -> type[BaseHTTPRequestHandler]:
    class RepoRadarLocalHandler(BaseHTTPRequestHandler):
        server_version = "RepoRadarLocal/0.1"

        def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
            parsed = urlparse(self.path)
            if parsed.path == "/api/health":
                self._write_json(_health_payload(settings_factory()))
                return
            if parsed.path.startswith("/api/"):
                self._write_json({"ok": False, "error": "unknown API endpoint"}, HTTPStatus.NOT_FOUND)
                return
            self._serve_static(parsed.path)

        def do_POST(self) -> None:  # noqa: N802 - stdlib handler API
            parsed = urlparse(self.path)
            try:
                body = self._read_json_body()
                if parsed.path == "/api/analyze":
                    self._handle_analyze(body)
                    return
                if parsed.path == "/api/localize":
                    self._handle_localize(body)
                    return
                if parsed.path == "/api/report":
                    self._handle_report(body)
                    return
                self._write_json({"ok": False, "error": "unknown API endpoint"}, HTTPStatus.NOT_FOUND)
            except (ValueError, json.JSONDecodeError) as exc:
                self._write_json({"ok": False, "error": str(exc)}, HTTPStatus.BAD_REQUEST)

        def log_message(self, format: str, *args: object) -> None:
            """Keep local server output quiet during tests and normal use."""

        def _handle_analyze(self, body: dict[str, Any]) -> None:
            idea = str(body.get("idea") or "").strip()
            if not idea:
                raise ValueError("idea is required")

            options = IdeaAnalysisOptions(
                idea=idea,
                max_repos=_int_option(body, "max_repos", 5, minimum=1, maximum=50),
                max_queries=_int_option(body, "max_queries", 6, minimum=1, maximum=20),
                offline=bool(body.get("offline", False)),
                no_cache=bool(body.get("no_cache", False)),
                query_mode=_choice_option(body, "query_mode", "llm", {"llm", "rules"}),
                review_mode=_choice_option(body, "review_mode", "llm", {"llm", "none"}),
                extract_cards=bool(body.get("extract_cards", False)),
                card_limit=_int_option(body, "card_limit", 1, minimum=0, maximum=20),
                card_decision=_choice_option(body, "card_decision", "keep", {"keep", "all"}),
            )
            settings = settings_factory()
            payload = IdeaAnalysisService(settings).analyze(options)
            _localize_for_display(payload, settings, body)
            self._write_json({"ok": "error" not in payload, "payload": payload, "error": payload.get("error", "")})

        def _handle_report(self, body: dict[str, Any]) -> None:
            raw_payload = body.get("payload", body)
            if not isinstance(raw_payload, dict):
                raise ValueError("payload must be an object")
            report = build_report_from_payload(raw_payload)
            markdown = ReportGenerator().generate_markdown(report)
            self._write_json({"ok": True, "markdown": markdown})

        def _handle_localize(self, body: dict[str, Any]) -> None:
            text = str(body.get("text") or "").strip()
            if not text:
                raise ValueError("text is required")
            language = normalize_display_language(str(body.get("target_language") or ""))
            if language is None:
                raise ValueError("target_language must be zh or en")

            settings = settings_factory()
            if not (settings.llm_api_key and settings.llm_base_url and settings.llm_model):
                self._write_json({"ok": False, "error": "LLM is not configured"})
                return

            provider = OpenAIProvider(
                api_key=settings.llm_api_key,
                base_url=settings.llm_base_url,
                model=settings.llm_model,
            )
            scope = str(body.get("scope") or "display_text").strip() or "display_text"
            localizer = TextLocalizer(provider, cache=JsonFileCache(settings.cache_dir), model_id=settings.llm_model)
            try:
                localized = localizer.localize_text(text, language, scope=scope)
            except (LLMProviderError, ValueError) as exc:
                self._write_json({"ok": False, "error": str(exc)})
                return
            self._write_json({"ok": True, **localized, "target_language": language})

        def _read_json_body(self) -> dict[str, Any]:
            content_length = int(self.headers.get("Content-Length", "0") or "0")
            raw = self.rfile.read(content_length)
            if not raw:
                return {}
            parsed = json.loads(raw.decode("utf-8"))
            if not isinstance(parsed, dict):
                raise ValueError("request body must be a JSON object")
            return parsed

        def _serve_static(self, request_path: str) -> None:
            relative = "index.html" if request_path in {"", "/"} else unquote(request_path.lstrip("/"))
            candidate = (frontend_dir / relative).resolve()

            try:
                candidate.relative_to(frontend_dir)
            except ValueError:
                self._write_json({"ok": False, "error": "invalid static path"}, HTTPStatus.FORBIDDEN)
                return

            if candidate.is_dir():
                candidate = candidate / "index.html"
            if not candidate.exists() or not candidate.is_file():
                self._write_json({"ok": False, "error": "file not found"}, HTTPStatus.NOT_FOUND)
                return

            mime_type, _encoding = mimetypes.guess_type(str(candidate))
            body = candidate.read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", f"{mime_type or 'application/octet-stream'}; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _write_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return RepoRadarLocalHandler


def _health_payload(settings: Settings) -> dict[str, Any]:
    return {
        "ok": True,
        "github_configured": bool(settings.github_api_base_url),
        "github_token_present": bool(settings.github_token),
        "llm_configured": bool(settings.llm_base_url and settings.llm_model),
        "llm_key_present": bool(settings.llm_api_key),
        "cache_dir": settings.cache_dir,
        "log_level": settings.log_level,
    }


def _localize_for_display(payload: dict[str, Any], settings: Settings, body: dict[str, Any]) -> None:
    language = normalize_display_language(str(body.get("display_language") or ""))
    if language is None or "error" in payload:
        return
    payload["display_language"] = language
    if not (settings.llm_api_key and settings.llm_base_url and settings.llm_model):
        payload["localization_status"] = "skipped_llm_not_configured"
        return

    provider = OpenAIProvider(
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        model=settings.llm_model,
    )
    localizer = PayloadLocalizer(provider, cache=JsonFileCache(settings.cache_dir), model_id=settings.llm_model)
    try:
        localizer.localize_payload(payload, language)
    except (LLMProviderError, ValueError) as exc:
        payload["localization_status"] = "error"
        payload["localization_error"] = str(exc)


def _int_option(data: dict[str, Any], key: str, default: int, minimum: int, maximum: int) -> int:
    raw_value = data.get(key, default)
    try:
        value = int(raw_value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{key} must be an integer") from exc
    return max(minimum, min(value, maximum))


def _choice_option(data: dict[str, Any], key: str, default: str, allowed: set[str]) -> str:
    value = str(data.get(key) or default).strip().lower()
    if value not in allowed:
        raise ValueError(f"{key} must be one of: {', '.join(sorted(allowed))}")
    return value
