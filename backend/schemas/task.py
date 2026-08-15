from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from backend.schemas.common import PriorityLevel


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    priority: PriorityLevel = PriorityLevel.NORMAL
    estimated_time: int = Field(default=60, gt=0, le=1440)
    due_date: datetime | None = None
    completed: bool = False


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    priority: PriorityLevel | None = None
    estimated_time: int | None = Field(default=None, gt=0, le=1440)
    due_date: datetime | None = None
    completed: bool | None = None


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    priority: PriorityLevel
    estimated_time: int
    due_date: datetime | None
    completed: bool
    created_at: datetime
    updated_at: datetime

