"""Direct tests for the OpenAI-compatible streaming provider."""

from __future__ import annotations

import io
import json
import unittest
from urllib.error import HTTPError, URLError

from app.providers.openai_provider import LLMProviderError, OpenAIProvider


class FakeStreamingResponse:
    def __init__(self, lines):
        self.lines = list(lines)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def __iter__(self):
        for line in self.lines:
            if isinstance(line, BaseException):
                raise line
            yield line.encode("utf-8")


class RecordingOpener:
    def __init__(self, outcome):
        self.outcome = outcome
        self.calls = []

    def __call__(self, request, timeout):
        self.calls.append((request, timeout))
        if isinstance(self.outcome, BaseException):
            raise self.outcome
        return FakeStreamingResponse(self.outcome)


def stream_line(content):
    return "data: " + json.dumps({"choices": [{"delta": {"content": content}}]})


def http_error(url, code=500, body='{"error": "server error"}'):
    return HTTPError(url=url, code=code, msg="Server Error", hdrs=None, fp=io.BytesIO(body.encode("utf-8")))


class OpenAIProviderTests(unittest.TestCase):
    def test_complete_uses_streaming_payload_and_default_300_second_timeout(self):
        opener = RecordingOpener([stream_line("hello"), stream_line(" world"), "data: [DONE]"])
        provider = OpenAIProvider(api_key="key", base_url="https://llm.example", model="model", opener=opener)

        response = provider.complete("prompt")

        self.assertEqual(response, "hello world")
        request, timeout = opener.calls[0]
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(request.full_url, "https://llm.example/chat/completions")
        self.assertTrue(payload["stream"])
        self.assertEqual(timeout, 300)

    def test_complete_wraps_invalid_stream_event(self):
        opener = RecordingOpener(["data: {not-json}"])
        provider = OpenAIProvider(api_key="key", base_url="https://llm.example", model="model", opener=opener)

        with self.assertRaises(LLMProviderError) as context:
            provider.complete("prompt")

        self.assertIn("invalid event", str(context.exception))

    def test_complete_skips_stream_events_without_choices(self):
        opener = RecordingOpener(['data: {"choices": []}', stream_line("done"), "data: [DONE]"])
        provider = OpenAIProvider(api_key="key", base_url="https://llm.example", model="model", opener=opener)

        self.assertEqual(provider.complete("prompt"), "done")

    def test_complete_wraps_http_error(self):
        opener = RecordingOpener(http_error("https://llm.example/chat/completions"))
        provider = OpenAIProvider(api_key="key", base_url="https://llm.example", model="model", opener=opener)

        with self.assertRaises(LLMProviderError) as context:
            provider.complete("prompt")

        self.assertIn("HTTP 500", str(context.exception))

    def test_complete_wraps_url_error(self):
        opener = RecordingOpener(URLError("temporary network failure"))
        provider = OpenAIProvider(api_key="key", base_url="https://llm.example", model="model", opener=opener)

        with self.assertRaises(LLMProviderError) as context:
            provider.complete("prompt")

        self.assertIn("temporary network failure", str(context.exception))

    def test_complete_wraps_stream_timeout(self):
        opener = RecordingOpener([TimeoutError("read timed out")])
        provider = OpenAIProvider(
            api_key="key",
            base_url="https://llm.example",
            model="model",
            timeout=12,
            opener=opener,
        )

        with self.assertRaises(LLMProviderError) as context:
            provider.complete("prompt")

        self.assertIn("timed out after 12 seconds", str(context.exception))


if __name__ == "__main__":
    unittest.main()
