from pydantic import BaseModel, constr
from .models import TaskStatus

class TaskBase(BaseModel):
    pass

class TaskCreate(TaskBase):
    input_data: constr(min_length=1, max_length=500)

class TaskResponse(TaskBase):
    id: int
    status: TaskStatus
    result: str | None = None

    class Config:
        from_attributes = True
