from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict
from datetime import date
from enum import Enum

# Constants
MAIN_TASK_PARENT_ID = None
DEFAULT_TASK_STATUS = "TO_DO"


class TaskStatus(str, Enum):
    TO_DO = "TO_DO"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"


class TaskPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class TaskCreate(BaseModel):
    title: str
    description: str
    due_date: date
    status: TaskStatus = TaskStatus.TO_DO
    priority: TaskPriority
    assignee_ids: List[str]
    parent_id: Optional[str] = Field(default=MAIN_TASK_PARENT_ID, description="Parent ID for main tasks is always None")

    @field_validator('title')
    @classmethod
    def title_not_empty(cls, v):
        if v.strip() == '':
            raise ValueError('Title cannot be empty')
        return v

    @field_validator('description')
    @classmethod
    def description_not_empty(cls, v):
        if v.strip() == '':
            raise ValueError('Description cannot be empty')
        return v

    @field_validator('assignee_ids')
    @classmethod
    def assignee_ids_not_empty(cls, v):
        # Allow empty assignee list - creator will be auto-assigned in TaskCreator
        if v is not None and len(v) > 5:
            raise ValueError('Maximum of 5 assignees allowed per task')
        return v

    @field_validator('due_date')
    @classmethod
    def due_date_not_past(cls, v):
        from datetime import date
        if v < date.today():
            raise ValueError('Due date cannot be in the past')
        return v


class SubtaskCreate(BaseModel):
    title: str
    description: str
    due_date: date
    status: TaskStatus = TaskStatus.TO_DO
    priority: TaskPriority
    assignee_ids: Optional[List[str]] = None
    parent_id: Optional[str] = None

    @field_validator('title')
    @classmethod
    def title_not_empty(cls, v):
        if v.strip() == '':
            raise ValueError('Title cannot be empty')
        return v

    @field_validator('description')
    @classmethod
    def description_not_empty(cls, v):
        if v.strip() == '':
            raise ValueError('Description cannot be empty')
        return v

    @field_validator('assignee_ids')
    @classmethod
    def assignee_ids_not_empty_if_provided(cls, v):
        # Allow empty assignee list - creator will be auto-assigned in TaskCreator
        if v is not None and len(v) > 5:
            raise ValueError('Maximum of 5 assignees allowed per subtask')
        return v

    @field_validator('due_date')
    @classmethod
    def due_date_not_past(cls, v):
        from datetime import date
        if v < date.today():
            raise ValueError('Due date cannot be in the past')
        return v


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[date] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assignee_ids: Optional[List[str]] = None
    is_archived: Optional[bool] = None

    @field_validator('title')
    @classmethod
    def title_not_empty(cls, v):
        if v is not None and v.strip() == '':
            raise ValueError('Title cannot be empty')
        return v

    @field_validator('description')
    @classmethod
    def description_not_empty(cls, v):
        if v is not None and v.strip() == '':
            raise ValueError('Description cannot be empty')
        return v

    @field_validator('assignee_ids')
    @classmethod
    def assignee_ids_not_empty_if_provided(cls, v):
        # Allow empty list for testing assignee removal
        if v is not None and len(v) > 5:
            raise ValueError('Maximum of 5 assignees allowed per task')
        return v

    @field_validator('due_date')
    @classmethod
    def due_date_not_past(cls, v):
        if v is not None:
            from datetime import date
            if v < date.today():
                raise ValueError('Due date cannot be in the past')
        return v


class SubtaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[date] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assignee_ids: Optional[List[str]] = None
    is_archived: Optional[bool] = None

    @field_validator('title')
    @classmethod
    def title_not_empty(cls, v):
        if v is not None and v.strip() == '':
            raise ValueError('Title cannot be empty')
        return v

    @field_validator('description')
    @classmethod
    def description_not_empty(cls, v):
        if v is not None and v.strip() == '':
            raise ValueError('Description cannot be empty')
        return v

    @field_validator('assignee_ids')
    @classmethod
    def assignee_ids_not_empty_if_provided(cls, v):
        if v is not None and len(v) == 0:
            raise ValueError('Assignee IDs list cannot be empty if provided')
        if v is not None and len(v) > 5:
            raise ValueError('Maximum of 5 assignees allowed per subtask')
        return v

    @field_validator('due_date')
    @classmethod
    def due_date_not_past(cls, v):
        if v is not None:
            from datetime import date
            if v < date.today():
                raise ValueError('Due date cannot be in the past')
        return v


class TaskCreateRequest(BaseModel):
    main_task: TaskCreate
    subtasks: Optional[List[SubtaskCreate]] = None


class TaskUpdateRequest(BaseModel):
    main_task_id: str
    main_task: Optional[TaskUpdate] = None
    subtasks: Optional[Dict[str, SubtaskUpdate]] = None
