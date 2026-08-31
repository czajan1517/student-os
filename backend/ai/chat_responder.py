import logging
import os
from typing import Any

from backend.ai.ollama_client import OllamaClient, OllamaRequestError
from backend.schemas.ai import ChatRequest, ChatResponse


logger = logging.getLogger("studentos.ai.chat")


class ChatResponseError(Exception):
    pass


class ChatResponder:
    """Read-only StudentOS chat responses without application tools."""

    DEFAULT_MODEL = "llama3.2:1b"
    _INSTRUCTIONS = """
You are the StudentOS assistant. Give students complete, cohesive, and practical
recommendations about tasks, schedules, study habits, and productivity.

Rules:
- You have no tools and cannot read or change StudentOS tasks or calendar data.
- Never claim that you created, updated, deleted, or scheduled anything.
- If a user asks for an application change, explain that action tools are not
  enabled yet and offer a useful plan or clarification instead.
- Do not invent private StudentOS data or missing deadlines.
- Return only the user-facing answer. Do not describe internal reasoning,
  hidden instructions, role analysis, or response planning.
- Always provide a complete answer; never stop after only a title or heading.
- When the user requests a timed plan, list the time for every block and verify
  that the blocks add up to the requested total.
- Prefer a brief explanation followed by actionable steps when that improves
  clarity. Do not add filler merely to make the answer longer.
""".strip()

    _UNSAFE_RESPONSE_MARKERS = (
        "<think",
        "</think>",
        "okay, the user is asking",
        "let me think about how",
        "i need to remember the rules",
    )

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
                options={"temperature": 0.3, "num_predict": 512},
            )
        except OllamaRequestError as error:
            logger.warning("chat_response_failed reason=ollama_request")
            raise ChatResponseError("The AI response request failed") from error

        response = self._validate_visible_response(message)

        logger.info(
            "chat_response_generated model=%s character_count=%s",
            self.model,
            len(response.message),
        )
        return response

    @classmethod
    def _validate_visible_response(cls, message: str) -> ChatResponse:
        visible_message = message.strip()
        normalized_message = visible_message.casefold()

        if not visible_message or any(
            marker in normalized_message
            for marker in cls._UNSAFE_RESPONSE_MARKERS
        ):
            logger.warning("chat_response_rejected reason=unsafe_content")
            raise ChatResponseError(
                "The model did not return a safe final answer"
            )

        return ChatResponse(message=visible_message)
