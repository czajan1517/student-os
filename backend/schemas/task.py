from pydantic import BaseModel
from datetime import datetime

class TaskCreate(BaseModel):

    title: str 
    description: str | None = None
    priority: int | None = None
    estimated_time: int | None = None
    due_date: datetime | None = None


class TaskUpdate(BaseModel):

    title: str | None = None
    description: str | None = None
    priority: int | None = None
    estimated_time: int | None = None
    due_date: datetime | None = None



