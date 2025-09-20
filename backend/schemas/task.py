from pydantic import BaseModel
from typing import Optional


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None


class TaskUpdate(BaseModel):
    task_uuid: str
    title: Optional[str] = None
    description: Optional[str] = None
