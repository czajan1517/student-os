import unittest
from datetime import datetime, timedelta

from backend.database.models import Task
from backend.schemas.common import EffortLevel, PriorityLevel, TaskType
from backend.services.priority_service import PriorityService


class PriorityServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = PriorityService()
        self.now = datetime(2026, 8, 18, 12, 0)

    def make_task(self, task_id: int, **overrides):
        defaults = {
            "id": task_id,
            "title": f"Task {task_id}",
            "description": "",
            "priority": int(PriorityLevel.NORMAL),
            "estimated_time": 60,
            "task_type": TaskType.GENERAL.value,
            "effort_level": int(EffortLevel.MODERATE),
            "recovery_buffer_minutes": 15,
            "splittable": True,
            "due_date": None,
            "completed": False,
            "created_at": self.now,
            "updated_at": self.now,
        }
        defaults.update(overrides)
        return Task(**defaults)

    def test_explicit_importance_does_not_follow_raw_enum_order(self):
        high = self.make_task(1, priority=int(PriorityLevel.HIGH))
        low = self.make_task(2, priority=int(PriorityLevel.LOW))

        high_result = self.service.analyze_task(high, now=self.now)
        low_result = self.service.analyze_task(low, now=self.now)

        self.assertGreater(high_result.score, low_result.score)
        self.assertEqual(high_result.breakdown.importance, 40)
        self.assertEqual(low_result.breakdown.importance, 10)

    def test_analysis_returns_explainable_priority_factors(self):
        task = self.make_task(
            1,
            title="Prepare for chemistry final",
            priority=int(PriorityLevel.HIGH),
            estimated_time=180,
            task_type=TaskType.EXAM_PREPARATION.value,
            effort_level=int(EffortLevel.HEAVY),
            recovery_buffer_minutes=30,
            created_at=self.now - timedelta(days=4),
        )

        result = self.service.analyze_task(
            task,
            scheduled_minutes=60,
            now=self.now,
        )

        self.assertEqual(result.remaining_minutes, 120)
        self.assertEqual(result.effective_workload_minutes, 150)
        self.assertEqual(result.breakdown.importance, 40)
        self.assertEqual(result.breakdown.task_type, 15)
        self.assertEqual(result.breakdown.effort, 10)
        self.assertEqual(result.breakdown.workload, 6)
        self.assertEqual(result.breakdown.age, 4)
        self.assertEqual(result.score, 75)
        self.assertIn("Task has waited 4 day(s)", result.reasons)

    def test_rank_excludes_completed_and_fully_allocated_tasks(self):
        high = self.make_task(1, priority=int(PriorityLevel.HIGH))
        completed = self.make_task(2, completed=True)
        allocated = self.make_task(3, estimated_time=60)
        normal = self.make_task(4)

        ranked = self.service.rank_tasks(
            [normal, completed, allocated, high],
            scheduled_minutes_by_task={3: 60},
            now=self.now,
        )

        self.assertEqual([result.task_id for result in ranked], [1, 4])

    def test_age_prevents_equal_tasks_from_starving(self):
        newer = self.make_task(1, created_at=self.now - timedelta(days=1))
        older = self.make_task(2, created_at=self.now - timedelta(days=7))

        ranked = self.service.rank_tasks([newer, older], now=self.now)

        self.assertEqual([result.task_id for result in ranked], [2, 1])

    def test_completed_task_cannot_be_analyzed(self):
        task = self.make_task(1, completed=True)

        with self.assertRaisesRegex(ValueError, "Completed tasks"):
            self.service.analyze_task(task, now=self.now)


if __name__ == "__main__":
    unittest.main()
