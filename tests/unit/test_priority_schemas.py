import unittest
from datetime import datetime, timedelta

from pydantic import ValidationError

from backend.schemas.calendar import CalendarCreate
from backend.schemas.common import PriorityLevel
from backend.schemas.task import TaskCreate


class PrioritySchemaTests(unittest.TestCase):
    def test_task_defaults_are_ready_for_priority_scoring(self):
        task = TaskCreate(title="Review calculus notes")

        self.assertEqual(task.priority, PriorityLevel.NORMAL)
        self.assertEqual(task.estimated_time, 60)
        self.assertEqual(task.description, "")
        self.assertFalse(task.completed)

    def test_task_rejects_unknown_priority(self):
        with self.assertRaises(ValidationError):
            TaskCreate(title="Review calculus notes", priority=4)

    def test_task_rejects_non_positive_estimated_time(self):
        with self.assertRaises(ValidationError):
            TaskCreate(title="Review calculus notes", estimated_time=0)

    def test_calendar_event_requires_end_after_start(self):
        start = datetime.now()

        with self.assertRaises(ValidationError):
            CalendarCreate(
                title="Study session",
                start_date=start,
                end_date=start - timedelta(minutes=30),
            )


if __name__ == "__main__":
    unittest.main()
