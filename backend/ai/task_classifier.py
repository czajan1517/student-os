import json
import os
from typing import Any

from openai import OpenAI, OpenAIError
from pydantic import ValidationError

from backend.schemas.ai import TaskClassification, TaskClassificationRequest


class AIConfigurationError(Exception):
    pass


class TaskClassificationError(Exception):
    pass


class TaskClassifier:
    """Preview-only OpenAI task classifier with structured output."""

    DEFAULT_MODEL = "gpt-5.6"
    _INSTRUCTIONS = """
You classify StudentOS tasks into structured scheduling inputs.

Rules:
- Classify the task; do not calculate a final priority score or rank tasks.
- Use only the task types, effort levels, and importance labels in the schema.
- Treat importance as the consequence of delaying or skipping the task, not merely
  its category.
- Preserve an estimated duration supplied by the user. If none is supplied, make
  a cautious estimate only when the task provides enough context; otherwise use
  null and ask a follow-up question.
- Never invent a due date. A supplied due date is context only and is not returned.
- Use assumptions to disclose uncertain judgments.
- Keep reasons and follow-up questions short and practical.
""".strip()

    def __init__(
        self,
        *,
        client: Any | None = None,
        model: str | None = None,
    ):
        self._client = client
        self._model = model

    @property
    def model(self) -> str:
        return (
            self._model
            or os.getenv("OPENAI_TASK_CLASSIFIER_MODEL")
            or self.DEFAULT_MODEL
        )

    def classify_task(
        self,
        request: TaskClassificationRequest,
    ) -> TaskClassification:
        if self._client is None:
            self._client = self._build_client()
        client = self._client
        try:
            response = client.responses.parse(
                model=self.model,
                instructions=self._INSTRUCTIONS,
                input=[
                    {
                        "role": "user",
                        "content": json.dumps(
                            request.model_dump(mode="json"),
                            ensure_ascii=False,
                        ),
                    }
                ],
                text_format=TaskClassification,
                max_output_tokens=700,
                store=False,
            )
        except (OpenAIError, ValidationError) as error:
            raise TaskClassificationError(
                "The task classification request failed"
            ) from error

        classification = response.output_parsed
        if classification is None:
            raise TaskClassificationError(
                "The model did not return a task classification"
            )
        return classification

    @staticmethod
    def _build_client() -> OpenAI:
        api_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not api_key or api_key == "your_api_key_here":
            raise AIConfigurationError(
                "OPENAI_API_KEY is not configured on the backend"
            )
        return OpenAI(
            api_key=api_key,
            timeout=20.0,
            max_retries=2,
        )
