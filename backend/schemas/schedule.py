from datetime import datetime, time

from pydantic import BaseModel, Field, model_validator

from backend.schemas.calendar import CalendarRead


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
