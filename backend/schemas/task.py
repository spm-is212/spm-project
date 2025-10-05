from pydantic import BaseModel
from typing import Optional


class TaskCreate(BaseModel):
    title: str
<<<<<<< Updated upstream
    description: Optional[str] = None
=======
    description: str
    project_id: Optional[str] = Field(None, description="Optional: Project ID that this task belongs to")
    due_date: date
    status: TaskStatus = TaskStatus.TO_DO
    priority: TaskPriority
    assignee_ids: List[str]
    file_url: Optional[str] = Field(None, description="Public URL of the task file stored in Supabase")
    parent_id: Optional[str] = Field(default=MAIN_TASK_PARENT_ID)

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
    priority: TaskPriority
    assignee_ids: Optional[List[str]] = None
    file_url: Optional[str] = Field(None, description="Public URL of the subtask file stored in Supabase")
    parent_id: Optional[str] = None
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

    @field_validator("due_date")
    @classmethod
    def due_date_not_past(cls, v: date) -> date:
        if v < date.today():
            raise ValueError("Due date cannot be in the past")
        return v
>>>>>>> Stashed changes

    @field_validator("file_url")
    @classmethod
    def file_url_not_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("File URL cannot be empty")
        return v

class TaskUpdate(BaseModel):
    task_uuid: str
    title: Optional[str] = None
    description: Optional[str] = None
<<<<<<< Updated upstream
=======
    project_id: Optional[str] = Field(None, description="Project ID that this task belongs to")
    due_date: Optional[date] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assignee_ids: Optional[List[str]] = None
    file_url: Optional[str] = None
    is_archived: Optional[bool] = None

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
    priority: Optional[TaskPriority] = None
    assignee_ids: Optional[List[str]] = None
    file_url: Optional[str] = None
    is_archived: Optional[bool] = None

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
>>>>>>> Stashed changes
