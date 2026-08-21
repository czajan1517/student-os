import unittest
from unittest.mock import patch

from backend.ai.task_classifier import (
    TaskClassificationError,
    TaskClassifier,
)
from backend.schemas.ai import (
    SuggestedEffort,
    SuggestedImportance,
    TaskClassification,
    TaskClassificationRequest,
)
from backend.schemas.common import TaskType


class FakeOllamaClient:
    def __init__(self, content):
        self.content = content
        self.calls = []

    def chat(self, **kwargs):
        self.calls.append(kwargs)
        return self.content


class TaskClassifierTests(unittest.TestCase):
    def classification(self):
        return TaskClassification(
            task_type=TaskType.EXAM_PREPARATION,
            effort_level=SuggestedEffort.HEAVY,
            suggested_importance=SuggestedImportance.HIGH,
            estimated_time_minutes=180,
            recovery_buffer_minutes=20,
            splittable=True,
            confidence=0.9,
            reasons=["The task prepares for an exam"],
            assumptions=["The chapters have moderate difficulty"],
            follow_up_questions=[],
        )

    def test_classify_task_uses_structured_output_without_writing(self):
        expected = self.classification()
        client = FakeOllamaClient(expected.model_dump_json())
        classifier = TaskClassifier(
            client=client,
            model="test-classifier-model",
        )
        request = TaskClassificationRequest(
            title="Study four chapters for chemistry",
            description="Final exam next week",
        )

        result = classifier.classify_task(request)

        self.assertEqual(result, expected)
        call = client.calls[0]
        self.assertEqual(call["model"], "test-classifier-model")
        self.assertEqual(
            call["output_format"],
            TaskClassification.model_json_schema(),
        )
        self.assertEqual(
            call["options"],
            {"temperature": 0, "num_predict": 512},
        )
        self.assertIs(call["think"], False)
        self.assertEqual(call["messages"][0]["role"], "system")
        self.assertEqual(call["messages"][1]["role"], "user")
        self.assertNotIn("priority score", result.reasons[0].lower())

    def test_user_supplied_duration_overrides_the_model_suggestion(self):
        model_result = self.classification().model_copy(
            update={"estimated_time_minutes": None}
        )
        classifier = TaskClassifier(
            client=FakeOllamaClient(model_result.model_dump_json()),
            model="test-classifier-model",
        )

        result = classifier.classify_task(
            TaskClassificationRequest(
                title="Finish project",
                estimated_time_minutes=180,
            )
        )

        self.assertEqual(result.estimated_time_minutes, 180)

    def test_classify_task_rejects_invalid_model_json(self):
        classifier = TaskClassifier(
            client=FakeOllamaClient("not valid JSON"),
            model="test-classifier-model",
        )

        with self.assertRaisesRegex(
            TaskClassificationError,
            "request failed",
        ):
            classifier.classify_task(
                TaskClassificationRequest(title="Ambiguous task")
            )

    def test_model_override_is_resolved_lazily_from_environment(self):
        client = FakeOllamaClient(self.classification().model_dump_json())
        classifier = TaskClassifier(client=client)

        with patch.dict(
            "os.environ",
            {"OLLAMA_TASK_CLASSIFIER_MODEL": "environment-model"},
        ):
            classifier.classify_task(
                TaskClassificationRequest(title="Read notes")
            )

        call = client.calls[0]
        self.assertEqual(call["model"], "environment-model")


if __name__ == "__main__":
    unittest.main()
