import logging
import tempfile
import unittest
from pathlib import Path

from backend.logging_config import configure_logging


class LoggingConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()

    def tearDown(self):
        configure_logging()
        self.temporary_directory.cleanup()

    @staticmethod
    def _flush_handlers():
        for handler in logging.getLogger("studentos").handlers:
            handler.flush()

    def test_configure_logging_writes_application_events_to_a_file(self):
        log_file = (
            Path(self.temporary_directory.name) / "studentos-test.log"
        )
        configure_logging(
            level="INFO",
            log_file=log_file,
            enable_console=False,
        )

        logging.getLogger("studentos.example").info(
            "example_event item_id=%s",
            42,
        )
        self._flush_handlers()

        content = log_file.read_text(encoding="utf-8")
        self.assertIn("INFO studentos.example", content)
        self.assertIn("example_event item_id=42", content)

    def test_reconfiguring_logging_does_not_duplicate_handlers(self):
        log_file = (
            Path(self.temporary_directory.name) / "studentos-test.log"
        )

        configure_logging(
            log_file=log_file,
            enable_console=False,
        )
        configure_logging(
            log_file=log_file,
            enable_console=False,
        )

        managed_handlers = [
            handler
            for handler in logging.getLogger("studentos").handlers
            if getattr(handler, "studentos_managed", False)
        ]
        self.assertEqual(len(managed_handlers), 1)

    def test_invalid_log_level_falls_back_to_info(self):
        configure_logging(
            level="NOT_A_LEVEL",
            log_file=(
                Path(self.temporary_directory.name) / "studentos-test.log"
            ),
            enable_console=False,
        )

        self.assertEqual(
            logging.getLogger("studentos").level,
            logging.INFO,
        )

    def test_info_level_hides_debug_messages(self):
        """Your exercise: prove INFO is recorded while DEBUG is filtered out."""

        log_file = (
            Path(self.temporary_directory.name) / "studentos-exercise.log"
        )
        configure_logging(
            level="INFO",
            log_file=log_file,
            enable_console=False,
        )
        exercise_logger = logging.getLogger("studentos.exercise")

        exercise_logger.debug("debug_event")
        exercise_logger.info("info_event")
        self._flush_handlers()
        content = log_file.read_text(encoding="utf-8")


        self.assertIn("info_event", content)
        self.assertNotIn("debug_event", content)


if __name__ == "__main__":
    unittest.main()
