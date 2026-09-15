from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.schemas.calendar import CalendarRead
from backend.schemas.task import TaskRead


class TaskScheduleIntent(BaseModel):
    """A fully resolved user-requested calendar placement."""

    model_config = ConfigDict(extra="forbid")

    start_at: datetime
    end_at: datetime
    locked: bool = True

    @model_validator(mode="after")
    def validate_schedule_intent(self):
        if (self.start_at.tzinfo is None) != (self.end_at.tzinfo is None):
            raise ValueError(
                "Schedule intent datetimes must use the same timezone style"
            )
        if self.end_at <= self.start_at:
            raise ValueError("Schedule intent end must be later than start")
        return self


class TaskTimingInput(BaseModel):
    """Structured timing intent produced before deterministic resolution."""

    model_config = ConfigDict(extra="forbid")

    due_date: datetime | None
    schedule_date: date | None
    start_time: time | None
    end_time: time | None
    duration_minutes: int | None = Field(gt=0, le=1440)


class TaskTimingParseResult(BaseModel):
    """Deterministically validated and resolved task timing facts."""

    model_config = ConfigDict(extra="forbid")

    due_date: datetime | None = None
    requested_schedule_date: date | None = None
    requested_start_time: time | None = None
    requested_end_time: time | None = None
    duration_minutes: int | None = Field(default=None, gt=0, le=1440)
    schedule: TaskScheduleIntent | None = None
    clarification_questions: list[str] = Field(default_factory=list)


class TaskCreationScheduleBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start_date: datetime
    end_date: datetime
    duration_minutes: int = Field(gt=0, le=1440)
    buffer_after_minutes: int = Field(default=0, ge=0, le=240)
    locked: bool

    @model_validator(mode="after")
    def validate_block(self):
        if (self.start_date.tzinfo is None) != (self.end_date.tzinfo is None):
            raise ValueError(
                "Schedule block datetimes must use the same timezone style"
            )
        if self.end_date <= self.start_date:
            raise ValueError("Schedule block end must be later than start")
        return self


class TaskCreationSchedulePreview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mode: Literal["fixed", "automatic"]
    deadline: datetime | None
    estimated_minutes: int = Field(gt=0, le=1440)
    available_minutes: int = Field(ge=0)
    proposed_blocks: list[TaskCreationScheduleBlock]
    unscheduled_minutes: int = Field(ge=0)
    feasible: bool
    warnings: list[str] = Field(default_factory=list)


class TaskCreationApplyResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task: TaskRead
    created_events: list[CalendarRead]
    schedule: TaskCreationSchedulePreview


class ScheduleRequest(BaseModel):
    task_id: int = Field(gt=0)
    window_start: datetime
    window_end: datetime
    day_start: time = time(8, 0)
    day_end: time = time(20, 0)
    minimum_block_minutes: int = Field(default=30, ge=5, le=240)
    maximum_block_minutes: int = Field(default=120, ge=5, le=480)
    recovery_buffer_minutes: int = Field(default=15, ge=0, le=120)
    allow_after_due: bool = False

    @model_validator(mode="after")
    def validate_schedule_window(self):
        if self.window_end <= self.window_start:
            raise ValueError("Window end must be later than window start")
        if self.day_end <= self.day_start:
            raise ValueError("Day end must be later than day start")
        if self.maximum_block_minutes < self.minimum_block_minutes:
            raise ValueError(
                "Maximum block length must be at least the minimum block length"
            )
        if (self.window_start.tzinfo is None) != (self.window_end.tzinfo is None):
            raise ValueError("Schedule window datetimes must use the same timezone style")
        return self


class ProposedScheduleBlock(BaseModel):
    start_date: datetime
    end_date: datetime
    duration_minutes: int
    buffer_after_minutes: int


class SchedulePreview(BaseModel):
    task_id: int
    task_title: str
    deadline: datetime | None
    scheduling_cutoff: datetime
    estimated_minutes: int
    already_scheduled_minutes: int
    minutes_to_schedule: int
    available_minutes: int
    proposed_blocks: list[ProposedScheduleBlock]
    unscheduled_minutes: int
    feasible: bool
    warnings: list[str] = Field(default_factory=list)


class ScheduleApplyResult(SchedulePreview):
    created_events: list[CalendarRead]
