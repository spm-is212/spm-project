"""
Task CRUD constants and configuration values.

This module contains all hard-coded values used throughout the task CRUD operations
to centralize configuration and improve maintainability.
"""
from datetime import date, timedelta

# Database table names
TASKS_TABLE_NAME = "tasks"

# User roles with specific access permissions
MANAGING_DIRECTOR_ROLE = "managing_director"
DIRECTOR_ROLE = "director"
MANAGER_ROLE = "manager"

# Teams with privileged access (department-wide visibility)
PRIVILEGED_TEAMS = ["sales manager", "finance managers"]

# User roles that can remove assignees
ASSIGNEE_REMOVAL_ROLES = ["manager", "director", "managing_director"]

# Task and subtask field names
OWNER_USER_ID_FIELD = "owner_user_id"
ASSIGNEE_IDS_FIELD = "assignee_ids"
PARENT_ID_FIELD = "parent_id"
IS_ARCHIVED_FIELD = "is_archived"
TASK_ID_FIELD = "id"
USER_ID_FIELD = "id"
TITLE_FIELD = "title"
DESCRIPTION_FIELD = "description"
DUE_DATE_FIELD = "due_date"
STATUS_FIELD = "status"
PRIORITY_FIELD = "priority"
COMMENTS_FIELD = "comments"
ATTACHMENTS_FIELD = "attachments"

# Default values for new tasks/subtasks
DEFAULT_COMMENTS = []
DEFAULT_ATTACHMENTS = []
DEFAULT_IS_ARCHIVED = False

# Response keys for complex operations
SUBTASK_KEY = "subtask"
MAIN_TASK_KEY = "main_task"
MAIN_TASK_RESPONSE_KEY = "main_task"
UPDATED_SUBTASKS_RESPONSE_KEY = "updated_subtasks"
SUBTASKS_RESPONSE_KEY = "subtasks"

# Validation error messages
TASK_ASSIGNEE_REQUIRED_ERROR = "Task must have at least one assignee"
SUBTASK_ASSIGNEE_REQUIRED_ERROR = "Subtask must have at least one assignee"

def make_future_due_date():
    return (date.today() + timedelta(days=7)).isoformat()