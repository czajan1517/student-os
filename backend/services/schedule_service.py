from dataclasses import dataclass
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from backend.database.database import SessionLocal
from backend.database.models import CalendarEvent, Task
from backend.schemas.schedule import (
    ProposedScheduleBlock,
    ScheduleApplyResult,
    SchedulePreview,
    ScheduleRequest,
)


class ScheduleTaskNotFoundError(Exception):
    pass


class ScheduleValidationError(Exception):
    pass


class ScheduleConflictError(Exception):
    def __init__(self, preview: SchedulePreview):
        super().__init__("The task cannot be fully scheduled in the requested window")
        self.preview = preview


@dataclass(frozen=True)
class TimeInterval:
    start: datetime
    end: datetime

    @property
    def minutes(self) -> int:
        return max(0, int((self.end - self.start).total_seconds() // 60))


class ScheduleService:
    def preview_task(self, request: ScheduleRequest) -> SchedulePreview:
        db = SessionLocal()
        try:
            return self._build_preview(db, request)
        finally:
            db.close()

    def apply_task(self, request: ScheduleRequest) -> ScheduleApplyResult:
        db = SessionLocal()
        try:
            preview = self._build_preview(db, request)
            if not preview.feasible:
                raise ScheduleConflictError(preview)

            task = db.get(Task, request.task_id)
            if task is None:
                raise ScheduleTaskNotFoundError

            created_events = [
                CalendarEvent(
                    title=task.title,
                    description=task.description,
                    priority=task.priority,
                    task_id=task.id,
                    locked=False,
                    buffer_after_minutes=block.buffer_after_minutes,
                    start_date=block.start_date,
                    end_date=block.end_date,
                )
                for block in preview.proposed_blocks
            ]
            db.add_all(created_events)
            db.commit()
            for event in created_events:
                db.refresh(event)

            return ScheduleApplyResult(
                **preview.model_dump(),
                created_events=created_events,
            )
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def _build_preview(
        self,
        db: Session,
        request: ScheduleRequest,
    ) -> SchedulePreview:
        task = db.get(Task, request.task_id)
        if task is None:
            raise ScheduleTaskNotFoundError
        if task.completed:
            raise ScheduleValidationError("Completed tasks cannot be scheduled")

        cutoff = self._get_cutoff(task, request)
        scheduled_minutes = self._get_scheduled_minutes(
            db,
            task.id,
            request.window_start,
            (
                task.due_date
                if task.due_date is not None and not request.allow_after_due
                else None
            ),
        )
        minutes_to_schedule = max(0, task.estimated_time - scheduled_minutes)
        warnings: list[str] = []

        if minutes_to_schedule == 0:
            warnings.append("The task already has enough future time allocated")

        if cutoff <= request.window_start:
            proposed_blocks: list[ProposedScheduleBlock] = []
            unscheduled_minutes = minutes_to_schedule
            available_minutes = 0
        else:
            free_intervals = self._get_free_intervals(db, request, cutoff)
            available_minutes = sum(interval.minutes for interval in free_intervals)
            proposed_blocks, unscheduled_minutes = self._allocate_blocks(
                free_intervals,
                minutes_to_schedule,
                request.minimum_block_minutes,
                request.maximum_block_minutes,
                request.recovery_buffer_minutes,
            )

            if unscheduled_minutes and request.recovery_buffer_minutes:
                no_buffer_blocks, no_buffer_remaining = self._allocate_blocks(
                    free_intervals,
                    minutes_to_schedule,
                    request.minimum_block_minutes,
                    request.maximum_block_minutes,
                    0,
                )
                if no_buffer_remaining < unscheduled_minutes:
                    proposed_blocks = no_buffer_blocks
                    unscheduled_minutes = no_buffer_remaining
                    warnings.append(
                        "Recovery buffers were reduced to protect the deadline"
                    )

        if task.due_date is not None and cutoff == task.due_date:
            warnings.append("The scheduling window was limited by the task deadline")
        if unscheduled_minutes:
            warnings.append(
                f"{unscheduled_minutes} minutes could not be scheduled in this window"
            )

        return SchedulePreview(
            task_id=task.id,
            task_title=task.title,
            deadline=task.due_date,
            scheduling_cutoff=cutoff,
            estimated_minutes=task.estimated_time,
            already_scheduled_minutes=scheduled_minutes,
            minutes_to_schedule=minutes_to_schedule,
            available_minutes=available_minutes,
            proposed_blocks=proposed_blocks,
            unscheduled_minutes=unscheduled_minutes,
            feasible=unscheduled_minutes == 0,
            warnings=warnings,
        )

    def _get_cutoff(self, task: Task, request: ScheduleRequest) -> datetime:
        if task.due_date is None or request.allow_after_due:
            return request.window_end

        self._require_matching_timezone_style(
            request.window_start,
            task.due_date,
        )
        return min(request.window_end, task.due_date)

    @staticmethod
    def _require_matching_timezone_style(first: datetime, second: datetime) -> None:
        first_is_aware = first.utcoffset() is not None
        second_is_aware = second.utcoffset() is not None
        if first_is_aware != second_is_aware:
            raise ScheduleValidationError(
                "Task deadline and schedule window must use the same timezone style"
            )

    @staticmethod
    def _get_scheduled_minutes(
        db: Session,
        task_id: int,
        window_start: datetime,
        allocation_cutoff: datetime | None,
    ) -> int:
        query = db.query(CalendarEvent).filter(
            CalendarEvent.task_id == task_id,
            CalendarEvent.end_date > window_start,
        )
        if allocation_cutoff is not None:
            query = query.filter(CalendarEvent.start_date < allocation_cutoff)

        events = query.all()
        return sum(
            TimeInterval(
                max(event.start_date, window_start),
                (
                    min(event.end_date, allocation_cutoff)
                    if allocation_cutoff is not None
                    else event.end_date
                ),
            ).minutes
            for event in events
        )

    def _get_free_intervals(
        self,
        db: Session,
        request: ScheduleRequest,
        cutoff: datetime,
    ) -> list[TimeInterval]:
        busy_events = (
            db.query(CalendarEvent)
            .filter(
                CalendarEvent.start_date < cutoff,
                CalendarEvent.end_date
                > request.window_start - timedelta(minutes=240),
            )
            .all()
        )
        busy_intervals = self._merge_intervals(
            [
                TimeInterval(
                    max(event.start_date, request.window_start),
                    min(
                        event.end_date
                        + timedelta(minutes=event.buffer_after_minutes),
                        cutoff,
                    ),
                )
                for event in busy_events
            ]
        )

        free_intervals: list[TimeInterval] = []
        for working_interval in self._working_intervals(request, cutoff):
            free_intervals.extend(
                self._subtract_busy_intervals(working_interval, busy_intervals)
            )
        return free_intervals

    @staticmethod
    def _working_intervals(
        request: ScheduleRequest,
        cutoff: datetime,
    ) -> list[TimeInterval]:
        intervals: list[TimeInterval] = []
        current_date: date = request.window_start.date()
        final_date = cutoff.date()
        timezone = request.window_start.tzinfo

        while current_date <= final_date:
            day_start = datetime.combine(
                current_date,
                request.day_start,
                tzinfo=timezone,
            )
            day_end = datetime.combine(
                current_date,
                request.day_end,
                tzinfo=timezone,
            )
            interval_start = max(day_start, request.window_start)
            interval_end = min(day_end, cutoff)
            if interval_end > interval_start:
                intervals.append(TimeInterval(interval_start, interval_end))
            current_date += timedelta(days=1)

        return intervals

    @staticmethod
    def _merge_intervals(intervals: list[TimeInterval]) -> list[TimeInterval]:
        valid_intervals = sorted(
            (interval for interval in intervals if interval.end > interval.start),
            key=lambda interval: interval.start,
        )
        if not valid_intervals:
            return []

        merged = [valid_intervals[0]]
        for interval in valid_intervals[1:]:
            previous = merged[-1]
            if interval.start <= previous.end:
                merged[-1] = TimeInterval(
                    previous.start,
                    max(previous.end, interval.end),
                )
            else:
                merged.append(interval)
        return merged

    @staticmethod
    def _subtract_busy_intervals(
        working_interval: TimeInterval,
        busy_intervals: list[TimeInterval],
    ) -> list[TimeInterval]:
        free_intervals: list[TimeInterval] = []
        cursor = working_interval.start

        for busy in busy_intervals:
            if busy.end <= cursor or busy.start >= working_interval.end:
                continue
            if busy.start > cursor:
                free_intervals.append(
                    TimeInterval(cursor, min(busy.start, working_interval.end))
                )
            cursor = max(cursor, busy.end)
            if cursor >= working_interval.end:
                break

        if cursor < working_interval.end:
            free_intervals.append(TimeInterval(cursor, working_interval.end))
        return free_intervals

    @staticmethod
    def _allocate_blocks(
        free_intervals: list[TimeInterval],
        required_minutes: int,
        minimum_block_minutes: int,
        maximum_block_minutes: int,
        recovery_buffer_minutes: int,
    ) -> tuple[list[ProposedScheduleBlock], int]:
        blocks: list[ProposedScheduleBlock] = []
        remaining_minutes = required_minutes

        for free_interval in free_intervals:
            cursor = free_interval.start
            while remaining_minutes > 0:
                available_minutes = TimeInterval(cursor, free_interval.end).minutes
                work_capacity = available_minutes - recovery_buffer_minutes
                if work_capacity <= 0:
                    break

                duration = min(
                    maximum_block_minutes,
                    remaining_minutes,
                    work_capacity,
                )
                if (
                    duration < minimum_block_minutes
                    and duration < remaining_minutes
                ):
                    break

                block_end = cursor + timedelta(minutes=duration)
                blocks.append(
                    ProposedScheduleBlock(
                        start_date=cursor,
                        end_date=block_end,
                        duration_minutes=duration,
                        buffer_after_minutes=recovery_buffer_minutes,
                    )
                )
                remaining_minutes -= duration
                cursor = block_end + timedelta(minutes=recovery_buffer_minutes)

        return blocks, remaining_minutes
