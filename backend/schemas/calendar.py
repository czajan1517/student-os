from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.schemas.common import PriorityLevel


class CalendarCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    start_date: datetime
    end_date: datetime
    priority: PriorityLevel = PriorityLevel.NORMAL
    task_id: int | None = Field(default=None, gt=0)
    locked: bool = True
    buffer_after_minutes: int = Field(default=0, ge=0, le=240)

    @model_validator(mode="after")
    def check_dates(self):
        if self.end_date <= self.start_date:
            raise ValueError("End date must be later than the start date")
        return self

class CalendarUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    start_date: datetime | None = None
    end_date: datetime | None = None
    priority: PriorityLevel | None = None
    task_id: int | None = Field(default=None, gt=0)
    locked: bool | None = None
    buffer_after_minutes: int | None = Field(default=None, ge=0, le=240)


class CalendarRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    priority: PriorityLevel
    task_id: int | None
    locked: bool
    buffer_after_minutes: int
    start_date: datetime
    end_date: datetime
