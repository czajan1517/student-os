from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.schemas.common import TaskType


class SuggestedImportance(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    MEDIUM = "medium"
    HIGH = "high"


class SuggestedEffort(str, Enum):
    LIGHT = "light"
    MODERATE = "moderate"
    HEAVY = "heavy"


class TaskClassificationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    due_date: datetime | None = None
    estimated_time_minutes: int | None = Field(default=None, gt=0, le=1440)


class TaskClassification(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task_type: TaskType
    effort_level: SuggestedEffort
    suggested_importance: SuggestedImportance
    estimated_time_minutes: int | None = Field(default=None, gt=0, le=1440)
    recovery_buffer_minutes: int = Field(ge=0, le=120)
    splittable: bool
    confidence: float = Field(ge=0, le=1)
    reasons: list[str]
    assumptions: list[str]
    follow_up_questions: list[str]


class ChatMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    messages: list[ChatMessage] = Field(min_length=1, max_length=20)

    @model_validator(mode="after")
    def require_latest_user_message(self):
        if self.messages[-1].role != "user":
            raise ValueError("The latest chat message must come from the user")
        return self


class ChatResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1)
