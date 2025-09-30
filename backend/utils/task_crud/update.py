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

    def can_remove_assignees(self, user_role: str, user_teams: list) -> bool:
        if user_role in ["manager", "director"]:
            return True
        privileged_teams = ["sales manager", "finance managers"]
        return any(team in privileged_teams for team in user_teams)

    def _validate_main_task_archival(self, main_task_id: str, is_archived: bool) -> bool:
        if not is_archived:
            return True
        subtasks = self.crud.select(self.table_name, filters={"parent_id": main_task_id})
        if not subtasks:
            return True
        for subtask in subtasks:
            if not subtask.get("is_archived", False):
                return False
        return True

    def update_tasks(
        self,
        main_task_id: str,
        user_role: str,
        user_teams: list,
        main_task: Optional[TaskUpdate] = None,
        subtasks: Optional[Dict[str, TaskUpdate]] = None
    ) -> Dict[str, Any]:
        result = {
            "main_task": None,
            "updated_subtasks": []
        }

        # --- MAIN TASK UPDATE ---
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
                        if self.can_remove_assignees(user_role, user_teams):
                            main_task_dict["assignee_ids"] = main_task.assignee_ids
                    else:
                        main_task_dict["assignee_ids"] = main_task.assignee_ids

            if main_task.is_archived is not None:
                main_task_dict["is_archived"] = main_task.is_archived

            # ✅ recurrence for main task
            if main_task.recurrence_rule is not None:
                main_task_dict["recurrence_rule"] = main_task.recurrence_rule.value
            if main_task.recurrence_interval is not None:
                main_task_dict["recurrence_interval"] = main_task.recurrence_interval
            if main_task.recurrence_end_date is not None:
                main_task_dict["recurrence_end_date"] = main_task.recurrence_end_date.isoformat()

            if main_task_dict:
                main_task_dict["parent_id"] = MAIN_TASK_PARENT_ID
                results = self.crud.update(
                    self.table_name,
                    main_task_dict,
                    {"id": main_task_id}
                )
                result["main_task"] = results[0] if results else None

        # --- SUBTASKS UPDATE ---
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
                            if self.can_remove_assignees(user_role, user_teams):
                                subtask_dict["assignee_ids"] = subtask_data.assignee_ids
                        else:
                            subtask_dict["assignee_ids"] = subtask_data.assignee_ids

                if subtask_data.is_archived is not None:
                    subtask_dict["is_archived"] = subtask_data.is_archived

                # ✅ recurrence for subtasks (if allowed)
                if subtask_data.recurrence_rule is not None:
                    subtask_dict["recurrence_rule"] = subtask_data.recurrence_rule.value
                if subtask_data.recurrence_interval is not None:
                    subtask_dict["recurrence_interval"] = subtask_data.recurrence_interval
                if subtask_data.recurrence_end_date is not None:
                    subtask_dict["recurrence_end_date"] = subtask_data.recurrence_end_date.isoformat()

                if subtask_dict:
                    results = self.crud.update(
                        self.table_name,
                        subtask_dict,
                        {"id": subtask_id, "parent_id": main_task_id}
                    )
                    if results:
                        result["updated_subtasks"].append(results[0])

        return result
