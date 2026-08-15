from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.schemas.common import PriorityLevel


class CalendarCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    start_date: datetime
    end_date: datetime
    priority: PriorityLevel = PriorityLevel.NORMAL

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


class CalendarRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    priority: PriorityLevel
    start_date: datetime
    end_date: datetime
