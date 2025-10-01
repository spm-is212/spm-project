from typing import List, Dict, Any, Optional
from backend.wrappers.supabase_wrapper.supabase_crud import SupabaseCRUD
from backend.schemas.task import TaskCreate, MAIN_TASK_PARENT_ID
from backend.utils.task_crud.constants import (
    TASKS_TABLE_NAME,
    TITLE_FIELD,
    DESCRIPTION_FIELD,
    DUE_DATE_FIELD,
    STATUS_FIELD,
    PRIORITY_FIELD,
    OWNER_USER_ID_FIELD,
    ASSIGNEE_IDS_FIELD,
    PARENT_ID_FIELD,
    COMMENTS_FIELD,
    ATTACHMENTS_FIELD,
    IS_ARCHIVED_FIELD,
    MAIN_TASK_KEY,
    SUBTASKS_RESPONSE_KEY,
    TASK_ID_FIELD,
    DEFAULT_COMMENTS,
    DEFAULT_ATTACHMENTS,
    DEFAULT_IS_ARCHIVED,
)


class TaskCreator:
    """
    Task creation utilities
    """

    def __init__(self):
        self.crud = SupabaseCRUD()
        self.table_name = TASKS_TABLE_NAME

    def create_task_with_subtasks(self, user_id: str, main_task: TaskCreate, subtasks: Optional[List[TaskCreate]] = None) -> Dict[str, Any]:
        assignee_ids = list(main_task.assignee_ids) if main_task.assignee_ids else []
        if user_id not in assignee_ids:
            assignee_ids.append(user_id)

        main_task_dict = {
            TITLE_FIELD: main_task.title,
            DESCRIPTION_FIELD: main_task.description,
            DUE_DATE_FIELD: main_task.due_date.isoformat(),
            STATUS_FIELD: main_task.status.value,
            PRIORITY_FIELD: main_task.priority.value,
            OWNER_USER_ID_FIELD: user_id,
            ASSIGNEE_IDS_FIELD: assignee_ids,
            PARENT_ID_FIELD: MAIN_TASK_PARENT_ID,
            COMMENTS_FIELD: DEFAULT_COMMENTS,
            ATTACHMENTS_FIELD: DEFAULT_ATTACHMENTS,
            IS_ARCHIVED_FIELD: DEFAULT_IS_ARCHIVED,
           "recurrence_rule": main_task.recurrence_rule.value if main_task.recurrence_rule else None,
            "recurrence_interval": main_task.recurrence_interval,
            "recurrence_end_date": main_task.recurrence_end_date.isoformat() if main_task.recurrence_end_date else None,
        }

        created_main_task = self.crud.insert(self.table_name, main_task_dict)

        result = {
            MAIN_TASK_KEY: created_main_task,
            SUBTASKS_RESPONSE_KEY: []
        }

        if subtasks:
            for subtask_data in subtasks:
                subtask_assignee_ids = list(subtask_data.assignee_ids) if subtask_data.assignee_ids else []
                if user_id not in subtask_assignee_ids:
                    subtask_assignee_ids.append(user_id)

                subtask_dict = {
                    TITLE_FIELD: subtask_data.title,
                    DESCRIPTION_FIELD: subtask_data.description,
                    DUE_DATE_FIELD: subtask_data.due_date.isoformat(),
                    STATUS_FIELD: subtask_data.status.value,
                    PRIORITY_FIELD: subtask_data.priority.value,
                    OWNER_USER_ID_FIELD: user_id,
                    ASSIGNEE_IDS_FIELD: subtask_assignee_ids,
                    PARENT_ID_FIELD: created_main_task[TASK_ID_FIELD],
                    COMMENTS_FIELD: DEFAULT_COMMENTS,
                    ATTACHMENTS_FIELD: DEFAULT_ATTACHMENTS,
                    IS_ARCHIVED_FIELD: DEFAULT_IS_ARCHIVED,
                    "recurrence_rule": subtask_data.recurrence_rule.value if subtask_data.recurrence_rule else None,
                    "recurrence_interval": subtask_data.recurrence_interval,
                    "recurrence_end_date": subtask_data.recurrence_end_date.isoformat() if subtask_data.recurrence_end_date else None,
                }

                created_subtask = self.crud.insert(self.table_name, subtask_dict)
                result[SUBTASKS_RESPONSE_KEY].append(created_subtask)

        return result
