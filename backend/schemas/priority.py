from pydantic import BaseModel, Field

from backend.schemas.common import EffortLevel, TaskType


class PriorityScoreBreakdown(BaseModel):
    importance: int = Field(ge=0)
    task_type: int = Field(ge=0)
    effort: int = Field(ge=0)
    workload: int = Field(ge=0)
    age: int = Field(ge=0)
    total: int = Field(ge=0, le=100)


class PriorityAnalysis(BaseModel):
    task_id: int
    task_title: str
    score: int = Field(ge=0, le=100)
    remaining_minutes: int = Field(ge=0)
    effective_workload_minutes: int = Field(ge=0)
    task_type: TaskType
    effort_level: EffortLevel
    splittable: bool
    recovery_buffer_minutes: int = Field(ge=0, le=120)
    breakdown: PriorityScoreBreakdown
    reasons: list[str] = Field(default_factory=list)
