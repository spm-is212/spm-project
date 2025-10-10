from pydantic import BaseModel, Field, field_validator, ValidationInfo
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

class RecurrenceRule(str, Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"

class TaskCreate(BaseModel):
    title: str
    description: str
    project_id: Optional[str] = Field(None, description="Optional: Project ID that this task belongs to")
    due_date: date
    status: TaskStatus = TaskStatus.TO_DO
    priority: int
    assignee_ids: List[str]
    parent_id: Optional[str] = Field(default=MAIN_TASK_PARENT_ID)
    file_url: Optional[str] = Field(None, description="Public URL of the task file stored in Supabase")

    # recurrence fields
    recurrence_rule: Optional[RecurrenceRule] = None
    recurrence_interval: Optional[int] = 1
    recurrence_end_date: Optional[date] = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Title cannot be empty")
        return v

    @field_validator("description")
    @classmethod
    def description_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Description cannot be empty")
        return v

    @field_validator("priority")
    @classmethod
    def priority_between_1_and_10(cls, v: int) -> int:
        if v < 1 or v > 10:
            raise ValueError("Priority must be between 1 and 10")
        return v

    @field_validator("assignee_ids")
    @classmethod
    def assignee_ids_not_empty(cls, v: List[str]) -> List[str]:
        if v is not None and len(v) > 5:
            raise ValueError("Maximum of 5 assignees allowed per task")
        return v

    @field_validator("due_date")
    @classmethod
    def due_date_not_past(cls, v: date) -> date:
        if v < date.today():
            raise ValueError("Due date cannot be in the past")
        return v

    @field_validator("recurrence_interval")
    @classmethod
    def interval_must_be_positive(cls, v: int, info: ValidationInfo) -> int:
        if info.data.get("recurrence_rule") and v < 1:
            raise ValueError("Recurrence interval must be at least 1")
        return v

    @field_validator("recurrence_end_date")
    @classmethod
    def end_date_after_due_date(cls, v: Optional[date], info: ValidationInfo) -> Optional[date]:
        if v and info.data.get("due_date") and v < info.data["due_date"]:
            raise ValueError("Recurrence end date cannot be before the due date")
        return v

    @field_validator("file_url")
    @classmethod
    def file_url_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("File URL cannot be empty")
        return v


class SubtaskCreate(BaseModel):
    title: str
    description: str
    project_id: Optional[str] = Field(None, description="Optional: Project ID that this subtask belongs to")
    due_date: date
    status: TaskStatus = TaskStatus.TO_DO
    priority: int
    assignee_ids: Optional[List[str]] = None
    parent_id: Optional[str] = None
    file_url: Optional[str] = Field(None, description="Public URL of the subtask file stored in Supabase")
    recurrence_rule: Optional[RecurrenceRule] = None
    recurrence_interval: Optional[int] = 1
    recurrence_end_date: Optional[date] = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Title cannot be empty")
        return v

    @field_validator("description")
    @classmethod
    def description_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Description cannot be empty")
        return v

    @field_validator("assignee_ids")
    @classmethod
    def assignee_ids_not_empty_if_provided(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is not None and len(v) > 5:
            raise ValueError("Maximum of 5 assignees allowed per subtask")
        return v

    @field_validator("priority")
    @classmethod
    def priority_between_1_and_10(cls, v: int) -> int:
        if v < 1 or v > 10:
            raise ValueError("Priority must be between 1 and 10")
        return v

    @field_validator("due_date")
    @classmethod
    def due_date_not_past(cls, v: date) -> date:
        if v < date.today():
            raise ValueError("Due date cannot be in the past")
        return v

    @field_validator("file_url")
    @classmethod
    def file_url_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("File URL cannot be empty")
        return v


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    project_id: Optional[str] = Field(None, description="Project ID that this task belongs to")
    due_date: Optional[date] = None
    status: Optional[TaskStatus] = None
    priority: Optional[int] = None
    assignee_ids: Optional[List[str]] = None
    is_archived: Optional[bool] = None
    file_url: Optional[str] = None

    # recurrence fields
    recurrence_rule: Optional[RecurrenceRule] = None
    recurrence_interval: Optional[int] = None
    recurrence_end_date: Optional[date] = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Title cannot be empty")
        return v

    @field_validator("description")
    @classmethod
    def description_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Description cannot be empty")
        return v

    @field_validator("assignee_ids")
    @classmethod
    def assignee_ids_not_empty_if_provided(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is not None and len(v) > 5:
            raise ValueError("Maximum of 5 assignees allowed per task")
        return v

    @field_validator("priority")
    @classmethod
    def priority_between_1_and_10(cls, v: int) -> int:
        if v < 1 or v > 10:
            raise ValueError("Priority must be between 1 and 10")
        return v

    @field_validator("due_date")
    @classmethod
    def due_date_not_past(cls, v: Optional[date]) -> Optional[date]:
        if v and v < date.today():
            raise ValueError("Due date cannot be in the past")
        return v

    @field_validator("recurrence_interval")
    @classmethod
    def interval_must_be_positive(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 1:
            raise ValueError("Recurrence interval must be at least 1")
        return v

    @field_validator("recurrence_end_date")
    @classmethod
    def end_date_after_due_date(cls, v: Optional[date], info: ValidationInfo) -> Optional[date]:
        if v and info.data.get("due_date") and v < info.data["due_date"]:
            raise ValueError("Recurrence end date cannot be before the due date")
        return v

    @field_validator("file_url")
    @classmethod
    def file_url_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("File URL cannot be empty")
        return v


class SubtaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[date] = None
    status: Optional[TaskStatus] = None
    priority: Optional[int] = None
    assignee_ids: Optional[List[str]] = None
    is_archived: Optional[bool] = None
    file_url: Optional[str] = None

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Title cannot be empty")
        return v

    @field_validator("description")
    @classmethod
    def description_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("Description cannot be empty")
        return v

    @field_validator("priority")
    @classmethod
    def priority_between_1_and_10(cls, v: int) -> int:
        if v < 1 or v > 10:
            raise ValueError("Priority must be between 1 and 10")
        return v

    @field_validator("assignee_ids")
    @classmethod
    def assignee_ids_not_empty_if_provided(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is not None and len(v) == 0:
            raise ValueError("Assignee IDs list cannot be empty if provided")
        if v is not None and len(v) > 5:
            raise ValueError("Maximum of 5 assignees allowed per subtask")
        return v

    @field_validator("due_date")
    @classmethod
    def due_date_not_past(cls, v: Optional[date]) -> Optional[date]:
        if v and v < date.today():
            raise ValueError("Due date cannot be in the past")
        return v

    @field_validator("file_url")
    @classmethod
    def file_url_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("File URL cannot be empty")
        return v


class TaskCreateRequest(BaseModel):
    main_task: TaskCreate
    subtasks: Optional[List[SubtaskCreate]] = None


class TaskUpdateRequest(BaseModel):
    main_task_id: str
    main_task: Optional[TaskUpdate] = None
    subtasks: Optional[Dict[str, SubtaskUpdate]] = None
    new_subtasks: Optional[List[SubtaskCreate]] = None
