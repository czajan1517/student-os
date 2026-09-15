import unittest
from datetime import date, datetime, time, timedelta, timezone

from pydantic import ValidationError

from backend.schemas.schedule import TaskScheduleIntent, TaskTimingInput
from backend.services.task_time_service import TaskTimeService


class TaskTimeServiceTests(unittest.TestCase):
    def setUp(self):
        self.local_timezone = timezone(timedelta(hours=8))
        self.now = datetime(
            2026,
            8,
            31,
            22,
            0,
            tzinfo=self.local_timezone,
        )
        self.service = TaskTimeService(now_factory=lambda: self.now)

    def test_clock_time_without_a_date_requires_clarification(self):
        result = self.service.parse(
            "Start at 11 PM and end in 30 minutes"
        )

        self.assertEqual(result.requested_start_time, time(23, 0))
        self.assertEqual(result.duration_minutes, 30)
        self.assertIsNone(result.requested_schedule_date)
        self.assertIsNone(result.schedule)
        self.assertIn(
            "What date should this scheduled task occur?",
            result.clarification_questions,
        )

    def test_structured_timing_resolves_without_parsing_a_sentence(self):
        result = self.service.resolve(
            TaskTimingInput(
                due_date=datetime(2026, 9, 1, 17, 0),
                schedule_date=date(2026, 9, 1),
                start_time=time(14, 0),
                end_time=None,
                duration_minutes=120,
            )
        )

        self.assertEqual(result.duration_minutes, 120)
        self.assertEqual(
            result.schedule.start_at,
            datetime(
                2026,
                9,
                1,
                14,
                0,
                tzinfo=self.local_timezone,
            ),
        )
        self.assertEqual(
            result.schedule.end_at,
            datetime(
                2026,
                9,
                1,
                16,
                0,
                tzinfo=self.local_timezone,
            ),
        )
        self.assertEqual(result.due_date.tzinfo, self.local_timezone)

    def test_structured_timing_uses_the_supplied_browser_reference_time(self):
        browser_timezone = timezone(timedelta(hours=-4))
        browser_now = datetime(
            2026,
            9,
            1,
            18,
            0,
            tzinfo=browser_timezone,
        )

        result = self.service.resolve(
            TaskTimingInput(
                due_date=None,
                schedule_date=date(2026, 9, 1),
                start_time=time(20, 0),
                end_time=None,
                duration_minutes=60,
            ),
            reference_time=browser_now,
        )

        self.assertEqual(result.schedule.start_at.tzinfo, browser_timezone)
        self.assertEqual(
            result.schedule.start_at,
            datetime(2026, 9, 1, 20, 0, tzinfo=browser_timezone),
        )

    def test_structured_duration_correction_recalculates_the_end_time(self):
        result = self.service.resolve(
            TaskTimingInput(
                due_date=None,
                schedule_date=date(2026, 9, 1),
                start_time=time(14, 0),
                end_time=None,
                duration_minutes=120,
            )
        )

        self.assertEqual(
            result.schedule.end_at,
            datetime(
                2026,
                9,
                1,
                16,
                0,
                tzinfo=self.local_timezone,
            ),
        )
        self.assertEqual(result.clarification_questions, [])

    def test_structured_conflicting_end_and_duration_require_clarification(self):
        result = self.service.resolve(
            TaskTimingInput(
                due_date=None,
                schedule_date=date(2026, 9, 1),
                start_time=time(14, 0),
                end_time=time(15, 0),
                duration_minutes=120,
            )
        )

        self.assertIsNone(result.schedule)
        self.assertIn(
            "The requested end time and duration do not match. "
            "Which one should StudentOS use?",
            result.clarification_questions,
        )

    def test_today_start_and_duration_resolve_a_fixed_schedule(self):
        result = self.service.parse(
            "Study today at 11 PM for 30 minutes"
        )

        self.assertEqual(
            result.schedule.start_at,
            datetime(
                2026,
                8,
                31,
                23,
                0,
                tzinfo=self.local_timezone,
            ),
        )
        self.assertEqual(
            result.schedule.end_at,
            datetime(
                2026,
                8,
                31,
                23,
                30,
                tzinfo=self.local_timezone,
            ),
        )
        self.assertTrue(result.schedule.locked)
        self.assertEqual(result.clarification_questions, [])
        self.assertIsNone(result.due_date)

    def test_deadline_wording_sets_due_date_not_schedule(self):
        result = self.service.parse(
            "Finish the assignment by 11:30 PM today"
        )

        self.assertEqual(
            result.due_date,
            datetime(
                2026,
                8,
                31,
                23,
                30,
                tzinfo=self.local_timezone,
            ),
        )
        self.assertIsNone(result.schedule)
        self.assertIsNone(result.requested_start_time)
        self.assertEqual(result.clarification_questions, [])

    def test_deadline_clock_without_a_date_requires_clarification(self):
        result = self.service.parse(
            "Submit the report by 9 AM"
        )

        self.assertIsNone(result.due_date)
        self.assertIn(
            "What date should this task be due?",
            result.clarification_questions,
        )

    def test_deadline_and_requested_schedule_are_parsed_together(self):
        result = self.service.parse(
            "Create a math task due today at 11 PM, "
            "start it at 10 PM, and make it 30 minutes."
        )

        self.assertEqual(
            result.due_date,
            datetime(
                2026,
                8,
                31,
                23,
                0,
                tzinfo=self.local_timezone,
            ),
        )
        self.assertEqual(result.requested_start_time, time(22, 0))
        self.assertEqual(result.duration_minutes, 30)
        self.assertEqual(
            result.schedule.start_at,
            datetime(
                2026,
                8,
                31,
                22,
                0,
                tzinfo=self.local_timezone,
            ),
        )
        self.assertEqual(
            result.schedule.end_at,
            datetime(
                2026,
                8,
                31,
                22,
                30,
                tzinfo=self.local_timezone,
            ),
        )
        self.assertEqual(result.clarification_questions, [])

    def test_schedule_ending_after_deadline_requires_clarification(self):
        result = self.service.parse(
            "Create a math task due today at 11 PM, "
            "start it at 10 PM, and make it 2 hours."
        )

        self.assertEqual(
            result.due_date,
            datetime(
                2026,
                8,
                31,
                23,
                0,
                tzinfo=self.local_timezone,
            ),
        )
        self.assertEqual(result.requested_start_time, time(22, 0))
        self.assertEqual(result.duration_minutes, 120)
        self.assertIsNone(result.schedule)
        self.assertIn(
            "The requested schedule ends after the task deadline. "
            "What should StudentOS change?",
            result.clarification_questions,
        )

    def test_invalid_clock_time_requires_clarification_instead_of_crashing(self):
        result = self.service.parse(
            "Submit the report by 13 PM today"
        )

        self.assertIsNone(result.due_date)
        self.assertIn(
            "What time should this task be due?",
            result.clarification_questions,
        )

    def test_tomorrow_is_resolved_from_the_injected_current_time(self):
        result = self.service.parse(
            "Study tomorrow at 9 AM for 45 minutes"
        )

        self.assertEqual(
            result.schedule.start_at,
            datetime(
                2026,
                9,
                1,
                9,
                0,
                tzinfo=self.local_timezone,
            ),
        )

    def test_named_date_and_clock_resolve_a_deadline(self):
        result = self.service.parse(
            "Finish the report by September 2, 2026 at 9 AM"
        )

        self.assertEqual(
            result.due_date,
            datetime(
                2026,
                9,
                2,
                9,
                0,
                tzinfo=self.local_timezone,
            ),
        )

    def test_duration_can_cross_midnight(self):
        result = self.service.parse(
            "Start today at 11:30 PM for 90 minutes"
        )

        self.assertEqual(
            result.schedule.end_at,
            datetime(
                2026,
                9,
                1,
                1,
                0,
                tzinfo=self.local_timezone,
            ),
        )

    def test_spelled_out_hours_are_converted_to_minutes(self):
        result = self.service.parse(
            "Start today at 11 PM for two hours"
        )

        self.assertEqual(result.duration_minutes, 120)
        self.assertEqual(
            result.schedule.end_at,
            datetime(
                2026,
                9,
                1,
                1,
                0,
                tzinfo=self.local_timezone,
            ),
        )

    def test_compound_spelled_out_duration_is_summed(self):
        result = self.service.parse(
            "Start today at 11 PM for one hour and thirty minutes"
        )

        self.assertEqual(result.duration_minutes, 90)
        self.assertEqual(
            result.schedule.end_at,
            datetime(
                2026,
                9,
                1,
                0,
                30,
                tzinfo=self.local_timezone,
            ),
        )

    def test_numeric_and_spelled_out_durations_are_equivalent(self):
        numeric = self.service.parse(
            "Start today at 11 PM for 45 minutes"
        )
        spelled_out = self.service.parse(
            "Start today at 11 PM for forty-five minutes"
        )

        self.assertEqual(
            spelled_out.duration_minutes,
            numeric.duration_minutes,
        )
        self.assertEqual(
            spelled_out.schedule.end_at,
            numeric.schedule.end_at,
        )

    def test_explicit_end_before_start_rolls_into_the_next_day(self):
        result = self.service.parse(
            "Start today at 11:30 PM and end at 1 AM"
        )

        self.assertEqual(
            result.schedule.end_at,
            datetime(
                2026,
                9,
                1,
                1,
                0,
                tzinfo=self.local_timezone,
            ),
        )
        self.assertIsNone(result.duration_minutes)

    def test_conflicting_duration_and_end_time_require_clarification(self):
        result = self.service.parse(
            "Start today at 11 PM, end at 11:30 PM, for 60 minutes"
        )

        self.assertIsNone(result.schedule)
        self.assertIn(
            "The requested end time and duration do not match. "
            "Which one should StudentOS use?",
            result.clarification_questions,
        )

    def test_iso_date_is_parsed_deterministically(self):
        result = self.service.parse(
            "Start on 2026-09-02 at noon for 45 minutes"
        )

        self.assertEqual(
            result.schedule.start_at,
            datetime(
                2026,
                9,
                2,
                12,
                0,
                tzinfo=self.local_timezone,
            ),
        )
        self.assertEqual(result.duration_minutes, 45)

    def test_schedule_schema_rejects_end_before_start(self):
        with self.assertRaisesRegex(
            ValidationError,
            "end must be later than start",
        ):
            TaskScheduleIntent(
                start_at=datetime(2026, 8, 31, 12, 0),
                end_at=datetime(2026, 8, 31, 11, 0),
            )

    def test_schedule_schema_rejects_mixed_timezone_styles(self):
        with self.assertRaisesRegex(
            ValidationError,
            "same timezone style",
        ):
            TaskScheduleIntent(
                start_at=datetime(
                    2026,
                    8,
                    31,
                    11,
                    0,
                    tzinfo=self.local_timezone,
                ),
                end_at=datetime(2026, 8, 31, 11, 30),
            )


if __name__ == "__main__":
    unittest.main()
