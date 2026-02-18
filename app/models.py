from sqlalchemy import Column, Integer, String, Enum
from .database import Base
import enum

class TaskStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String, default=TaskStatus.PENDING, index=True)
    result = Column(String, nullable=True)
