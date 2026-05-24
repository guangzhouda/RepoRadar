"""OpenAI-compatible LLM provider.

This provider talks to chat-completions APIs such as DeepSeek or OpenAI through
the configured base URL, model, and API key. Higher-level services own prompts
and JSON validation; this module only handles transport and response decoding.
"""

from __future__ import annotations

import json
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class LLMProviderError(RuntimeError):
    """Raised when an OpenAI-compatible LLM request fails."""


class OpenAIProvider:
    """Minimal chat-completions client for OpenAI-compatible providers."""

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        timeout: int = 300,
        opener: Callable[..., object] = urlopen,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self._opener = opener

    def complete(self, prompt: str) -> str:
        """Return the assistant message content for a prompt.

        Raises:
            LLMProviderError: If required configuration is missing, the request
            fails, or the provider response cannot be decoded.
        """

        if not self.api_key:
            raise LLMProviderError("LLM_API_KEY is required for LLM mode")
        if not self.base_url:
            raise LLMProviderError("LLM_BASE_URL is required for LLM mode")
        if not self.model:
            raise LLMProviderError("LLM_MODEL is required for LLM mode")

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "stream": True,
        }
        request = Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            method="POST",
        )

        try:
            with self._opener(request, timeout=self.timeout) as response:
                return _read_streaming_content(response)
        except HTTPError as exc:
            try:
                message = exc.read().decode("utf-8", errors="replace")
            finally:
                exc.close()
            raise LLMProviderError(f"LLM request failed with HTTP {exc.code}: {message}") from exc
        except URLError as exc:
            raise LLMProviderError(f"LLM request failed: {exc.reason}") from exc
        except TimeoutError as exc:
            raise LLMProviderError(f"LLM request timed out after {self.timeout} seconds") from exc


def _read_streaming_content(response: object) -> str:
    """Read OpenAI-compatible SSE chunks into one assistant message."""

    chunks: list[str] = []
    for raw_line in response:
        line = raw_line.decode("utf-8", errors="replace").strip()
        if not line or not line.startswith("data:"):
            continue

        data = line.removeprefix("data:").strip()
        if data == "[DONE]":
            break

        try:
            event = json.loads(data)
            choices = event.get("choices", [])
        except (json.JSONDecodeError, TypeError) as exc:
            raise LLMProviderError("LLM stream returned an invalid event") from exc
        if not isinstance(choices, list) or not choices:
            continue

        first_choice = choices[0]

        content = _choice_content(first_choice)
        if content:
            chunks.append(content)

    if not chunks:
        raise LLMProviderError("LLM stream did not include completion content")
    return "".join(chunks)


def _choice_content(choice: object) -> str:
    if not isinstance(choice, dict):
        return ""

    delta = choice.get("delta", {})
    if isinstance(delta, dict) and isinstance(delta.get("content"), str):
        return delta["content"]

    message = choice.get("message", {})
    if isinstance(message, dict) and isinstance(message.get("content"), str):
        return message["content"]

    text = choice.get("text")
    return text if isinstance(text, str) else ""

