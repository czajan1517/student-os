import os
import tempfile
import unittest
from pathlib import Path


TEST_DIRECTORY = tempfile.TemporaryDirectory()
TEST_DATABASE_PATH = Path(TEST_DIRECTORY.name) / "studentos-test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DATABASE_PATH.as_posix()}"

from fastapi.testclient import TestClient  # noqa: E402

from backend.database.database import engine  # noqa: E402
from backend.database.models import Base  # noqa: E402
from backend.main import app  # noqa: E402


class ApiSchemaContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        cls.client.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()
        TEST_DIRECTORY.cleanup()

    def test_task_priority_is_numeric_and_completed_is_persisted(self):
        response = self.client.post(
            "/tasks",
            json={
                "title": "Finish the priority engine",
                "priority": 1,
                "estimated_time": 90,
                "completed": True,
            },
        )

        self.assertEqual(response.status_code, 201)
        task = response.json()
        self.assertEqual(task["priority"], 1)
        self.assertIsInstance(task["priority"], int)
        self.assertTrue(task["completed"])

    def test_task_rejects_priority_outside_the_enum(self):
        response = self.client.post(
            "/tasks",
            json={"title": "Invalid priority", "priority": 9},
        )

        self.assertEqual(response.status_code, 422)

    def test_calendar_update_rejects_invalid_date_order(self):
        created = self.client.post(
            "/calendar_events",
            json={
                "title": "Valid event",
                "start_date": "2026-08-15T10:00:00",
                "end_date": "2026-08-15T11:00:00",
                "priority": 2,
            },
        )
        self.assertEqual(created.status_code, 201)

        event_id = created.json()["id"]
        response = self.client.put(
            f"/calendar_events/{event_id}",
            json={"end_date": "2026-08-15T09:00:00"},
        )

        self.assertEqual(response.status_code, 422)

    def test_schedule_preview_works_around_anchor_and_recovery_buffer(self):
        task = self.client.post(
            "/tasks",
            json={
                "title": "Prepare presentation",
                "estimated_time": 90,
                "due_date": "2026-09-10T12:00:00",
            },
        ).json()
        anchor = self.client.post(
            "/calendar_events",
            json={
                "title": "Anchored class",
                "start_date": "2026-09-10T09:00:00",
                "end_date": "2026-09-10T10:00:00",
                "buffer_after_minutes": 15,
            },
        )
        self.assertEqual(anchor.status_code, 201)
        self.assertTrue(anchor.json()["locked"])

        response = self.client.post(
            "/schedule/preview",
            json={
                "task_id": task["id"],
                "window_start": "2026-09-10T08:00:00",
                "window_end": "2026-09-10T12:00:00",
                "minimum_block_minutes": 30,
                "maximum_block_minutes": 90,
                "recovery_buffer_minutes": 15,
            },
        )

        self.assertEqual(response.status_code, 200)
        preview = response.json()
        self.assertTrue(preview["feasible"])
        self.assertEqual(preview["unscheduled_minutes"], 0)
        self.assertEqual(
            sum(block["duration_minutes"] for block in preview["proposed_blocks"]),
            90,
        )
        self.assertGreaterEqual(
            preview["proposed_blocks"][1]["start_date"],
            "2026-09-10T10:15:00",
        )

    def test_schedule_apply_creates_movable_task_blocks(self):
        task = self.client.post(
            "/tasks",
            json={
                "title": "Write lab notes",
                "estimated_time": 60,
                "due_date": "2026-09-11T17:00:00",
            },
        ).json()

        response = self.client.post(
            "/schedule/apply",
            json={
                "task_id": task["id"],
                "window_start": "2026-09-11T08:00:00",
                "window_end": "2026-09-11T17:00:00",
                "recovery_buffer_minutes": 15,
            },
        )

        self.assertEqual(response.status_code, 201)
        result = response.json()
        self.assertTrue(result["feasible"])
        self.assertEqual(len(result["created_events"]), 1)
        event = result["created_events"][0]
        self.assertEqual(event["task_id"], task["id"])
        self.assertFalse(event["locked"])
        self.assertEqual(event["buffer_after_minutes"], 15)

        deleted = self.client.delete(f"/tasks/{task['id']}")
        self.assertEqual(deleted.status_code, 200)
        removed_event = self.client.get(f"/calendar_events/{event['id']}")
        self.assertEqual(removed_event.status_code, 404)

    def test_schedule_relaxes_recovery_only_when_needed_for_feasibility(self):
        task = self.client.post(
            "/tasks",
            json={
                "title": "Deadline-sensitive task",
                "estimated_time": 60,
                "due_date": "2026-09-14T09:00:00",
            },
        ).json()

        response = self.client.post(
            "/schedule/preview",
            json={
                "task_id": task["id"],
                "window_start": "2026-09-14T08:00:00",
                "window_end": "2026-09-14T12:00:00",
                "recovery_buffer_minutes": 15,
            },
        )

        self.assertEqual(response.status_code, 200)
        preview = response.json()
        self.assertTrue(preview["feasible"])
        self.assertEqual(preview["proposed_blocks"][0]["buffer_after_minutes"], 0)
        self.assertIn(
            "Recovery buffers were reduced to protect the deadline",
            preview["warnings"],
        )

    def test_schedule_counts_existing_blocks_outside_the_preview_window(self):
        task = self.client.post(
            "/tasks",
            json={
                "title": "Partially allocated task",
                "estimated_time": 120,
                "due_date": "2026-09-15T17:00:00",
            },
        ).json()
        linked_event = self.client.post(
            "/calendar_events",
            json={
                "title": "Later work block",
                "task_id": task["id"],
                "locked": False,
                "start_date": "2026-09-15T15:00:00",
                "end_date": "2026-09-15T16:00:00",
            },
        )
        self.assertEqual(linked_event.status_code, 201)

        preview = self.client.post(
            "/schedule/preview",
            json={
                "task_id": task["id"],
                "window_start": "2026-09-15T08:00:00",
                "window_end": "2026-09-15T12:00:00",
                "recovery_buffer_minutes": 0,
            },
        ).json()

        self.assertEqual(preview["already_scheduled_minutes"], 60)
        self.assertEqual(preview["minutes_to_schedule"], 60)
        self.assertEqual(
            sum(block["duration_minutes"] for block in preview["proposed_blocks"]),
            60,
        )

    def test_event_recovery_buffer_blocks_the_start_of_a_window(self):
        task = self.client.post(
            "/tasks",
            json={
                "title": "Task after an exhausting event",
                "estimated_time": 30,
                "due_date": "2026-09-16T09:00:00",
            },
        ).json()
        anchor = self.client.post(
            "/calendar_events",
            json={
                "title": "Early anchored event",
                "start_date": "2026-09-16T07:30:00",
                "end_date": "2026-09-16T08:00:00",
                "buffer_after_minutes": 30,
            },
        )
        self.assertEqual(anchor.status_code, 201)

        preview = self.client.post(
            "/schedule/preview",
            json={
                "task_id": task["id"],
                "window_start": "2026-09-16T08:15:00",
                "window_end": "2026-09-16T09:00:00",
                "recovery_buffer_minutes": 0,
            },
        ).json()

        self.assertTrue(preview["feasible"])
        self.assertEqual(
            preview["proposed_blocks"][0]["start_date"],
            "2026-09-16T08:30:00",
        )

    def test_schedule_apply_rejects_an_infeasible_window_without_writing(self):
        task = self.client.post(
            "/tasks",
            json={
                "title": "Impossible workload",
                "estimated_time": 240,
                "due_date": "2026-09-12T09:00:00",
            },
        ).json()

        response = self.client.post(
            "/schedule/apply",
            json={
                "task_id": task["id"],
                "window_start": "2026-09-12T08:00:00",
                "window_end": "2026-09-12T12:00:00",
                "recovery_buffer_minutes": 0,
            },
        )

        self.assertEqual(response.status_code, 409)
        preview = response.json()["detail"]["preview"]
        self.assertFalse(preview["feasible"])
        self.assertEqual(preview["unscheduled_minutes"], 180)
        linked_events = [
            event
            for event in self.client.get("/calendar_events").json()
            if event["task_id"] == task["id"]
        ]
        self.assertEqual(linked_events, [])

    def test_calendar_event_rejects_a_missing_linked_task(self):
        response = self.client.post(
            "/calendar_events",
            json={
                "title": "Orphaned block",
                "task_id": 999999,
                "start_date": "2026-09-13T10:00:00",
                "end_date": "2026-09-13T11:00:00",
            },
        )

        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
