import json
import logging
import os
import re
from datetime import datetime
from typing import Any, Callable

from pydantic import ValidationError

from backend.ai.ollama_client import OllamaClient, OllamaRequestError
from backend.schemas.ai import (
    SuggestedEffort,
    SuggestedImportance,
    TaskActionPreviewRequest,
    TaskCreateDraft,
    TaskCreateInterpretation,
    TaskCreateProposal,
)
from backend.schemas.common import EffortLevel, PriorityLevel
from backend.schemas.task import TaskCreate, TaskRead
from backend.services.task_service import TaskService


logger = logging.getLogger("studentos.ai.task_action")


class TaskActionPlanningError(Exception):
    pass


class TaskActionNotReadyError(Exception):
    pass


class TaskActionService:
    """Plans task creation with Qwen and applies only confirmed proposals."""

    DEFAULT_MODEL = "qwen3:4b"
    _INSTRUCTIONS = """
You convert one StudentOS user message into a proposed task creation action.

Rules:
- Propose only a create_task action. Never claim that the task was created.
- Extract a short action-oriented title and preserve useful user details.
- Importance means the consequence of delaying or skipping the task.
- Never invent an exact due date. Resolve a relative date only when it is
  unambiguous from the supplied current time; otherwise use an empty string and
  ask.
- Estimate duration only when the message has enough context. Otherwise use null
  and ask how long the task should take.
- Convert explicit hours to total minutes. For example, three hours means 180
  minutes unless the user clearly says that duration applies to each session.
- Preserve an explicitly supplied clock time. Never replace "9 AM" with
  midnight or another hour.
- Ask a follow-up question when important ambiguity could materially change the
  task, especially its identity, duration, or deadline.
- Disclose non-blocking uncertainty in assumptions.
- Return only JSON matching the supplied schema.
""".strip()

    _PRIORITY_MAP = {
        SuggestedImportance.NORMAL: PriorityLevel.NORMAL,
        SuggestedImportance.HIGH: PriorityLevel.HIGH,
        SuggestedImportance.MEDIUM: PriorityLevel.MEDIUM,
        SuggestedImportance.LOW: PriorityLevel.LOW,
    }
    _EFFORT_MAP = {
        SuggestedEffort.LIGHT: EffortLevel.LIGHT,
        SuggestedEffort.MODERATE: EffortLevel.MODERATE,
        SuggestedEffort.HEAVY: EffortLevel.HEAVY,
    }
    _UNSUPPORTED_GRAMMAR_KEYS = {
        "default",
        "description",
        "exclusiveMinimum",
        "format",
        "maxLength",
        "maximum",
        "minLength",
        "minimum",
        "title",
    }

    def __init__(
        self,
        *,
        client: Any | None = None,
        model: str | None = None,
        task_service: TaskService | None = None,
        now_factory: Callable[[], datetime] | None = None,
    ):
        self._client = client if client is not None else OllamaClient()
        self._model = model
        self._task_service = task_service or TaskService()
        self._now_factory = now_factory or (
            lambda: datetime.now().astimezone()
        )

    @property
    def model(self) -> str:
        return (
            self._model
            or os.getenv("OLLAMA_TASK_ACTION_MODEL")
            or self.DEFAULT_MODEL
        )

    def preview_task_creation(
        self,
        request: TaskActionPreviewRequest,
    ) -> TaskCreateProposal:
        logger.info("task_action_preview_started model=%s", self.model)
        context = {
            "current_time": self._now_factory().isoformat(),
            "user_message": request.message,
        }
        try:
            content = self._client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._INSTRUCTIONS},
                    {
                        "role": "user",
                        "content": json.dumps(context, ensure_ascii=False),
                    },
                ],
                output_format=self._ollama_output_schema(),
                options={"temperature": 0, "num_predict": 512},
                think=False,
            )
            interpretation = (
                TaskCreateInterpretation.model_validate_json(content)
            )
        except (OllamaRequestError, ValidationError) as error:
            logger.warning(
                "task_action_preview_failed reason=%s",
                type(error).__name__,
            )
            raise TaskActionPlanningError(
                "The task action preview request failed"
            ) from error

        questions = list(interpretation.follow_up_questions)
        explicit_duration = self._explicit_duration_minutes(request.message)
        estimated_time_minutes = (
            explicit_duration or interpretation.estimated_time_minutes
        )
        if explicit_duration is not None:
            questions = [
                question
                for question in questions
                if not self._is_duration_question(question)
            ]
        if estimated_time_minutes is None:
            if not questions:
                questions.append("How many minutes should this task take?")

        due_date = None
        if interpretation.due_date:
            try:
                due_date = datetime.fromisoformat(
                    interpretation.due_date.replace("Z", "+00:00")
                )
            except ValueError:
                questions.append(
                    "What exact date and time should this task be due?"
                )
        explicit_time = self._explicit_clock_time(request.message)
        if due_date is not None and explicit_time is not None:
            hour, minute = explicit_time
            due_date = due_date.replace(
                hour=hour,
                minute=minute,
                second=0,
                microsecond=0,
            )

        try:
            task = TaskCreateDraft(
                title=interpretation.title,
                description=interpretation.description,
                priority=self._PRIORITY_MAP[
                    interpretation.suggested_importance
                ],
                estimated_time=estimated_time_minutes,
                task_type=interpretation.task_type,
                effort_level=self._EFFORT_MAP[interpretation.effort_level],
                recovery_buffer_minutes=(
                    interpretation.recovery_buffer_minutes
                ),
                splittable=interpretation.splittable,
                due_date=due_date,
                completed=False,
            )
        except ValidationError as error:
            logger.warning(
                "task_action_preview_failed reason=draft_validation",
            )
            raise TaskActionPlanningError(
                "The task action preview request failed"
            ) from error
        ready_to_apply = (
            estimated_time_minutes is not None
            and not questions
        )
        proposal = TaskCreateProposal(
            task=task,
            confidence=interpretation.confidence,
            reasons=interpretation.reasons,
            assumptions=interpretation.assumptions,
            follow_up_questions=questions,
            ready_to_apply=ready_to_apply,
        )
        logger.info(
            "task_action_preview_generated ready_to_apply=%s "
            "question_count=%s task_type=%s estimated_time_minutes=%s "
            "has_due_date=%s",
            proposal.ready_to_apply,
            len(proposal.follow_up_questions),
            proposal.task.task_type.value,
            proposal.task.estimated_time,
            proposal.task.due_date is not None,
        )
        return proposal

    def apply_task_creation(
        self,
        proposal: TaskCreateProposal,
    ) -> TaskRead:
        if not proposal.ready_to_apply:
            logger.warning(
                "task_action_apply_rejected reason=proposal_not_ready"
            )
            raise TaskActionNotReadyError(
                "The task proposal needs more information before it can be applied"
            )
        task = TaskCreate.model_validate(proposal.task.model_dump())
        created_task = self._task_service.create_task(task)
        logger.info(
            "task_action_applied task_id=%s task_type=%s",
            getattr(created_task, "id", None),
            task.task_type.value,
        )
        return created_task

    @staticmethod
    def _explicit_duration_minutes(message: str) -> int | None:
        if re.search(r"\bper\s+session\b", message, flags=re.IGNORECASE):
            return None

        hours = re.search(
            r"\b(\d+(?:\.\d+)?)\s*(?:hours?|hrs?|hr)\b",
            message,
            flags=re.IGNORECASE,
        )
        if hours:
            minutes = round(float(hours.group(1)) * 60)
            return minutes if 0 < minutes <= 1440 else None

        minutes = re.search(
            r"\b(\d+)\s*(?:minutes?|mins?|min)\b",
            message,
            flags=re.IGNORECASE,
        )
        if minutes:
            value = int(minutes.group(1))
            return value if 0 < value <= 1440 else None
        return None

    @staticmethod
    def _explicit_clock_time(message: str) -> tuple[int, int] | None:
        match = re.search(
            r"\b(?:at|by)\s+(\d{1,2})(?::(\d{2}))?\s*([ap]m)\b",
            message,
            flags=re.IGNORECASE,
        )
        if not match:
            return None

        hour = int(match.group(1))
        minute = int(match.group(2) or 0)
        if not 1 <= hour <= 12 or not 0 <= minute <= 59:
            return None
        if match.group(3).lower() == "am":
            hour = 0 if hour == 12 else hour
        else:
            hour = 12 if hour == 12 else hour + 12
        return hour, minute

    @staticmethod
    def _is_duration_question(question: str) -> bool:
        normalized = question.lower()
        return any(
            phrase in normalized
            for phrase in (
                "how long",
                "minute",
                "hour",
                "duration",
                "per session",
                "total time",
            )
        )

    @classmethod
    def _ollama_output_schema(cls) -> dict[str, Any]:
        """Keep grammar structure while Pydantic retains full validation."""

        def clean(value: Any, *, schema_names: bool = False) -> Any:
            if isinstance(value, list):
                return [clean(item) for item in value]
            if not isinstance(value, dict):
                return value
            if schema_names:
                return {
                    name: clean(schema)
                    for name, schema in value.items()
                }
            return {
                key: clean(
                    item,
                    schema_names=key in {"$defs", "properties"},
                )
                for key, item in value.items()
                if key not in cls._UNSUPPORTED_GRAMMAR_KEYS
            }

        return clean(TaskCreateInterpretation.model_json_schema())
