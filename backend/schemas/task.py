from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from backend.schemas.common import EffortLevel, PriorityLevel, TaskType


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    priority: PriorityLevel = PriorityLevel.NORMAL
    estimated_time: int = Field(default=60, gt=0, le=1440)
    task_type: TaskType = TaskType.GENERAL
    effort_level: EffortLevel = EffortLevel.MODERATE
    recovery_buffer_minutes: int = Field(default=15, ge=0, le=120)
    splittable: bool = True
    due_date: datetime | None = None
    completed: bool = False


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    priority: PriorityLevel | None = None
    estimated_time: int | None = Field(default=None, gt=0, le=1440)
    task_type: TaskType | None = None
    effort_level: EffortLevel | None = None
    recovery_buffer_minutes: int | None = Field(default=None, ge=0, le=120)
    splittable: bool | None = None
    due_date: datetime | None = None
    completed: bool | None = None


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    priority: PriorityLevel
    estimated_time: int
    task_type: TaskType
    effort_level: EffortLevel
    recovery_buffer_minutes: int
    splittable: bool
    due_date: datetime | None
    completed: bool
    created_at: datetime
    updated_at: datetime

