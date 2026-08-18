from enum import Enum, IntEnum

from pydantic import BaseModel


class PriorityLevel(IntEnum):
    NORMAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3


class TaskType(str, Enum):
    GENERAL = "general"
    ASSIGNMENT = "assignment"
    EXAM_PREPARATION = "exam_preparation"
    PROJECT = "project"
    STUDY = "study"
    ADMIN = "admin"
    CHORE = "chore"
    PERSONAL = "personal"


class EffortLevel(IntEnum):
    LIGHT = 0
    MODERATE = 1
    HEAVY = 2


class MessageResponse(BaseModel):
    message: str
