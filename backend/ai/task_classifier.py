import json
import os
from typing import Any

from pydantic import ValidationError

from backend.ai.ollama_client import OllamaClient, OllamaRequestError
from backend.schemas.ai import TaskClassification, TaskClassificationRequest


class TaskClassificationError(Exception):
    pass


class TaskClassifier:
    """Preview-only local task classifier with structured output."""

    DEFAULT_MODEL = "qwen3:4b"
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
- Return only JSON that matches the supplied schema.
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
        return (
            self._model
            or os.getenv("OLLAMA_TASK_CLASSIFIER_MODEL")
            or self.DEFAULT_MODEL
        )

    def classify_task(
        self,
        request: TaskClassificationRequest,
    ) -> TaskClassification:
        try:
            content = self._client.chat(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self._INSTRUCTIONS,
                    },
                    {
                        "role": "user",
                        "content": json.dumps(
                            request.model_dump(mode="json"),
                            ensure_ascii=False,
                        ),
                    }
                ],
                output_format=TaskClassification.model_json_schema(),
                options={"temperature": 0, "num_predict": 512},
                think=False,
            )
            classification = TaskClassification.model_validate_json(content)
        except (OllamaRequestError, ValidationError) as error:
            raise TaskClassificationError(
                "The task classification request failed"
            ) from error

        if request.estimated_time_minutes is not None:
            classification = classification.model_copy(
                update={
                    "estimated_time_minutes": request.estimated_time_minutes,
                }
            )

        return classification
