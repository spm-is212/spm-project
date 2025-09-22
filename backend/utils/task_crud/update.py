from typing import Dict, Any, Optional
from backend.wrappers.supabase_wrapper.supabase_crud import SupabaseCRUD
from backend.schemas.task import TaskUpdate, MAIN_TASK_PARENT_ID


class TaskUpdater:
    """
    Task update utilities
    """

    def __init__(self):
        self.crud = SupabaseCRUD()
        self.table_name = "tasks"

    def update_tasks(self, main_task_id: str, user_role: str, main_task: Optional[TaskUpdate] = None, subtasks: Optional[Dict[str, TaskUpdate]] = None) -> Dict[str, Any]:
        """
        Update main task and/or subtasks

        Args:
            main_task_id: ID of the main task
            user_role: Role of the user updating the tasks
            main_task: Optional main task update data
            subtasks: Optional dictionary of {subtask_id: TaskUpdate} for updates

        Returns:
            Dictionary containing updated main task and subtasks
        """
        result = {
            "main_task": None,
            "updated_subtasks": []
        }

        if main_task:
            main_task_dict = {}

            if main_task.title:
                main_task_dict["title"] = main_task.title
            if main_task.description:
                main_task_dict["description"] = main_task.description
            if main_task.due_date:
                main_task_dict["due_date"] = main_task.due_date.isoformat()
            if main_task.status:
                main_task_dict["status"] = main_task.status.value
            if main_task.priority:
                main_task_dict["priority"] = main_task.priority.value
            if main_task.assignee_ids is not None:
                current_task = self.crud.select(self.table_name, filters={"id": main_task_id})
                if current_task:
                    current_assignees = set(current_task[0].get("assignee_ids", []))
                    new_assignees = set(main_task.assignee_ids)

                    if new_assignees.issubset(current_assignees) and len(new_assignees) < len(current_assignees):
                        if user_role == "manager":
                            main_task_dict["assignee_ids"] = main_task.assignee_ids
                    else:
                        main_task_dict["assignee_ids"] = main_task.assignee_ids

            if main_task_dict:
                main_task_dict["parent_id"] = MAIN_TASK_PARENT_ID
                results = self.crud.update(
                    self.table_name,
                    main_task_dict,
                    {"id": main_task_id}
                )
                result["main_task"] = results[0] if results else None

        if subtasks:
            for subtask_id, subtask_data in subtasks.items():
                subtask_dict = {}

                if subtask_data.title:
                    subtask_dict["title"] = subtask_data.title
                if subtask_data.description:
                    subtask_dict["description"] = subtask_data.description
                if subtask_data.due_date:
                    subtask_dict["due_date"] = subtask_data.due_date.isoformat()
                if subtask_data.status:
                    subtask_dict["status"] = subtask_data.status.value
                if subtask_data.priority:
                    subtask_dict["priority"] = subtask_data.priority.value

                if subtask_data.assignee_ids is not None:
                    current_subtask = self.crud.select(self.table_name, filters={"id": subtask_id})
                    if current_subtask:
                        current_assignees = set(current_subtask[0].get("assignee_ids", []))
                        new_assignees = set(subtask_data.assignee_ids)

                        if new_assignees.issubset(current_assignees) and len(new_assignees) < len(current_assignees):
                            if user_role == "manager":
                                subtask_dict["assignee_ids"] = subtask_data.assignee_ids
                        else:
                            subtask_dict["assignee_ids"] = subtask_data.assignee_ids

                if subtask_dict:
                    results = self.crud.update(
                        self.table_name,
                        subtask_dict,
                        {"id": subtask_id, "parent_id": main_task_id}
                    )
                    if results:
                        result["updated_subtasks"].append(results[0])

        return result
