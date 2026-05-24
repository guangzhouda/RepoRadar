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
        timeout: int = 60,
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
                raw = response.read().decode("utf-8")
        except HTTPError as exc:
            message = exc.read().decode("utf-8", errors="replace")
            raise LLMProviderError(f"LLM request failed with HTTP {exc.code}: {message}") from exc
        except URLError as exc:
            raise LLMProviderError(f"LLM request failed: {exc.reason}") from exc

        try:
            decoded = json.loads(raw)
            choices = decoded["choices"]
            first_choice = choices[0]
            message = first_choice.get("message", {})
            content = message.get("content") or first_choice.get("text")
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMProviderError("LLM response did not include completion content") from exc

        if not isinstance(content, str):
            raise LLMProviderError("LLM completion content was not a string")
        return content

