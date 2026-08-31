import unittest
from datetime import datetime, timezone

from backend.ai.task_action_service import (
    TaskActionNotReadyError,
    TaskActionPlanningError,
    TaskActionService,
)
from backend.schemas.ai import (
    SuggestedEffort,
    SuggestedImportance,
    TaskActionPreviewRequest,
    TaskCreateInterpretation,
)
from backend.schemas.common import EffortLevel, PriorityLevel, TaskType


class FakeOllamaClient:
    def __init__(self, content):
        self.content = content
        self.calls = []

    def chat(self, **kwargs):
        self.calls.append(kwargs)
        return self.content


class FakeTaskService:
    def __init__(self):
        self.created_tasks = []

    def create_task(self, task):
        self.created_tasks.append(task)
        return task


class TaskActionServiceTests(unittest.TestCase):
    def interpretation(self, **updates):
        result = TaskCreateInterpretation(
            title="Finish database project",
            description="Complete the API documentation",
            suggested_importance=SuggestedImportance.HIGH,
            estimated_time_minutes=180,
            task_type=TaskType.PROJECT,
            effort_level=SuggestedEffort.HEAVY,
            recovery_buffer_minutes=20,
            splittable=True,
            due_date="2026-08-25T09:00:00+08:00",
            confidence=0.9,
            reasons=["The project has a clear academic deadline"],
            assumptions=[],
            follow_up_questions=[],
        )
        return result.model_copy(update=updates)

    def service(self, interpretation=None, task_service=None):
        model_output = interpretation or self.interpretation()
        client = FakeOllamaClient(model_output.model_dump_json())
        service = TaskActionService(
            client=client,
            model="test-action-model",
            task_service=task_service or FakeTaskService(),
            now_factory=lambda: datetime(
                2026,
                8,
                21,
                12,
                0,
                tzinfo=timezone.utc,
            ),
        )
        return service, client

    def test_preview_maps_model_labels_without_writing(self):
        task_service = FakeTaskService()
        service, client = self.service(task_service=task_service)

        with self.assertLogs(
            "studentos.ai.task_action",
            level="INFO",
        ) as logs:
            proposal = service.preview_task_creation(
                TaskActionPreviewRequest(
                    message="Create my database project task"
                )
            )

        self.assertTrue(proposal.ready_to_apply)
        self.assertTrue(proposal.requires_confirmation)
        self.assertEqual(proposal.task.priority, PriorityLevel.HIGH)
        self.assertEqual(proposal.task.effort_level, EffortLevel.HEAVY)
        self.assertEqual(proposal.task.estimated_time, 180)
        self.assertFalse(proposal.task.completed)
        self.assertEqual(task_service.created_tasks, [])

        call = client.calls[0]
        self.assertEqual(call["model"], "test-action-model")
        self.assertEqual(
            call["output_format"],
            TaskActionService._ollama_output_schema(),
        )
        self.assertNotIn(
            "maxLength",
            str(call["output_format"]),
        )
        self.assertIn("2026-08-21T12:00:00+00:00", call["messages"][1]["content"])
        log_output = " ".join(logs.output)
        self.assertIn("task_action_preview_generated", log_output)
        self.assertIn("ready_to_apply=True", log_output)
        self.assertNotIn("Create my database project task", log_output)
        self.assertNotIn("Finish database project", log_output)

    def test_missing_duration_blocks_apply_and_adds_a_question(self):
        interpretation = self.interpretation(
            estimated_time_minutes=None,
            follow_up_questions=[],
        )
        service, _client = self.service(interpretation=interpretation)

        proposal = service.preview_task_creation(
            TaskActionPreviewRequest(message="Create a project task")
        )

        self.assertFalse(proposal.ready_to_apply)
        self.assertIsNone(proposal.task.estimated_time)
        self.assertIn("How many minutes", proposal.follow_up_questions[0])

    def test_invalid_due_date_blocks_apply(self):
        interpretation = self.interpretation(due_date="sometime Friday")
        service, _client = self.service(interpretation=interpretation)

        proposal = service.preview_task_creation(
            TaskActionPreviewRequest(message="Create a project task")
        )

        self.assertFalse(proposal.ready_to_apply)
        self.assertIsNone(proposal.task.due_date)
        self.assertIn("exact date", proposal.follow_up_questions[0])

    def test_explicit_duration_and_clock_time_override_model_mistakes(self):
        interpretation = self.interpretation(
            estimated_time_minutes=None,
            due_date="2026-08-25T00:00:00",
        )
        service, _client = self.service(interpretation=interpretation)

        proposal = service.preview_task_creation(
            TaskActionPreviewRequest(
                message="Finish it by August 25 at 9 AM; it takes 3 hours"
            )
        )

        self.assertEqual(proposal.task.estimated_time, 180)
        self.assertEqual(proposal.task.due_date.hour, 9)

    def test_per_session_duration_is_not_treated_as_total_duration(self):
        interpretation = self.interpretation(
            estimated_time_minutes=None,
            due_date="",
        )
        service, _client = self.service(interpretation=interpretation)

        proposal = service.preview_task_creation(
            TaskActionPreviewRequest(
                message="Split this into 2 hours per session"
            )
        )

        self.assertIsNone(proposal.task.estimated_time)
        self.assertFalse(proposal.ready_to_apply)

    def test_invalid_model_output_is_rejected(self):
        service = TaskActionService(
            client=FakeOllamaClient("not json"),
            model="test-action-model",
        )

        with self.assertRaisesRegex(TaskActionPlanningError, "preview request failed"):
            service.preview_task_creation(
                TaskActionPreviewRequest(message="Create a task")
            )

    def test_model_output_with_an_empty_title_is_rejected(self):
        interpretation = self.interpretation(title="")
        service, _client = self.service(interpretation=interpretation)

        with self.assertRaisesRegex(
            TaskActionPlanningError,
            "preview request failed",
        ):
            service.preview_task_creation(
                TaskActionPreviewRequest(message="Create a task")
            )

    def test_apply_uses_task_service_without_calling_qwen_again(self):
        task_service = FakeTaskService()
        service, client = self.service(task_service=task_service)
        proposal = service.preview_task_creation(
            TaskActionPreviewRequest(message="Create the project task")
        )

        result = service.apply_task_creation(proposal)

        self.assertEqual(result.title, "Finish database project")
        self.assertEqual(len(task_service.created_tasks), 1)
        self.assertEqual(len(client.calls), 1)

    def test_apply_rejects_a_proposal_that_needs_information(self):
        task_service = FakeTaskService()
        service, _client = self.service(task_service=task_service)
        proposal = service.preview_task_creation(
            TaskActionPreviewRequest(message="Create the project task")
        ).model_copy(update={"ready_to_apply": False})

        with self.assertRaisesRegex(TaskActionNotReadyError, "more information"):
            service.apply_task_creation(proposal)

        self.assertEqual(task_service.created_tasks, [])


if __name__ == "__main__":
    unittest.main()
