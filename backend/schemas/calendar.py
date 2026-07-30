from pydantic import BaseModel, model_validator
from datetime import datetime


class CalendarCreate(BaseModel):

    title: str
    description: str | None = None
    start_date: datetime 
    end_date: datetime 
    priority: int | None = None

    @model_validator(mode="after")
    def check_dates(self):
        if self.end_date <= self.start_date:
            raise ValueError("End date must be later than the start date")
        return self

class CalendarUpdate(BaseModel):

    title: str | None = None
    description: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    priority: int | None = None
