import unittest

import httpx

from backend.ai.ollama_client import (
    AIConfigurationError,
    AIProviderUnavailableError,
    OllamaClient,
    OllamaRequestError,
)


class OllamaClientTests(unittest.TestCase):
    def test_chat_posts_to_the_local_ollama_api(self):
        captured_request = None

        def handler(request):
            nonlocal captured_request
            captured_request = request
            return httpx.Response(
                200,
                json={
                    "message": {
                        "role": "assistant",
                        "content": "Local response",
                    }
                },
            )

        http_client = httpx.Client(transport=httpx.MockTransport(handler))
        client = OllamaClient(
            base_url="http://127.0.0.1:11434/",
            client=http_client,
        )

        result = client.chat(
            model="qwen3:4b",
            messages=[{"role": "user", "content": "Hello"}],
            output_format={"type": "object"},
            options={"temperature": 0},
            think=False,
        )

        self.assertEqual(result, "Local response")
        self.assertEqual(
            str(captured_request.url),
            "http://127.0.0.1:11434/api/chat",
        )
        payload = captured_request.read().decode("utf-8")
        self.assertIn('"model":"qwen3:4b"', payload)
        self.assertIn('"stream":false', payload)
        self.assertIn('"format":{"type":"object"}', payload)
        self.assertIn('"think":false', payload)

    def test_connection_failure_reports_that_ollama_is_not_running(self):
        def handler(request):
            raise httpx.ConnectError("connection refused", request=request)

        client = OllamaClient(
            client=httpx.Client(transport=httpx.MockTransport(handler))
        )

        with self.assertRaisesRegex(
            AIProviderUnavailableError,
            "Ollama is not running",
        ):
            client.chat(
                model="qwen3:4b",
                messages=[{"role": "user", "content": "Hello"}],
            )

    def test_missing_model_includes_the_pull_command(self):
        def handler(_request):
            return httpx.Response(
                404,
                json={"error": "model 'qwen3:4b' not found"},
            )

        client = OllamaClient(
            client=httpx.Client(transport=httpx.MockTransport(handler))
        )

        with self.assertRaisesRegex(
            AIConfigurationError,
            "ollama pull qwen3:4b",
        ):
            client.chat(
                model="qwen3:4b",
                messages=[{"role": "user", "content": "Hello"}],
            )

    def test_timeout_is_reported_as_a_request_error(self):
        def handler(request):
            raise httpx.ReadTimeout("timed out", request=request)

        client = OllamaClient(
            client=httpx.Client(transport=httpx.MockTransport(handler))
        )

        with self.assertRaisesRegex(OllamaRequestError, "too long"):
            client.chat(
                model="qwen3:4b",
                messages=[{"role": "user", "content": "Hello"}],
            )

    def test_other_http_errors_are_reported_as_request_errors(self):
        def handler(_request):
            return httpx.Response(500, json={"error": "model runner failed"})

        client = OllamaClient(
            client=httpx.Client(transport=httpx.MockTransport(handler))
        )

        with self.assertRaisesRegex(OllamaRequestError, "model runner failed"):
            client.chat(
                model="qwen3:4b",
                messages=[{"role": "user", "content": "Hello"}],
            )


if __name__ == "__main__":
    unittest.main()
