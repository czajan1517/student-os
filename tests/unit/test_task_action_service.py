import json
import unittest
from datetime import date, datetime, time, timedelta, timezone
from types import SimpleNamespace

from backend.ai.task_action_service import (
    TaskActionNotReadyError,
    TaskActionPlanningError,
    TaskActionService,
)
from backend.schemas.ai import (
    SuggestedEffort,
    SuggestedImportance,
    TaskActionPreviewRequest,
    TaskClarification,
    TaskClarificationField,
    TaskCreateInterpretation,
    TaskSchedulingMode,
)
from backend.schemas.common import EffortLevel, PriorityLevel, TaskType
from backend.schemas.schedule import (
    TaskCreationScheduleBlock,
    TaskCreationSchedulePreview,
    TaskScheduleIntent,
    TaskTimingInput,
    TaskTimingParseResult,
)


class FakeOllamaClient:
    def __init__(self, content):
        self.content = content
        self.calls = []

    def chat(self, **kwargs):
        self.calls.append(kwargs)
        return self.content


class FakeTaskTimeService:
    def __init__(self, result):
        self.result = result
        self.inputs = []
        self.reference_times = []
        self.parse_calls = []

    def resolve(self, timing, *, reference_time=None):
        self.inputs.append(timing)
        self.reference_times.append(reference_time)
        return self.result

    def parse(self, message):
        self.parse_calls.append(message)
        raise AssertionError(
            "AI task creation must not reparse the raw user sentence"
        )


class FakeScheduleService:
    def __init__(self, preview):
        self.preview = preview
        self.preview_calls = []
        self.apply_calls = []

    def preview_task_creation(self, task, timing, now):
        self.preview_calls.append((task, timing, now))
        return self.preview

    def apply_task_creation(self, task, timing, now):
        self.apply_calls.append((task, timing, now))
        return SimpleNamespace(
            task=SimpleNamespace(id=1, title=task.title),
            created_events=[SimpleNamespace(id=1, task_id=1)],
            schedule=self.preview,
        )


class TaskActionServiceTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 8, 21, 12, 0, tzinfo=timezone.utc)
        self.deadline = datetime(2026, 8, 25, 9, 0, tzinfo=timezone.utc)

    def timing_input(self, **updates):
        result = TaskTimingInput(
            due_date=self.deadline,
            schedule_date=None,
            start_time=None,
            end_time=None,
            duration_minutes=180,
        )
        return result.model_copy(update=updates)

    def interpretation(self, *, timing_input=None, **updates):
        result = TaskCreateInterpretation(
            title="Finish database project",
            description="Complete the API documentation",
            suggested_importance=SuggestedImportance.HIGH,
            task_type=TaskType.PROJECT,
            effort_level=SuggestedEffort.HEAVY,
            recovery_buffer_minutes=20,
            splittable=True,
            scheduling_mode=TaskSchedulingMode.AUTOMATIC,
            timing=timing_input or self.timing_input(),
            confidence=0.9,
            reasons=["The project has a clear academic deadline"],
            assumptions=[],
            follow_up_questions=[],
        )
        return result.model_copy(update=updates)

    def timing(self, **updates):
        result = TaskTimingParseResult(
            due_date=self.deadline,
            duration_minutes=180,
        )
        return result.model_copy(update=updates)

    def schedule_preview(self, **updates):
        result = TaskCreationSchedulePreview(
            mode="automatic",
            deadline=self.deadline,
            estimated_minutes=180,
            available_minutes=240,
            proposed_blocks=[
                TaskCreationScheduleBlock(
                    start_date=datetime(
                        2026, 8, 24, 9, 0, tzinfo=timezone.utc
                    ),
                    end_date=datetime(
                        2026, 8, 24, 11, 0, tzinfo=timezone.utc
                    ),
                    duration_minutes=120,
                    buffer_after_minutes=20,
                    locked=False,
                ),
                TaskCreationScheduleBlock(
                    start_date=datetime(
                        2026, 8, 24, 11, 20, tzinfo=timezone.utc
                    ),
                    end_date=datetime(
                        2026, 8, 24, 12, 20, tzinfo=timezone.utc
                    ),
                    duration_minutes=60,
                    buffer_after_minutes=20,
                    locked=False,
                ),
            ],
            unscheduled_minutes=0,
            feasible=True,
            warnings=[
                "The scheduling window was limited by the task deadline"
            ],
        )
        return result.model_copy(update=updates)

    def service(
        self,
        *,
        interpretation=None,
        timing_result=None,
        schedule_preview=None,
    ):
        model_output = interpretation or self.interpretation()
        client = FakeOllamaClient(model_output.model_dump_json())
        time_service = FakeTaskTimeService(timing_result or self.timing())
        schedule_service = FakeScheduleService(
            schedule_preview or self.schedule_preview()
        )
        service = TaskActionService(
            client=client,
            model="test-action-model",
            schedule_service=schedule_service,
            task_time_service=time_service,
            now_factory=lambda: self.now,
        )
        return service, client, time_service, schedule_service

    def test_preview_combines_model_labels_with_backend_timing_without_writing(self):
        service, client, time_service, schedule_service = self.service()

        with self.assertLogs(
            "studentos.ai.task_action",
            level="INFO",
        ) as logs:
            proposal = service.preview_task_creation(
                TaskActionPreviewRequest(
                    message=(
                        "Create my database project due August 25 at 9 AM "
                        "for three hours"
                    )
                )
            )

        self.assertTrue(proposal.ready_to_apply)
        self.assertTrue(proposal.requires_confirmation)
        self.assertEqual(proposal.task.priority, PriorityLevel.HIGH)
        self.assertEqual(proposal.task.effort_level, EffortLevel.HEAVY)
        self.assertEqual(proposal.task.estimated_time, 180)
        self.assertEqual(proposal.task.due_date, self.deadline)
        self.assertEqual(proposal.timing.due_date, self.deadline)
        self.assertTrue(proposal.schedule_preview.feasible)
        self.assertEqual(len(schedule_service.preview_calls), 1)
        self.assertEqual(schedule_service.apply_calls, [])
        self.assertEqual(len(time_service.inputs), 1)
        self.assertEqual(time_service.parse_calls, [])

        call = client.calls[0]
        self.assertEqual(call["model"], "test-action-model")
        self.assertEqual(
            call["output_format"],
            TaskActionService._ollama_output_schema(),
        )
        self.assertNotIn("maxLength", str(call["output_format"]))
        self.assertIn("due_date", str(call["output_format"]))
        self.assertIn("duration_minutes", str(call["output_format"]))
        self.assertIn(
            "2026-08-21T12:00:00+00:00",
            call["messages"][1]["content"],
        )
        self.assertIn(
            'A short follow-up such as\n  "tomorrow" answers a schedule_date question',
            call["messages"][0]["content"],
        )
        self.assertIn(
            "Never return more than one follow-up question for the same field",
            call["messages"][0]["content"],
        )
        log_output = " ".join(logs.output)
        self.assertIn("task_action_preview_generated", log_output)
        self.assertIn("ready_to_apply=True", log_output)
        self.assertNotIn("Create my database project", log_output)
        self.assertNotIn("Finish database project", log_output)

    def test_missing_duration_blocks_apply_and_adds_a_question(self):
        interpretation = self.interpretation(
            timing_input=self.timing_input(duration_minutes=None),
            follow_up_questions=[],
        )
        timing = self.timing(duration_minutes=None)
        service, _client, _time_service, schedule_service = self.service(
            interpretation=interpretation,
            timing_result=timing,
        )

        proposal = service.preview_task_creation(
            TaskActionPreviewRequest(
                message="Create a project task due August 25"
            )
        )

        self.assertFalse(proposal.ready_to_apply)
        self.assertIsNone(proposal.task.estimated_time)
        self.assertIn("How many minutes", proposal.follow_up_questions[0])
        self.assertEqual(len(proposal.pending_clarifications), 1)
        self.assertEqual(
            proposal.pending_clarifications[0].field,
            TaskClarificationField.DURATION,
        )
        self.assertEqual(schedule_service.preview_calls, [])

    def test_automatic_mode_repairs_a_deadline_time_put_in_end_time(self):
        deadline = datetime(2026, 9, 17, 18, 0, tzinfo=timezone.utc)
        interpretation = self.interpretation(
            scheduling_mode=TaskSchedulingMode.AUTOMATIC,
            timing_input=TaskTimingInput(
                due_date=datetime(
                    2026,
                    9,
                    17,
                    0,
                    0,
                    tzinfo=timezone.utc,
                ),
                schedule_date=date(2026, 9, 17),
                start_time=None,
                end_time=time(18, 0),
                duration_minutes=90,
            ),
        )
        service, _client, time_service, _schedule_service = self.service(
            interpretation=interpretation,
            timing_result=self.timing(
                due_date=deadline,
                duration_minutes=90,
            ),
            schedule_preview=self.schedule_preview(
                deadline=deadline,
                estimated_minutes=90,
            ),
        )

        proposal = service.preview_task_creation(
            TaskActionPreviewRequest(
                message="Create a 90-minute task due September 17 at 6 PM"
            )
        )

        normalized = time_service.inputs[0]
        self.assertEqual(normalized.due_date, deadline)
        self.assertIsNone(normalized.schedule_date)
        self.assertIsNone(normalized.start_time)
        self.assertIsNone(normalized.end_time)
        self.assertTrue(proposal.ready_to_apply)

    def test_answering_field_and_latest_answer_are_sent_to_qwen(self):
        interpretation = self.interpretation(
            timing_input=self.timing_input(duration_minutes=None),
            follow_up_questions=[
                TaskClarification(
                    field=TaskClarificationField.DURATION,
                    question="How long should this task take?",
                )
            ],
        )
        service, client, time_service, schedule_service = self.service(
            interpretation=interpretation,
            timing_result=self.timing(duration_minutes=None),
        )
        initial = service.preview_task_creation(
            TaskActionPreviewRequest(message="Create a project task")
        )

        client.content = self.interpretation(
            timing_input=self.timing_input(duration_minutes=120)
        ).model_dump_json()
        time_service.result = self.timing(duration_minutes=120)
        schedule_service.preview = self.schedule_preview(
            estimated_minutes=120
        )
        revised = service.preview_task_creation(
            TaskActionPreviewRequest(
                message="two hours",
                current_proposal=initial,
                answering_field=TaskClarificationField.DURATION,
                latest_answer="two hours",
            )
        )

        sent_context = json.loads(client.calls[-1]["messages"][1]["content"])
        self.assertEqual(sent_context["answering_field"], "duration")
        self.assertEqual(sent_context["latest_answer"], "two hours")
        self.assertEqual(revised.follow_up_questions, [])

    def test_follow_up_revises_current_proposal_instead_of_reparsing_history(self):
        initial_interpretation = self.interpretation(
            timing_input=self.timing_input(duration_minutes=60)
        )
        initial_timing = self.timing(duration_minutes=60)
        initial_preview = self.schedule_preview(
            estimated_minutes=60,
            proposed_blocks=[
                TaskCreationScheduleBlock(
                    start_date=datetime(
                        2026, 8, 24, 9, 0, tzinfo=timezone.utc
                    ),
                    end_date=datetime(
                        2026, 8, 24, 10, 0, tzinfo=timezone.utc
                    ),
                    duration_minutes=60,
                    buffer_after_minutes=20,
                    locked=False,
                )
            ],
        )
        service, client, time_service, schedule_service = self.service(
            interpretation=initial_interpretation,
            timing_result=initial_timing,
            schedule_preview=initial_preview,
        )
        initial = service.preview_task_creation(
            TaskActionPreviewRequest(
                message="Create a one-hour database project due August 25"
            )
        )

        client.content = self.interpretation(
            timing_input=self.timing_input(duration_minutes=120)
        ).model_dump_json()
        time_service.result = self.timing(duration_minutes=120)
        schedule_service.preview = self.schedule_preview(
            estimated_minutes=120,
            proposed_blocks=[
                TaskCreationScheduleBlock(
                    start_date=datetime(
                        2026, 8, 24, 9, 0, tzinfo=timezone.utc
                    ),
                    end_date=datetime(
                        2026, 8, 24, 11, 0, tzinfo=timezone.utc
                    ),
                    duration_minutes=120,
                    buffer_after_minutes=20,
                    locked=False,
                )
            ],
        )

        revised = service.preview_task_creation(
            TaskActionPreviewRequest(
                message="Actually, make that two hours.",
                current_proposal=initial,
            )
        )

        self.assertEqual(revised.task.estimated_time, 120)
        self.assertEqual(time_service.inputs[-1].duration_minutes, 120)
        sent_context = json.loads(
            client.calls[-1]["messages"][1]["content"]
        )
        self.assertEqual(
            sent_context["latest_user_message"],
            "Actually, make that two hours.",
        )
        self.assertEqual(
            sent_context["current_proposal"]["timing"]["duration_minutes"],
            60,
        )
        self.assertEqual(
            sent_context["current_proposal"]["task"][
                "suggested_importance"
            ],
            "high",
        )

    def test_resolved_fields_remove_stale_model_questions(self):
        start_at = datetime(2026, 8, 21, 20, 30, tzinfo=timezone.utc)
        end_at = start_at + timedelta(hours=2)
        interpretation = self.interpretation(
            scheduling_mode=TaskSchedulingMode.FIXED,
            timing_input=self.timing_input(
                due_date=None,
                schedule_date=date(2026, 8, 21),
                start_time=time(20, 30),
                end_time=None,
                duration_minutes=120,
            ),
            follow_up_questions=[
                TaskClarification(
                    field=TaskClarificationField.SCHEDULE_DATE,
                    question="What date should this task occur?",
                ),
                TaskClarification(
                    field=TaskClarificationField.TIMEZONE,
                    question="What timezone should StudentOS use?",
                ),
            ],
        )
        timing = TaskTimingParseResult(
            requested_schedule_date=date(2026, 8, 21),
            requested_start_time=time(20, 30),
            duration_minutes=120,
            schedule=TaskScheduleIntent(
                start_at=start_at,
                end_at=end_at,
                locked=True,
            ),
        )
        preview = self.schedule_preview(
            mode="fixed",
            deadline=None,
            estimated_minutes=120,
            available_minutes=120,
            proposed_blocks=[
                TaskCreationScheduleBlock(
                    start_date=start_at,
                    end_date=end_at,
                    duration_minutes=120,
                    buffer_after_minutes=20,
                    locked=True,
                )
            ],
            warnings=[],
        )
        service, client, time_service, _schedule_service = self.service(
            interpretation=interpretation,
            timing_result=timing,
            schedule_preview=preview,
        )

        proposal = service.preview_task_creation(
            TaskActionPreviewRequest(
                message="Use my current timezone and schedule it tonight",
                timezone_name="Asia/Manila",
                utc_offset_minutes=480,
            )
        )

        self.assertTrue(proposal.ready_to_apply)
        self.assertEqual(proposal.follow_up_questions, [])
        localized_now = time_service.reference_times[0]
        self.assertEqual(localized_now.utcoffset(), timedelta(hours=8))
        self.assertEqual(localized_now.hour, 20)
        sent_context = json.loads(client.calls[0]["messages"][1]["content"])
        self.assertEqual(sent_context["browser_timezone"], "Asia/Manila")
        self.assertEqual(sent_context["utc_offset_minutes"], 480)

    def test_missing_deadline_and_schedule_blocks_apply(self):
        interpretation = self.interpretation(
            timing_input=self.timing_input(
                due_date=None,
                duration_minutes=180,
            )
        )
        timing = TaskTimingParseResult(duration_minutes=180)
        service, _client, _time_service, schedule_service = self.service(
            interpretation=interpretation,
            timing_result=timing,
        )

        proposal = service.preview_task_creation(
            TaskActionPreviewRequest(
                message="Create a three-hour project task"
            )
        )

        self.assertFalse(proposal.ready_to_apply)
        self.assertIsNone(proposal.task.due_date)
        self.assertIsNone(proposal.schedule_preview)
        self.assertIn(
            "When should this task be scheduled or due?",
            proposal.follow_up_questions,
        )
        self.assertEqual(schedule_service.preview_calls, [])

    def test_backend_resolution_is_used_after_model_interpretation(self):
        interpretation = self.interpretation(
            timing_input=self.timing_input(duration_minutes=30)
        )
        timing = self.timing(duration_minutes=180)
        service, _client, _time_service, _schedule_service = self.service(
            interpretation=interpretation,
            timing_result=timing,
        )

        proposal = service.preview_task_creation(
            TaskActionPreviewRequest(
                message=(
                    "Finish it by August 25 at 9 AM; "
                    "it takes three hours"
                )
            )
        )

        self.assertEqual(proposal.task.estimated_time, 180)
        self.assertEqual(proposal.task.due_date, self.deadline)

    def test_per_session_duration_is_not_treated_as_total_duration(self):
        interpretation = self.interpretation(
            timing_input=self.timing_input(duration_minutes=None)
        )
        timing = TaskTimingParseResult(due_date=self.deadline)
        service, _client, _time_service, schedule_service = self.service(
            interpretation=interpretation,
            timing_result=timing,
        )

        proposal = service.preview_task_creation(
            TaskActionPreviewRequest(
                message="Split this into two hours per session"
            )
        )

        self.assertIsNone(proposal.task.estimated_time)
        self.assertFalse(proposal.ready_to_apply)
        self.assertEqual(schedule_service.preview_calls, [])

    def test_infeasible_schedule_adds_a_clarification(self):
        infeasible = self.schedule_preview(
            proposed_blocks=[],
            unscheduled_minutes=180,
            feasible=False,
            warnings=[
                "180 minutes could not be scheduled before the deadline"
            ],
        )
        service, _client, _time_service, _schedule_service = self.service(
            schedule_preview=infeasible
        )

        proposal = service.preview_task_creation(
            TaskActionPreviewRequest(
                message=(
                    "Create a three-hour project due August 25 at 9 AM"
                )
            )
        )

        self.assertFalse(proposal.ready_to_apply)
        self.assertIn(
            "There is not enough free time before the deadline. "
            "Should StudentOS change the duration or deadline?",
            proposal.follow_up_questions,
        )

    def test_invalid_model_output_is_rejected(self):
        service = TaskActionService(
            client=FakeOllamaClient("not json"),
            model="test-action-model",
        )

        with self.assertRaisesRegex(
            TaskActionPlanningError,
            "preview request failed",
        ):
            service.preview_task_creation(
                TaskActionPreviewRequest(message="Create a task")
            )

    def test_model_output_with_an_empty_title_is_rejected(self):
        interpretation = self.interpretation(title="")
        service, _client, _time_service, _schedule_service = self.service(
            interpretation=interpretation
        )

        with self.assertRaisesRegex(
            TaskActionPlanningError,
            "preview request failed",
        ):
            service.preview_task_creation(
                TaskActionPreviewRequest(message="Create a task")
            )

    def test_apply_uses_schedule_service_without_calling_qwen_again(self):
        service, client, _time_service, schedule_service = self.service()
        proposal = service.preview_task_creation(
            TaskActionPreviewRequest(
                message=(
                    "Create the project task due August 25 at 9 AM"
                )
            )
        )

        result = service.apply_task_creation(proposal)

        self.assertEqual(result.task.title, "Finish database project")
        self.assertEqual(len(schedule_service.apply_calls), 1)
        self.assertEqual(len(client.calls), 1)

    def test_apply_rejects_a_proposal_that_needs_information(self):
        service, _client, _time_service, schedule_service = self.service()
        proposal = service.preview_task_creation(
            TaskActionPreviewRequest(
                message=(
                    "Create the project task due August 25 at 9 AM"
                )
            )
        ).model_copy(update={"ready_to_apply": False})

        with self.assertRaisesRegex(
            TaskActionNotReadyError,
            "more information",
        ):
            service.apply_task_creation(proposal)

        self.assertEqual(schedule_service.apply_calls, [])


if __name__ == "__main__":
    unittest.main()
