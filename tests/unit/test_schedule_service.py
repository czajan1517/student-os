import unittest
from datetime import datetime

from backend.services.schedule_service import ScheduleService, TimeInterval


class ScheduleServiceTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
