import os
from typing import Any

from backend.ai.ollama_client import OllamaClient, OllamaRequestError
from backend.schemas.ai import ChatRequest, ChatResponse


class ChatResponseError(Exception):
    pass


class ChatResponder:
    """Read-only StudentOS chat responses without application tools."""

    DEFAULT_MODEL = "qwen3:4b"
    _INSTRUCTIONS = """
You are the StudentOS assistant. Help students reason about tasks, schedules,
study habits, and productivity in a concise and supportive way.

Rules:
- You have no tools and cannot read or change StudentOS tasks or calendar data.
- Never claim that you created, updated, deleted, or scheduled anything.
- If a user asks for an application change, explain that action tools are not
  enabled yet and offer a useful plan or clarification instead.
- Do not invent private StudentOS data or missing deadlines.
- Keep answers practical and easy to scan.
""".strip()

    def __init__(
        self,
        *,
        client: Any | None = None,
        model: str | None = None,
    ):
        self._client = client if client is not None else OllamaClient()
        self._model = model

    @property
    def model(self) -> str:
        return self._model or os.getenv("OLLAMA_CHAT_MODEL") or self.DEFAULT_MODEL

    def respond(self, request: ChatRequest) -> ChatResponse:
        chat_messages = [
            chat_message.model_dump()
            for chat_message in request.messages
        ]
        chat_messages[-1]["content"] += "\n\n/no_think"

        try:
            message = self._client.chat(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._INSTRUCTIONS,
                    },
                    *chat_messages,
                ],
                options={"temperature": 0.3, "num_predict": 256},
                think=False,
            )
        except OllamaRequestError as error:
            raise ChatResponseError("The AI response request failed") from error

        if "</think>" in message:
            message = message.rsplit("</think>", maxsplit=1)[1]
        message = message.strip()
        if not message:
            raise ChatResponseError("The model did not return a message")
        return ChatResponse(message=message)
