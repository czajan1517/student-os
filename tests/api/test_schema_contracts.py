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


if __name__ == "__main__":
    unittest.main()
