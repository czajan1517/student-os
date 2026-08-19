import unittest
from types import SimpleNamespace
from unittest.mock import patch

from backend.ai.task_classifier import (
    AIConfigurationError,
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


class FakeResponses:
    def __init__(self, parsed):
        self.parsed = parsed
        self.calls = []

    def parse(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(output_parsed=self.parsed)


class FakeOpenAIClient:
    def __init__(self, parsed):
        self.responses = FakeResponses(parsed)


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
        client = FakeOpenAIClient(expected)
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
        call = client.responses.calls[0]
        self.assertEqual(call["model"], "test-classifier-model")
        self.assertIs(call["text_format"], TaskClassification)
        self.assertFalse(call["store"])
        self.assertNotIn("priority score", result.reasons[0].lower())

    def test_classify_task_rejects_an_empty_parsed_response(self):
        classifier = TaskClassifier(
            client=FakeOpenAIClient(None),
            model="test-classifier-model",
        )

        with self.assertRaisesRegex(
            TaskClassificationError,
            "did not return",
        ):
            classifier.classify_task(
                TaskClassificationRequest(title="Ambiguous task")
            )

    def test_missing_api_key_does_not_break_application_import(self):
        classifier = TaskClassifier(model="test-classifier-model")

        with patch.dict("os.environ", {"OPENAI_API_KEY": ""}):
            with self.assertRaisesRegex(AIConfigurationError, "not configured"):
                classifier.classify_task(
                    TaskClassificationRequest(title="Read notes")
                )

    def test_model_override_is_resolved_lazily_from_environment(self):
        client = FakeOpenAIClient(self.classification())
        classifier = TaskClassifier(client=client)

        with patch.dict(
            "os.environ",
            {"OPENAI_TASK_CLASSIFIER_MODEL": "environment-model"},
        ):
            classifier.classify_task(
                TaskClassificationRequest(title="Read notes")
            )

        call = client.responses.calls[0]
        self.assertEqual(call["model"], "environment-model")


if __name__ == "__main__":
    unittest.main()
