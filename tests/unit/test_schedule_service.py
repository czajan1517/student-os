import unittest
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.database.models import Base, CalendarEvent, Task
from backend.schemas.schedule import TaskScheduleIntent, TaskTimingParseResult
from backend.schemas.task import TaskCreate
from backend.services.schedule_service import (
    ScheduleService,
    TaskCreationScheduleConflictError,
    TimeInterval,
)


class ScheduleServiceTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = TemporaryDirectory()
        database_path = Path(self.temporary_directory.name) / "schedule.db"
        self.engine = create_engine(
            f"sqlite:///{database_path.as_posix()}",
            connect_args={"check_same_thread": False},
        )
        Base.metadata.create_all(bind=self.engine)
        self.session_factory = sessionmaker(bind=self.engine)
        self.service = ScheduleService(
            session_factory=self.session_factory
        )
        self.now = datetime(2026, 9, 10, 8, 0)

    def tearDown(self):
        Base.metadata.drop_all(bind=self.engine)
        self.engine.dispose()
        self.temporary_directory.cleanup()

    @staticmethod
    def task(**updates):
        values = {
            "title": "Review mathematics",
            "description": "Practice the assigned problem set",
            "estimated_time": 60,
            "due_date": datetime(2026, 9, 10, 12, 0),
            "recovery_buffer_minutes": 15,
        }
        values.update(updates)
        return TaskCreate(**values)

    @staticmethod
    def fixed_timing(**updates):
        start_at = datetime(2026, 9, 10, 9, 0)
        end_at = datetime(2026, 9, 10, 10, 0)
        values = {
            "due_date": datetime(2026, 9, 10, 12, 0),
            "requested_schedule_date": start_at.date(),
            "requested_start_time": start_at.time(),
            "requested_end_time": end_at.time(),
            "duration_minutes": 60,
            "schedule": TaskScheduleIntent(
                start_at=start_at,
                end_at=end_at,
                locked=True,
            ),
        }
        values.update(updates)
        return TaskTimingParseResult(**values)

    def test_merge_intervals_combines_overlapping_and_adjacent_time(self):
        intervals = [
            TimeInterval(
                datetime(2026, 9, 10, 9, 0),
                datetime(2026, 9, 10, 10, 0),
            ),
            TimeInterval(
                datetime(2026, 9, 10, 9, 30),
                datetime(2026, 9, 10, 11, 0),
            ),
            TimeInterval(
                datetime(2026, 9, 10, 11, 0),
                datetime(2026, 9, 10, 11, 30),
            ),
        ]

        merged = ScheduleService._merge_intervals(intervals)

        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0].start, datetime(2026, 9, 10, 9, 0))
        self.assertEqual(merged[0].end, datetime(2026, 9, 10, 11, 30))

    def test_allocate_blocks_reserves_recovery_time(self):
        free_intervals = [
            TimeInterval(
                datetime(2026, 9, 10, 9, 0),
                datetime(2026, 9, 10, 12, 0),
            )
        ]

        blocks, remaining = ScheduleService._allocate_blocks(
            free_intervals=free_intervals,
            required_minutes=150,
            minimum_block_minutes=30,
            maximum_block_minutes=90,
            recovery_buffer_minutes=15,
        )

        self.assertEqual(remaining, 0)
        self.assertEqual([block.duration_minutes for block in blocks], [90, 60])
        self.assertEqual(
            blocks[1].start_date,
            datetime(2026, 9, 10, 10, 45),
        )

    def test_task_creation_preview_does_not_write(self):
        preview = self.service.preview_task_creation(
            self.task(),
            self.fixed_timing(),
            self.now,
        )

        self.assertTrue(preview.feasible)
        self.assertEqual(preview.mode, "fixed")
        with self.session_factory() as db:
            self.assertEqual(db.query(Task).count(), 0)
            self.assertEqual(db.query(CalendarEvent).count(), 0)

    def test_fixed_apply_creates_task_and_locked_linked_event(self):
        result = self.service.apply_task_creation(
            self.task(),
            self.fixed_timing(),
            self.now,
        )

        self.assertEqual(len(result.created_events), 1)
        event = result.created_events[0]
        self.assertEqual(event.task_id, result.task.id)
        self.assertTrue(event.locked)
        self.assertEqual(event.start_date, datetime(2026, 9, 10, 9, 0))
        self.assertEqual(event.end_date, datetime(2026, 9, 10, 10, 0))

        with self.session_factory() as db:
            self.assertEqual(db.query(Task).count(), 1)
            self.assertEqual(db.query(CalendarEvent).count(), 1)

    def test_automatic_apply_creates_movable_linked_event(self):
        task = self.task(estimated_time=90)
        timing = TaskTimingParseResult(
            due_date=task.due_date,
            duration_minutes=90,
        )

        preview = self.service.preview_task_creation(
            task,
            timing,
            self.now,
        )
        result = self.service.apply_task_creation(
            task,
            timing,
            self.now,
        )

        self.assertEqual(preview.mode, "automatic")
        self.assertTrue(preview.feasible)
        self.assertTrue(result.created_events)
        self.assertTrue(
            all(not event.locked for event in result.created_events)
        )
        self.assertTrue(
            all(
                event.task_id == result.task.id
                for event in result.created_events
            )
        )
        self.assertLessEqual(
            result.created_events[-1].end_date,
            task.due_date,
        )

    def test_fixed_conflict_rejects_apply_without_creating_task(self):
        preview = self.service.preview_task_creation(
            self.task(),
            self.fixed_timing(),
            self.now,
        )
        self.assertTrue(preview.feasible)

        with self.session_factory() as db:
            db.add(
                CalendarEvent(
                    title="Existing class",
                    description="",
                    priority=0,
                    locked=True,
                    buffer_after_minutes=0,
                    start_date=datetime(2026, 9, 10, 9, 30),
                    end_date=datetime(2026, 9, 10, 10, 30),
                )
            )
            db.commit()

        with self.assertRaises(TaskCreationScheduleConflictError):
            self.service.apply_task_creation(
                self.task(),
                self.fixed_timing(),
                self.now,
            )

        with self.session_factory() as db:
            self.assertEqual(db.query(Task).count(), 0)
            self.assertEqual(db.query(CalendarEvent).count(), 1)

    def test_commit_failure_rolls_back_task_and_event_together(self):
        failing_session = self.session_factory()
        service = ScheduleService(
            session_factory=lambda: failing_session
        )

        with patch.object(
            failing_session,
            "commit",
            side_effect=RuntimeError("simulated commit failure"),
        ):
            with self.assertRaisesRegex(
                RuntimeError,
                "simulated commit failure",
            ):
                service.apply_task_creation(
                    self.task(),
                    self.fixed_timing(),
                    self.now,
                )

        with self.session_factory() as db:
            self.assertEqual(db.query(Task).count(), 0)
            self.assertEqual(db.query(CalendarEvent).count(), 0)


if __name__ == "__main__":
    unittest.main()
