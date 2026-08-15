from enum import IntEnum

from pydantic import BaseModel


class PriorityLevel(IntEnum):
    NORMAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3


class MessageResponse(BaseModel):
    message: str
