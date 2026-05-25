"""Payload localization helpers for frontend display text.

The analyzer returns GitHub metadata in its original language. This service
adds optional localized display fields to the JSON payload without changing the
canonical source fields, so CLI output and downstream report conversion keep
their existing behavior.
"""

from __future__ import annotations

import json
from typing import Any, Protocol

from app.services.cache import JsonFileCache
from app.services.llm_json import parse_json_object


CANDIDATE_TEXT_FIELDS = ("description", "rationale", "reject_reason")
SKILL_CARD_TEXT_FIELDS = ("summary",)
SKILL_CARD_LIST_FIELDS = (
    "categories",
    "core_capabilities",
    "optional_capabilities",
    "deployment",
    "suitable_for",
    "not_supported",
    "limitations",
)


class TextCompletionProvider(Protocol):
    """Minimal provider contract used by payload localization."""

    def complete(self, prompt: str) -> str:
        """Return assistant text for a prompt."""


class PayloadLocalizer:
    """Add localized candidate display fields to analysis payloads.

    The service mutates the provided payload in place and only adds
    ``*_i18n`` fields. It never overwrites the original GitHub description,
    review rationale, or reject reason.
    """

    def __init__(self, provider: TextCompletionProvider, cache: JsonFileCache, model_id: str = "") -> None:
        self.provider = provider
        self.cache = cache
        self.model_id = model_id

    def localize_payload(self, payload: dict[str, Any], target_language: str) -> dict[str, Any]:
        """Populate localized display fields for supported languages.

        Args:
            payload: Analysis payload produced by ``IdeaAnalysisService``.
            target_language: ``zh`` or ``en``.

        Returns:
            The same payload object, updated with localized candidate fields.

        Raises:
            ValueError: If the LLM response cannot be mapped back to payload
                candidates.
        """

        language = normalize_display_language(target_language)
        if language is None:
            return payload

        candidates = payload.get("candidates", [])
        if not isinstance(candidates, list):
            return payload

        payload["display_language"] = language
        requests = _translation_requests(candidates, language)
        if not requests:
            payload["localization_status"] = "not_needed"
            return payload

        cache_key = _cache_key(requests, language, self.model_id)
        cached = self.cache.get("localization", cache_key)
        if cached is None:
            cached = self._translate(requests, language)
            self.cache.set("localization", cache_key, cached)

        _apply_translations(candidates, cached, language)
        payload["localization_status"] = "translated"
        return payload

    def _translate(self, requests: list[dict[str, Any]], target_language: str) -> dict[str, Any]:
        prompt = build_localization_prompt(requests, target_language)
        parsed = parse_json_object(self.provider.complete(prompt))
        if not isinstance(parsed.get("items"), list):
            raise ValueError("localization response must include an items list")
        return parsed


class TextLocalizer:
    """Translate one frontend display string without changing source fields.

    This is used by interactive UI actions where the user requests translation
    for a single candidate description after analysis has already completed.
    Results are cached by model, target language, scope, and full input text.
    """

    def __init__(self, provider: TextCompletionProvider, cache: JsonFileCache, model_id: str = "") -> None:
        self.provider = provider
        self.cache = cache
        self.model_id = model_id

    def localize_text(self, text: str, target_language: str, scope: str = "display_text") -> dict[str, Any]:
        """Return translated text for one display field.

        Args:
            text: Source text to translate. It is not truncated.
            target_language: Supported target language alias, currently zh/en.
            scope: Caller-provided purpose label included in the cache key.

        Returns:
            A small JSON-serializable object with ``text``, ``status``, and
            ``cached`` fields.

        Raises:
            ValueError: If text is empty, target language is unsupported, or
                the provider response does not contain translated text.
        """

        source_text = str(text or "").strip()
        if not source_text:
            raise ValueError("text is required")

        language = normalize_display_language(target_language)
        if language is None:
            raise ValueError("target_language must be zh or en")

        if not _needs_translation(source_text, language):
            return {"text": source_text, "status": "not_needed", "cached": False}

        cache_key = _text_cache_key(source_text, language, scope, self.model_id)
        cached = self.cache.get("text_localization", cache_key)
        if cached is not None:
            cached_text = str(cached.get("text") or "").strip()
            if cached_text:
                return {"text": cached_text, "status": "translated", "cached": True}

        translated_text = self._translate_text(source_text, language, scope)
        cached_payload = {"text": translated_text}
        self.cache.set("text_localization", cache_key, cached_payload)
        return {"text": translated_text, "status": "translated", "cached": False}

    def _translate_text(self, text: str, target_language: str, scope: str) -> str:
        prompt = build_text_localization_prompt(text, target_language, scope)
        parsed = parse_json_object(self.provider.complete(prompt))
        translated = str(parsed.get("text") or "").strip()
        if not translated:
            raise ValueError("localization response must include non-empty text")
        return translated


def normalize_display_language(language: str) -> str | None:
    """Return the supported display language code, or None for no localization."""

    normalized = str(language or "").strip().lower()
    if normalized in {"zh", "zh-cn", "cn", "chinese"}:
        return "zh"
    if normalized in {"en", "en-us", "english"}:
        return "en"
    return None


def build_localization_prompt(requests: list[dict[str, Any]], target_language: str) -> str:
    """Build the strict JSON localization prompt for candidate display text."""

    language_name = "Simplified Chinese" if target_language == "zh" else "English"
    return "\n".join(
        [
            f"Translate the following GitHub repository display text into {language_name}.",
            "Keep repository names, product names, API names, model names, file formats, and programming terms unchanged when appropriate.",
            "Translate candidate fields and nested skill_card fields. Preserve the input JSON shape and field names.",
            "Return strict JSON only. Do not add Markdown fences or commentary.",
            'Schema: {"items":[{"full_name":"owner/repo","description":"...","rationale":"...","reject_reason":"...","skill_card":{"summary":"...","categories":["..."],"core_capabilities":["..."]}}]}',
            "Omit empty translated fields, but keep every full_name that appears in the input.",
            "",
            json.dumps({"items": requests}, ensure_ascii=False, indent=2),
        ]
    )


def build_text_localization_prompt(text: str, target_language: str, scope: str) -> str:
    """Build the strict JSON prompt for one display text translation."""

    language_name = "Simplified Chinese" if target_language == "zh" else "English"
    return "\n".join(
        [
            f"Translate this GitHub repository display text into {language_name}.",
            "Keep repository names, product names, API names, model names, file formats, and programming terms unchanged when appropriate.",
            "Preserve the meaning and keep the translation concise for UI display.",
            "Return strict JSON only. Do not add Markdown fences or commentary.",
            'Schema: {"text":"..."}',
            f"Scope: {scope}",
            "",
            json.dumps({"text": text}, ensure_ascii=False, indent=2),
        ]
    )


def _translation_requests(candidates: list[Any], target_language: str) -> list[dict[str, Any]]:
    requests: list[dict[str, Any]] = []
    for raw_candidate in candidates:
        if not isinstance(raw_candidate, dict):
            continue

        full_name = str(raw_candidate.get("full_name") or raw_candidate.get("fullName") or "").strip()
        if not full_name:
            continue

        item: dict[str, Any] = {"full_name": full_name}
        for field in CANDIDATE_TEXT_FIELDS:
            value = str(raw_candidate.get(field) or "").strip()
            if value and _needs_translation(value, target_language):
                item[field] = value

        raw_card = raw_candidate.get("skill_card")
        if isinstance(raw_card, dict):
            card_request = _skill_card_translation_request(raw_card, target_language)
            if card_request:
                item["skill_card"] = card_request

        if len(item) > 1:
            requests.append(item)
    return requests


def _skill_card_translation_request(raw_card: dict[str, Any], target_language: str) -> dict[str, Any]:
    request: dict[str, Any] = {}
    for field in SKILL_CARD_TEXT_FIELDS:
        value = str(raw_card.get(field) or "").strip()
        if value and _needs_translation(value, target_language):
            request[field] = value

    for field in SKILL_CARD_LIST_FIELDS:
        values = _string_list(raw_card.get(field))
        if values and any(_needs_translation(value, target_language) for value in values):
            request[field] = values

    return request


def _needs_translation(value: str, target_language: str) -> bool:
    has_cjk = any("\u3400" <= char <= "\u9fff" for char in value)
    if target_language == "zh":
        return not has_cjk
    if target_language == "en":
        return has_cjk
    return False


def _apply_translations(candidates: list[Any], translated: dict[str, Any], target_language: str) -> None:
    by_name = {
        str(candidate.get("full_name") or candidate.get("fullName") or ""): candidate
        for candidate in candidates
        if isinstance(candidate, dict)
    }

    for item in translated.get("items", []):
        if not isinstance(item, dict):
            continue
        candidate = by_name.get(str(item.get("full_name") or ""))
        if candidate is None:
            continue
        for field in CANDIDATE_TEXT_FIELDS:
            value = str(item.get(field) or "").strip()
            if value:
                _set_i18n_field(candidate, field, target_language, value)

        raw_card = candidate.get("skill_card")
        translated_card = item.get("skill_card")
        if isinstance(raw_card, dict) and isinstance(translated_card, dict):
            _apply_skill_card_translations(raw_card, translated_card, target_language)


def _apply_skill_card_translations(card: dict[str, Any], translated: dict[str, Any], target_language: str) -> None:
    for field in SKILL_CARD_TEXT_FIELDS:
        value = str(translated.get(field) or "").strip()
        if value:
            _set_i18n_field(card, field, target_language, value)

    for field in SKILL_CARD_LIST_FIELDS:
        values = _string_list(translated.get(field))
        if values:
            _set_i18n_field(card, field, target_language, values)


def _set_i18n_field(candidate: dict[str, Any], field: str, language: str, value: Any) -> None:
    i18n_key = f"{field}_i18n"
    existing = candidate.get(i18n_key)
    if not isinstance(existing, dict):
        existing = {}
        candidate[i18n_key] = existing
    existing[language] = value


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _cache_key(requests: list[dict[str, Any]], target_language: str, model_id: str) -> str:
    return json.dumps(
        {
            "model": model_id,
            "target_language": target_language,
            "items": requests,
        },
        ensure_ascii=False,
        sort_keys=True,
    )


def _text_cache_key(text: str, target_language: str, scope: str, model_id: str) -> str:
    return json.dumps(
        {
            "model": model_id,
            "target_language": target_language,
            "scope": scope,
            "text": text,
        },
        ensure_ascii=False,
        sort_keys=True,
    )
