import logging
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Callable

from sqlalchemy.orm import Session

from backend.database.database import SessionLocal
from backend.database.models import CalendarEvent, Task
from backend.schemas.schedule import (
    ProposedScheduleBlock,
    ScheduleApplyResult,
    SchedulePreview,
    ScheduleRequest,
    TaskCreationApplyResult,
    TaskCreationScheduleBlock,
    TaskCreationSchedulePreview,
    TaskTimingParseResult,
)
from backend.schemas.task import TaskCreate


logger = logging.getLogger("studentos.schedule")


class ScheduleTaskNotFoundError(Exception):
    pass


class ScheduleValidationError(Exception):
    pass


class ScheduleConflictError(Exception):
    def __init__(self, preview: SchedulePreview):
        super().__init__("The task cannot be fully scheduled in the requested window")
        self.preview = preview


class TaskCreationScheduleConflictError(Exception):
    def __init__(self, preview: TaskCreationSchedulePreview):
        super().__init__("The proposed task cannot be safely scheduled")
        self.preview = preview


@dataclass(frozen=True)
class TimeInterval:
    start: datetime
    end: datetime

    @property
    def minutes(self) -> int:
        return max(0, int((self.end - self.start).total_seconds() // 60))


class ScheduleService:
    def __init__(
        self,
        *,
        session_factory: Callable[[], Session] = SessionLocal,
    ):
        self._session_factory = session_factory

    def preview_task(self, request: ScheduleRequest) -> SchedulePreview:
        db = self._session_factory()
        try:
            preview = self._build_preview(db, request)
            logger.info(
                "schedule_preview_generated task_id=%s feasible=%s "
                "block_count=%s unscheduled_minutes=%s warning_count=%s",
                request.task_id,
                preview.feasible,
                len(preview.proposed_blocks),
                preview.unscheduled_minutes,
                len(preview.warnings),
            )
            return preview
        except (ScheduleTaskNotFoundError, ScheduleValidationError) as error:
            logger.warning(
                "schedule_preview_rejected task_id=%s reason=%s",
                request.task_id,
                type(error).__name__,
            )
            raise
        except Exception:
            logger.exception(
                "schedule_preview_failed task_id=%s",
                request.task_id,
            )
            raise
        finally:
            db.close()

    def apply_task(self, request: ScheduleRequest) -> ScheduleApplyResult:
        db = self._session_factory()
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

            result = ScheduleApplyResult(
                **preview.model_dump(),
                created_events=created_events,
            )
            logger.info(
                "schedule_applied task_id=%s created_event_count=%s",
                request.task_id,
                len(created_events),
            )
            return result
        except ScheduleConflictError as error:
            db.rollback()
            logger.warning(
                "schedule_apply_rejected task_id=%s reason=conflict "
                "unscheduled_minutes=%s",
                request.task_id,
                error.preview.unscheduled_minutes,
            )
            raise
        except (ScheduleTaskNotFoundError, ScheduleValidationError) as error:
            db.rollback()
            logger.warning(
                "schedule_apply_rejected task_id=%s reason=%s",
                request.task_id,
                type(error).__name__,
            )
            raise
        except Exception:
            db.rollback()
            logger.exception(
                "schedule_apply_failed task_id=%s",
                request.task_id,
            )
            raise
        finally:
            db.close()

    def preview_task_creation(
        self,
        task: TaskCreate,
        timing: TaskTimingParseResult,
        now: datetime,
    ) -> TaskCreationSchedulePreview:
        db = self._session_factory()
        try:
            preview = self._build_task_creation_preview(
                db,
                task,
                timing,
                now,
            )
            logger.info(
                "task_creation_schedule_preview_generated mode=%s "
                "feasible=%s block_count=%s unscheduled_minutes=%s",
                preview.mode,
                preview.feasible,
                len(preview.proposed_blocks),
                preview.unscheduled_minutes,
            )
            return preview
        except Exception:
            logger.exception("task_creation_schedule_preview_failed")
            raise
        finally:
            db.close()

    def apply_task_creation(
        self,
        task: TaskCreate,
        timing: TaskTimingParseResult,
        now: datetime,
    ) -> TaskCreationApplyResult:
        db = self._session_factory()
        try:
            preview = self._build_task_creation_preview(
                db,
                task,
                timing,
                now,
            )
            if not preview.feasible:
                raise TaskCreationScheduleConflictError(preview)

            new_task = self._new_task(task)
            db.add(new_task)
            db.flush()

            created_events = [
                CalendarEvent(
                    title=new_task.title,
                    description=new_task.description,
                    priority=new_task.priority,
                    task_id=new_task.id,
                    locked=block.locked,
                    buffer_after_minutes=block.buffer_after_minutes,
                    start_date=block.start_date,
                    end_date=block.end_date,
                )
                for block in preview.proposed_blocks
            ]
            db.add_all(created_events)
            db.flush()
            db.refresh(new_task)
            for event in created_events:
                db.refresh(event)

            result = TaskCreationApplyResult(
                task=new_task,
                created_events=created_events,
                schedule=preview,
            )
            db.commit()
            logger.info(
                "task_creation_schedule_applied task_id=%s mode=%s "
                "created_event_count=%s",
                new_task.id,
                preview.mode,
                len(created_events),
            )
            return result
        except TaskCreationScheduleConflictError as error:
            db.rollback()
            logger.warning(
                "task_creation_schedule_apply_rejected reason=conflict "
                "mode=%s unscheduled_minutes=%s",
                error.preview.mode,
                error.preview.unscheduled_minutes,
            )
            raise
        except Exception:
            db.rollback()
            logger.exception("task_creation_schedule_apply_failed")
            raise
        finally:
            db.close()

    def _build_task_creation_preview(
        self,
        db: Session,
        task: TaskCreate,
        timing: TaskTimingParseResult,
        now: datetime,
    ) -> TaskCreationSchedulePreview:
        if timing.schedule is not None:
            return self._build_fixed_task_creation_preview(
                db,
                task,
                timing,
            )
        return self._build_automatic_task_creation_preview(
            db,
            task,
            now,
        )

    def _build_fixed_task_creation_preview(
        self,
        db: Session,
        task: TaskCreate,
        timing: TaskTimingParseResult,
    ) -> TaskCreationSchedulePreview:
        schedule = timing.schedule
        if schedule is None:
            raise ScheduleValidationError("A fixed schedule was not supplied")

        duration_minutes = TimeInterval(
            schedule.start_at,
            schedule.end_at,
        ).minutes
        has_conflict = self._fixed_schedule_has_conflict(
            db,
            schedule.start_at,
            schedule.end_at,
            task.recovery_buffer_minutes,
        )
        misses_deadline = (
            task.due_date is not None
            and schedule.end_at > task.due_date
        )
        warnings: list[str] = []
        if has_conflict:
            warnings.append(
                "The requested time overlaps existing calendar time"
            )
        if misses_deadline:
            warnings.append(
                "The requested schedule ends after the task deadline"
            )
        duration_mismatch = duration_minutes != task.estimated_time
        if duration_mismatch:
            warnings.append(
                "The requested schedule duration does not match the task duration"
            )

        feasible = (
            not has_conflict
            and not misses_deadline
            and not duration_mismatch
        )
        return TaskCreationSchedulePreview(
            mode="fixed",
            deadline=task.due_date,
            estimated_minutes=task.estimated_time,
            available_minutes=(duration_minutes if feasible else 0),
            proposed_blocks=[
                TaskCreationScheduleBlock(
                    start_date=schedule.start_at,
                    end_date=schedule.end_at,
                    duration_minutes=duration_minutes,
                    buffer_after_minutes=task.recovery_buffer_minutes,
                    locked=True,
                )
            ],
            unscheduled_minutes=(0 if feasible else task.estimated_time),
            feasible=feasible,
            warnings=warnings,
        )

    def _build_automatic_task_creation_preview(
        self,
        db: Session,
        task: TaskCreate,
        now: datetime,
    ) -> TaskCreationSchedulePreview:
        if task.due_date is None:
            raise ScheduleValidationError(
                "Automatic scheduling requires a task deadline"
            )

        window_start = now.replace(second=0, microsecond=0)
        self._require_matching_timezone_style(window_start, task.due_date)
        warnings: list[str] = [
            "The scheduling window was limited by the task deadline"
        ]

        if task.due_date <= window_start:
            free_intervals: list[TimeInterval] = []
        else:
            free_intervals = self._get_free_intervals_for_window(
                db,
                window_start=window_start,
                day_start=time(8, 0),
                day_end=time(20, 0),
                cutoff=task.due_date,
            )

        available_minutes = sum(
            interval.minutes for interval in free_intervals
        )
        minimum_block_minutes = 30 if task.splittable else task.estimated_time
        maximum_block_minutes = 120 if task.splittable else task.estimated_time
        blocks, unscheduled_minutes = self._allocate_blocks(
            free_intervals,
            task.estimated_time,
            minimum_block_minutes,
            maximum_block_minutes,
            task.recovery_buffer_minutes,
        )

        if unscheduled_minutes and task.recovery_buffer_minutes:
            no_buffer_blocks, no_buffer_remaining = self._allocate_blocks(
                free_intervals,
                task.estimated_time,
                minimum_block_minutes,
                maximum_block_minutes,
                0,
            )
            if no_buffer_remaining < unscheduled_minutes:
                blocks = no_buffer_blocks
                unscheduled_minutes = no_buffer_remaining
                warnings.append(
                    "Recovery buffers were reduced to protect the deadline"
                )

        if unscheduled_minutes:
            warnings.append(
                f"{unscheduled_minutes} minutes could not be scheduled "
                "before the deadline"
            )

        return TaskCreationSchedulePreview(
            mode="automatic",
            deadline=task.due_date,
            estimated_minutes=task.estimated_time,
            available_minutes=available_minutes,
            proposed_blocks=[
                TaskCreationScheduleBlock(
                    start_date=block.start_date,
                    end_date=block.end_date,
                    duration_minutes=block.duration_minutes,
                    buffer_after_minutes=block.buffer_after_minutes,
                    locked=False,
                )
                for block in blocks
            ],
            unscheduled_minutes=unscheduled_minutes,
            feasible=unscheduled_minutes == 0,
            warnings=warnings,
        )

    @staticmethod
    def _new_task(task: TaskCreate) -> Task:
        return Task(
            title=task.title,
            description=task.description,
            priority=int(task.priority),
            estimated_time=task.estimated_time,
            task_type=task.task_type.value,
            effort_level=int(task.effort_level),
            recovery_buffer_minutes=task.recovery_buffer_minutes,
            splittable=task.splittable,
            due_date=task.due_date,
            completed=task.completed,
        )

    def _fixed_schedule_has_conflict(
        self,
        db: Session,
        start_at: datetime,
        end_at: datetime,
        buffer_after_minutes: int,
    ) -> bool:
        requested_end = end_at + timedelta(minutes=buffer_after_minutes)
        for event in db.query(CalendarEvent).all():
            event_start = self._match_timezone_style(
                event.start_date,
                start_at,
            )
            event_end = self._match_timezone_style(
                event.end_date,
                start_at,
            ) + timedelta(minutes=event.buffer_after_minutes)
            if event_start < requested_end and event_end > start_at:
                return True
        return False

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
        return self._get_free_intervals_for_window(
            db,
            window_start=request.window_start,
            day_start=request.day_start,
            day_end=request.day_end,
            cutoff=cutoff,
        )

    def _get_free_intervals_for_window(
        self,
        db: Session,
        *,
        window_start: datetime,
        day_start: time,
        day_end: time,
        cutoff: datetime,
    ) -> list[TimeInterval]:
        busy_intervals: list[TimeInterval] = []
        for event in db.query(CalendarEvent).all():
            event_start = self._match_timezone_style(
                event.start_date,
                window_start,
            )
            event_end = self._match_timezone_style(
                event.end_date,
                window_start,
            ) + timedelta(minutes=event.buffer_after_minutes)
            if event_start < cutoff and event_end > window_start:
                busy_intervals.append(
                    TimeInterval(
                        max(event_start, window_start),
                        min(event_end, cutoff),
                    )
                )

        merged_busy_intervals = self._merge_intervals(busy_intervals)
        free_intervals: list[TimeInterval] = []
        for working_interval in self._working_intervals_for_window(
            window_start=window_start,
            day_start=day_start,
            day_end=day_end,
            cutoff=cutoff,
        ):
            free_intervals.extend(
                self._subtract_busy_intervals(
                    working_interval,
                    merged_busy_intervals,
                )
            )
        return free_intervals

    @classmethod
    def _match_timezone_style(
        cls,
        value: datetime,
        reference: datetime,
    ) -> datetime:
        value_is_aware = value.utcoffset() is not None
        reference_is_aware = reference.utcoffset() is not None
        if reference_is_aware and not value_is_aware:
            return value.replace(tzinfo=reference.tzinfo)
        if value_is_aware and not reference_is_aware:
            return value.replace(tzinfo=None)
        if value_is_aware and reference_is_aware:
            return value.astimezone(reference.tzinfo)
        return value

    @staticmethod
    def _working_intervals_for_window(
        *,
        window_start: datetime,
        day_start: time,
        day_end: time,
        cutoff: datetime,
    ) -> list[TimeInterval]:
        intervals: list[TimeInterval] = []
        current_date: date = window_start.date()
        final_date = cutoff.date()
        timezone = window_start.tzinfo

        while current_date <= final_date:
            interval_day_start = datetime.combine(
                current_date,
                day_start,
                tzinfo=timezone,
            )
            interval_day_end = datetime.combine(
                current_date,
                day_end,
                tzinfo=timezone,
            )
            interval_start = max(interval_day_start, window_start)
            interval_end = min(interval_day_end, cutoff)
            if interval_end > interval_start:
                intervals.append(TimeInterval(interval_start, interval_end))
            current_date += timedelta(days=1)

        return intervals

    @staticmethod
    def _working_intervals(
        request: ScheduleRequest,
        cutoff: datetime,
    ) -> list[TimeInterval]:
        return ScheduleService._working_intervals_for_window(
            window_start=request.window_start,
            day_start=request.day_start,
            day_end=request.day_end,
            cutoff=cutoff,
        )

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
