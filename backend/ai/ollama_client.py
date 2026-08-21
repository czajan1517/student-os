import os
from typing import Any

import httpx


class AIConfigurationError(Exception):
    pass


class AIProviderUnavailableError(Exception):
    pass


class OllamaRequestError(Exception):
    pass


class OllamaClient:
    """Small client for the local Ollama chat API."""

    DEFAULT_BASE_URL = "http://127.0.0.1:11434"

    def __init__(
        self,
        *,
        base_url: str | None = None,
        client: httpx.Client | None = None,
        timeout_seconds: float = 300.0,
    ):
        configured_url = (
            base_url
            or os.getenv("OLLAMA_BASE_URL")
            or self.DEFAULT_BASE_URL
        )
        self.base_url = configured_url.rstrip("/")
        self._client = client or httpx.Client(timeout=timeout_seconds)

    def chat(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        output_format: dict[str, Any] | None = None,
        options: dict[str, Any] | None = None,
        think: bool | None = None,
    ) -> str:
        if not model.strip():
            raise AIConfigurationError("An Ollama model is not configured")

        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": False,
        }
        if output_format is not None:
            payload["format"] = output_format
        if options is not None:
            payload["options"] = options
        if think is not None:
            payload["think"] = think

        try:
            response = self._client.post(
                f"{self.base_url}/api/chat",
                json=payload,
            )
        except httpx.ConnectError as error:
            raise AIProviderUnavailableError(
                f"Ollama is not running at {self.base_url}"
            ) from error
        except httpx.TimeoutException as error:
            raise OllamaRequestError(
                "Ollama took too long to generate a response"
            ) from error
        except httpx.RequestError as error:
            raise OllamaRequestError(
                "The request to the local Ollama service failed"
            ) from error

        if response.status_code == 404:
            detail = self._response_error(response)
            if "model" in detail.lower() and "not found" in detail.lower():
                raise AIConfigurationError(
                    f"Ollama model '{model}' is not installed. "
                    f"Run: ollama pull {model}"
                )

        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as error:
            detail = self._response_error(response)
            raise OllamaRequestError(
                f"Ollama returned HTTP {response.status_code}: {detail}"
            ) from error

        try:
            body = response.json()
        except ValueError as error:
            raise OllamaRequestError(
                "Ollama returned an invalid JSON response"
            ) from error

        if body.get("error"):
            raise OllamaRequestError(str(body["error"]))

        message = body.get("message")
        if not isinstance(message, dict):
            raise OllamaRequestError("Ollama returned no message object")

        content = message.get("content")
        if not isinstance(content, str):
            raise OllamaRequestError("Ollama returned no message content")
        return content

    @staticmethod
    def _response_error(response: httpx.Response) -> str:
        try:
            detail = response.json().get("error")
        except ValueError:
            detail = None
        return str(detail or response.reason_phrase or "Unknown Ollama error")
