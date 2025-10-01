from typing import List, Dict, Any, Optional
from backend.wrappers.supabase_wrapper.supabase_crud import SupabaseCRUD
from backend.schemas.task import TaskCreate, MAIN_TASK_PARENT_ID


class TaskCreator:
    """
    Task creation utilities
    """

    def __init__(self):
        self.crud = SupabaseCRUD()
        self.table_name = "tasks"

    def create_task_with_subtasks(self, user_id: str, main_task: TaskCreate, subtasks: Optional[List[TaskCreate]] = None) -> Dict[str, Any]:
        """
        Create a main task and optional subtasks

        Args:
            user_id: ID of the user creating the tasks
            main_task: Main task data
            subtasks: Optional list of subtask data

        Returns:
            Dictionary containing main task and created subtasks
        """
        assignee_ids = list(main_task.assignee_ids) if main_task.assignee_ids else []
        if user_id not in assignee_ids:
            assignee_ids.append(user_id)

        main_task_dict = {
            "title": main_task.title,
            "description": main_task.description,
            "due_date": main_task.due_date.isoformat(),
            "status": main_task.status.value,
            "priority": main_task.priority.value,
            "owner_user_id": user_id,
            "assignee_ids": assignee_ids,
            "parent_id": MAIN_TASK_PARENT_ID,
            "comments": [],
            "attachments": [],
            "is_archived": False,
            "recurrence_rule": str(main_task.recurrence_rule) if main_task.recurrence_rule else None,
            "recurrence_interval": main_task.recurrence_interval,
            "recurrence_end_date": main_task.recurrence_end_date.isoformat() if main_task.recurrence_end_date else None,
        }

        created_main_task = self.crud.insert(self.table_name, main_task_dict)

        result = {
            "main_task": created_main_task,
            "subtasks": []
        }

        if subtasks:
            for subtask_data in subtasks:
                subtask_assignee_ids = list(subtask_data.assignee_ids) if subtask_data.assignee_ids else []
                if user_id not in subtask_assignee_ids:
                    subtask_assignee_ids.append(user_id)

                subtask_dict = {
                    "title": subtask_data.title,
                    "description": subtask_data.description,
                    "due_date": subtask_data.due_date.isoformat(),
                    "status": subtask_data.status.value,
                    "priority": subtask_data.priority.value,
                    "owner_user_id": user_id,
                    "assignee_ids": subtask_assignee_ids,
                    "parent_id": created_main_task["id"],  # Set parent to main task ID
                    "comments": [],
                    "attachments": [],
                    "is_archived": False,
                    "recurrence_rule": str(subtask_data.recurrence_rule) if subtask_data.recurrence_rule else None,
                    "recurrence_interval": subtask_data.recurrence_interval,
                    "recurrence_end_date": subtask_data.recurrence_end_date.isoformat() if subtask_data.recurrence_end_date else None,

                }

                created_subtask = self.crud.insert(self.table_name, subtask_dict)
                result["subtasks"].append(created_subtask)

        return result
