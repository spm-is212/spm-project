from pydantic import BaseModel, field_validator
from typing import List, Literal
from datetime import date


class TaskCompletionRequest(BaseModel):
    """Request schema for task completion report"""
    scope_type: Literal["project", "staff"]
    scope_id: str
    start_date: date
    end_date: date
    export_format: Literal["xlsx", "pdf"] = "xlsx"

    @field_validator("end_date")
    @classmethod
    def end_date_after_start_date(cls, v: date, info) -> date:
        if "start_date" in info.data and v < info.data["start_date"]:
            raise ValueError("end_date must be after or equal to start_date")
        return v


class TaskCompletionItem(BaseModel):
    """Individual task item in the completion report"""
    task_title: str
    priority: int
    status: str
    due_date: str
    overdue: bool


class TaskCompletionResponse(BaseModel):
    """Response schema for task completion report"""
    scope_type: str
    scope_id: str
    scope_name: str  # Project name or staff email
    start_date: str
    end_date: str
    total_tasks: int
    tasks: List[TaskCompletionItem]


# Team Summary Report Schemas
class TeamSummaryRequest(BaseModel):
    """Request schema for team summary report"""
    scope_type: Literal["department", "project"]
    scope_id: str  # Department name or Project ID
    time_frame: Literal["weekly", "monthly"]
    start_date: date
    end_date: date
    export_format: Literal["xlsx", "pdf"] = "xlsx"

    @field_validator("end_date")
    @classmethod
    def end_date_after_start_date(cls, v: date, info) -> date:
        if "start_date" in info.data and v < info.data["start_date"]:
            raise ValueError("end_date must be after or equal to start_date")
        return v


class StaffTaskSummary(BaseModel):
    """Individual staff member's task summary"""
    staff_name: str
    blocked: int
    in_progress: int
    completed: int
    overdue: int
    total_tasks: int


class TeamSummaryResponse(BaseModel):
    """Response schema for team summary report"""
    scope_type: str
    scope_id: str
    scope_name: str  # Department name or Project name
    time_frame: str
    start_date: str
    end_date: str
    total_staff: int
    staff_summaries: List[StaffTaskSummary]


# Logged Time Report Schemas
class LoggedTimeRequest(BaseModel):
    """Request schema for logged time report"""
    scope_type: Literal["department", "project"]
    scope_id: str  # Department name or Project ID
    start_date: date
    end_date: date
    export_format: Literal["xlsx", "pdf"] = "xlsx"

    @field_validator("end_date")
    @classmethod
    def end_date_after_start_date(cls, v: date, info) -> date:
        if "start_date" in info.data and v < info.data["start_date"]:
            raise ValueError("end_date must be after or equal to start_date")
        return v


class LoggedTimeItem(BaseModel):
    """Individual time log entry"""
    staff_name: str
    task_title: str
    time_log: float  # hours
    status: str
    due_date: str
    overdue: bool


class LoggedTimeResponse(BaseModel):
    """Response schema for logged time report"""
    scope_type: str
    scope_id: str
    scope_name: str  # Department name or Project name
    start_date: str
    end_date: str
    total_entries: int
    total_hours: float
    time_entries: List[LoggedTimeItem]
