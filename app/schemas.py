from pydantic import BaseModel
from .models import TaskStatus

class TaskBase(BaseModel):
    pass

class TaskCreate(TaskBase):
    pass

class TaskResponse(TaskBase):
    id: int
    status: TaskStatus
    result: str | None = None

    class Config:
        from_attributes = True
