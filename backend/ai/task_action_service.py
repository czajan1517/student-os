import json
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Callable
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import ValidationError

from backend.ai.ollama_client import OllamaClient, OllamaRequestError
from backend.schemas.ai import (
    SuggestedEffort,
    SuggestedImportance,
    TaskActionPreviewRequest,
    TaskClarification,
    TaskClarificationField,
    TaskCreateDraft,
    TaskCreateInterpretation,
    TaskCreateProposal,
    TaskSchedulingMode,
)
from backend.schemas.common import EffortLevel, PriorityLevel
from backend.schemas.schedule import (
    TaskCreationApplyResult,
    TaskTimingInput,
    TaskTimingParseResult,
)
from backend.schemas.task import TaskCreate
from backend.services.schedule_service import ScheduleService
from backend.services.task_time_service import TaskTimeService


logger = logging.getLogger("studentos.ai.task_action")


class TaskActionPlanningError(Exception):
    pass


class TaskActionNotReadyError(Exception):
    pass


class TaskActionService:
    """Plans task creation with Qwen and applies only confirmed proposals."""

    DEFAULT_MODEL = "qwen3:4b"
    _INSTRUCTIONS = """
You convert the latest StudentOS user message into the full current state of a
proposed task creation action.

Rules:
- Propose only a create_task action. Never claim that the task was created.
- When current_proposal is null, interpret a new task request.
- When current_proposal is present, treat the latest_user_message as a revision.
  Preserve existing values unless the latest message changes or clears them.
  The latest message takes precedence over older proposal values.
- Re-evaluate every previous follow-up question against the latest message and
  updated timing values. Return only questions that are still unanswered. Never
  copy a previous question when its corresponding field is now populated.
- Tag every follow-up question with the single field that would resolve it.
- Set scheduling_mode to automatic when the user gives a deadline and wants
  StudentOS to choose the work time. In automatic mode, put the complete
  deadline date and clock time in due_date; leave schedule_date, start_time,
  and end_time null.
- Set scheduling_mode to fixed when the user gives an exact work date or clock
  interval. In fixed mode, schedule_date/start_time/end_time describe when the
  work happens. Set due_date only when the user separately states a deadline.
- Set scheduling_mode to undecided when neither an exact work placement nor a
  complete deadline is known.
- Words such as due, deadline, submit by, and finish by describe due_date. They
  never describe end_time. Words such as schedule, start, work from, and work
  until describe the fixed schedule fields.
- Treat "scheduled for", "occur on", "happen on", "do it on", and similar
  wording as the same schedule_date intent. A short follow-up such as
  "tomorrow" answers a schedule_date question: set schedule_date from
  current_time and remove every previous schedule_date question.
- Never return more than one follow-up question for the same field.
- Extract a short action-oriented title and preserve useful user details.
- Importance means the consequence of delaying or skipping the task.
- Interpret natural-language dates, clock times, durations, corrections, and
  unusual grammar into the timing object. Use current_time for relative dates.
- Return due_date as an ISO 8601 datetime, schedule_date as YYYY-MM-DD, and
  start_time/end_time as HH:MM:SS. Use null when a value is not known.
- timing must describe the latest intended state, not every value mentioned in
  the conversation. If a revision changes duration without repeating an old
  end time, clear end_time so the backend can recalculate it. If it changes the
  end time without repeating a duration, clear duration_minutes.
- Estimate duration only when the request has enough context. Otherwise use
  null and ask how long the task should take.
- Resolve explicit relative phrases such as today or tomorrow from current_time,
  using browser_timezone when supplied. Do not decide calendar feasibility or
  calculate schedule blocks. Backend code validates timing, calculates
  intervals, and detects conflicts.
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
        schedule_service: ScheduleService | None = None,
        task_time_service: TaskTimeService | None = None,
        now_factory: Callable[[], datetime] | None = None,
    ):
        self._client = client if client is not None else OllamaClient()
        self._model = model
        self._now_factory = now_factory or (
            lambda: datetime.now().astimezone()
        )
        self._schedule_service = schedule_service or ScheduleService()
        self._task_time_service = task_time_service or TaskTimeService(
            now_factory=self._now_factory
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
        now = self._localized_now(request)
        context = {
            "current_time": now.isoformat(),
            "browser_timezone": request.timezone_name,
            "utc_offset_minutes": request.utc_offset_minutes,
            "latest_user_message": request.message,
            "answering_field": (
                request.answering_field.value
                if request.answering_field is not None
                else None
            ),
            "latest_answer": request.latest_answer,
            "current_proposal": self._proposal_context(
                request.current_proposal
            ),
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

        interpretation = self._reconcile_explicit_timing_facts(
            request,
            interpretation,
            now=now,
        )
        normalized_timing_input = self._normalize_timing_input(
            interpretation.scheduling_mode,
            interpretation.timing,
        )
        timing = self._task_time_service.resolve(
            normalized_timing_input,
            reference_time=now,
        )
        model_clarifications = self._remaining_model_clarifications(
            interpretation.follow_up_questions,
            interpretation=interpretation,
            timing=timing,
            timezone_available=(
                request.timezone_name is not None
                or request.utc_offset_minutes is not None
            ),
        )
        clarifications = self._unique_clarifications(
            [
                *model_clarifications,
                *(
                    self._timing_clarification(question)
                    for question in timing.clarification_questions
                ),
            ]
        )
        estimated_time_minutes = self._resolved_schedule_duration(timing)
        if estimated_time_minutes is None:
            clarifications.append(
                TaskClarification(
                    field=TaskClarificationField.DURATION,
                    question="How many minutes should this task take?",
                )
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
                due_date=timing.due_date,
                completed=False,
            )
        except ValidationError as error:
            logger.warning(
                "task_action_preview_failed reason=draft_validation",
            )
            raise TaskActionPlanningError(
                "The task action preview request failed"
            ) from error

        schedule_preview = None
        if estimated_time_minutes is not None and not timing.clarification_questions:
            if timing.schedule is not None or timing.due_date is not None:
                try:
                    schedule_preview = self._schedule_service.preview_task_creation(
                        TaskCreate.model_validate(task.model_dump()),
                        timing,
                        now,
                    )
                except Exception as error:
                    logger.warning(
                        "task_action_preview_failed reason=schedule_preview"
                    )
                    raise TaskActionPlanningError(
                        "The task schedule preview failed"
                    ) from error
                if not schedule_preview.feasible:
                    clarifications.append(
                        self._schedule_clarification(schedule_preview.mode)
                    )
            elif not clarifications:
                clarifications.append(
                    TaskClarification(
                        field=TaskClarificationField.SCHEDULE_OR_DUE,
                        question="When should this task be scheduled or due?",
                    )
                )

        pending_clarifications = self._unique_clarifications(
            clarifications
        )[:1]
        questions = [
            clarification.question
            for clarification in pending_clarifications
        ]
        ready_to_apply = (
            estimated_time_minutes is not None
            and schedule_preview is not None
            and schedule_preview.feasible
            and not questions
        )
        proposal = TaskCreateProposal(
            scheduling_mode=interpretation.scheduling_mode,
            task=task,
            timing=timing,
            schedule_preview=schedule_preview,
            confidence=interpretation.confidence,
            reasons=interpretation.reasons,
            assumptions=interpretation.assumptions,
            follow_up_questions=questions,
            pending_clarifications=pending_clarifications,
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
    ) -> TaskCreationApplyResult:
        if (
            not proposal.ready_to_apply
            or proposal.follow_up_questions
            or proposal.timing.clarification_questions
            or proposal.schedule_preview is None
            or not proposal.schedule_preview.feasible
        ):
            logger.warning(
                "task_action_apply_rejected reason=proposal_not_ready"
            )
            raise TaskActionNotReadyError(
                "The task proposal needs more information before it can be applied"
            )
        task = TaskCreate.model_validate(proposal.task.model_dump())
        result = self._schedule_service.apply_task_creation(
            task,
            proposal.timing,
            self._now_factory(),
        )
        logger.info(
            "task_action_applied task_id=%s task_type=%s "
            "created_event_count=%s",
            result.task.id,
            task.task_type.value,
            len(result.created_events),
        )
        return result

    @staticmethod
    def _resolved_schedule_duration(
        timing: TaskTimingParseResult,
    ) -> int | None:
        if timing.duration_minutes is not None:
            return timing.duration_minutes
        if timing.schedule is None:
            return None
        return round(
            (
                timing.schedule.end_at - timing.schedule.start_at
            ).total_seconds()
            / 60
        )

    def _reconcile_explicit_timing_facts(
        self,
        request: TaskActionPreviewRequest,
        interpretation: TaskCreateInterpretation,
        *,
        now: datetime,
    ) -> TaskCreateInterpretation:
        """Restore unambiguous timing facts that Qwen omitted."""

        timing_updates: dict[str, Any] = {}
        latest_text = request.latest_answer or request.message
        explicit_duration = TaskTimeService.extract_explicit_duration(
            latest_text
        )
        if (
            interpretation.timing.duration_minutes is None
            and explicit_duration is not None
        ):
            timing_updates["duration_minutes"] = explicit_duration
        elif (
            interpretation.timing.duration_minutes is None
            and request.current_proposal is not None
            and request.answering_field
            != TaskClarificationField.DURATION
            and request.current_proposal.timing.duration_minutes is not None
        ):
            timing_updates["duration_minutes"] = (
                request.current_proposal.timing.duration_minutes
            )

        scheduling_mode = interpretation.scheduling_mode
        should_restore_schedule_date = (
            interpretation.timing.schedule_date is None
            and interpretation.timing.due_date is None
            and not TaskTimeService.has_explicit_deadline_intent(
                request.message
            )
            and (
                request.answering_field
                == TaskClarificationField.SCHEDULE_DATE
                or request.current_proposal is None
            )
        )
        if should_restore_schedule_date:
            explicit_date = TaskTimeService.extract_explicit_date(
                latest_text,
                reference_time=now,
            )
            if explicit_date is not None:
                timing_updates["schedule_date"] = explicit_date
                scheduling_mode = TaskSchedulingMode.FIXED

        if (
            request.answering_field == TaskClarificationField.START_TIME
            and interpretation.timing.start_time is None
        ):
            explicit_start_time = TaskTimeService.extract_explicit_start_time(
                request.latest_answer
            )
            if explicit_start_time is not None:
                timing_updates["start_time"] = explicit_start_time
                scheduling_mode = TaskSchedulingMode.FIXED

        if not timing_updates:
            return interpretation

        logger.info(
            "task_action_clarification_fallback_applied fields=%s",
            ",".join(timing_updates),
        )
        return interpretation.model_copy(
            update={
                "scheduling_mode": scheduling_mode,
                "timing": interpretation.timing.model_copy(
                    update=timing_updates
                ),
            }
        )

    @classmethod
    def _remaining_model_clarifications(
        cls,
        clarifications: list[TaskClarification],
        *,
        interpretation: TaskCreateInterpretation,
        timing: TaskTimingParseResult,
        timezone_available: bool,
    ) -> list[TaskClarification]:
        return [
            clarification
            for clarification in clarifications
            if not cls._clarification_is_resolved(
                clarification.field,
                interpretation=interpretation,
                timing=timing,
                timezone_available=timezone_available,
            )
        ]

    @classmethod
    def _clarification_is_resolved(
        cls,
        field: TaskClarificationField,
        *,
        interpretation: TaskCreateInterpretation,
        timing: TaskTimingParseResult,
        timezone_available: bool,
    ) -> bool:
        duration = cls._resolved_schedule_duration(timing)
        has_deadline = timing.due_date is not None
        has_schedule_intent = any(
            value is not None
            for value in (
                timing.requested_schedule_date,
                timing.requested_start_time,
                timing.requested_end_time,
            )
        )

        if field == TaskClarificationField.TASK_TITLE:
            return bool(interpretation.title.strip())
        if field == TaskClarificationField.DURATION:
            return duration is not None
        if field == TaskClarificationField.SCHEDULE_DATE:
            return has_deadline or timing.requested_schedule_date is not None
        if field == TaskClarificationField.START_TIME:
            return has_deadline or timing.requested_start_time is not None
        if field == TaskClarificationField.END_TIME:
            return has_deadline or (
                timing.requested_end_time is not None
                or (
                    timing.requested_start_time is not None
                    and duration is not None
                )
            )
        if field == TaskClarificationField.DUE_DATE:
            return has_deadline or has_schedule_intent
        if field == TaskClarificationField.SCHEDULE_OR_DUE:
            return has_deadline or timing.schedule is not None
        if field == TaskClarificationField.TIMEZONE:
            return timezone_available
        return False

    @staticmethod
    def _normalize_timing_input(
        scheduling_mode: TaskSchedulingMode,
        timing: TaskTimingInput,
    ) -> TaskTimingInput:
        """Normalize model-owned intent without reparsing the user sentence."""

        if scheduling_mode != TaskSchedulingMode.AUTOMATIC:
            return timing

        due_date = timing.due_date
        misplaced_deadline_time = (
            timing.end_time
            if timing.start_time is None
            else None
        )
        if misplaced_deadline_time is not None:
            deadline_date = (
                due_date.date()
                if due_date is not None
                else timing.schedule_date
            )
            if deadline_date is not None:
                due_date = datetime.combine(
                    deadline_date,
                    misplaced_deadline_time,
                )
                if timing.due_date is not None:
                    due_date = due_date.replace(
                        tzinfo=timing.due_date.tzinfo
                    )

        return timing.model_copy(
            update={
                "due_date": due_date,
                "schedule_date": None,
                "start_time": None,
                "end_time": None,
            }
        )

    def _localized_now(self, request: TaskActionPreviewRequest) -> datetime:
        now = self._now_factory()
        if now.tzinfo is None:
            now = now.astimezone()

        if request.timezone_name is not None:
            try:
                return now.astimezone(ZoneInfo(request.timezone_name))
            except ZoneInfoNotFoundError:
                logger.warning(
                    "task_action_timezone_fallback reason=unknown_timezone"
                )

        if request.utc_offset_minutes is not None:
            browser_timezone = timezone(
                timedelta(minutes=request.utc_offset_minutes)
            )
            return now.astimezone(browser_timezone)

        return now

    @staticmethod
    def _schedule_clarification(mode: str) -> TaskClarification:
        if mode == "fixed":
            return TaskClarification(
                field=TaskClarificationField.START_TIME,
                question=(
                    "The requested calendar time is unavailable. "
                    "When should StudentOS schedule it instead?"
                ),
            )
        return TaskClarification(
            field=TaskClarificationField.SCHEDULE_OR_DUE,
            question=(
                "There is not enough free time before the deadline. "
                "Should StudentOS change the duration or deadline?"
            ),
        )

    @staticmethod
    def _timing_clarification(question: str) -> TaskClarification:
        field_by_question = {
            "What date should this scheduled task occur?": (
                TaskClarificationField.SCHEDULE_DATE
            ),
            "What time should this scheduled task start?": (
                TaskClarificationField.START_TIME
            ),
            "What date should this task be due?": (
                TaskClarificationField.DUE_DATE
            ),
            "What time should this task be due?": (
                TaskClarificationField.DUE_DATE
            ),
            "The requested end time and duration do not match. "
            "Which one should StudentOS use?": (
                TaskClarificationField.END_TIME
            ),
            "The requested schedule ends after the task deadline. "
            "What should StudentOS change?": (
                TaskClarificationField.SCHEDULE_OR_DUE
            ),
        }
        return TaskClarification(
            field=field_by_question.get(
                question,
                TaskClarificationField.SCHEDULE_OR_DUE,
            ),
            question=question,
        )

    @staticmethod
    def _unique_clarifications(
        clarifications: list[TaskClarification],
    ) -> list[TaskClarification]:
        unique: list[TaskClarification] = []
        seen_fields: set[TaskClarificationField] = set()
        for clarification in clarifications:
            if clarification.field in seen_fields:
                continue
            seen_fields.add(clarification.field)
            unique.append(clarification)
        return unique

    @staticmethod
    def _proposal_context(
        proposal: TaskCreateProposal | None,
    ) -> dict[str, Any] | None:
        if proposal is None:
            return None

        return {
            "scheduling_mode": proposal.scheduling_mode.value,
            "task": {
                "title": proposal.task.title,
                "description": proposal.task.description,
                "suggested_importance": proposal.task.priority.name.lower(),
                "estimated_time_minutes": proposal.task.estimated_time,
                "task_type": proposal.task.task_type.value,
                "effort_level": proposal.task.effort_level.name.lower(),
                "recovery_buffer_minutes": (
                    proposal.task.recovery_buffer_minutes
                ),
                "splittable": proposal.task.splittable,
            },
            "timing": {
                "due_date": (
                    proposal.timing.due_date.isoformat()
                    if proposal.timing.due_date is not None
                    else None
                ),
                "schedule_date": (
                    proposal.timing.requested_schedule_date.isoformat()
                    if proposal.timing.requested_schedule_date is not None
                    else None
                ),
                "start_time": (
                    proposal.timing.requested_start_time.isoformat()
                    if proposal.timing.requested_start_time is not None
                    else None
                ),
                "end_time": (
                    proposal.timing.requested_end_time.isoformat()
                    if proposal.timing.requested_end_time is not None
                    else None
                ),
                "duration_minutes": proposal.timing.duration_minutes,
            },
            "pending_clarifications": [
                clarification.model_dump(mode="json")
                for clarification in proposal.pending_clarifications
            ],
        }

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
