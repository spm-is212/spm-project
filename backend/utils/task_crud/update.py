from typing import Dict, Any, Optional, List
from datetime import datetime
from backend.wrappers.supabase_wrapper.supabase_crud import SupabaseCRUD
from backend.schemas.task import TaskUpdate, SubtaskCreate, MAIN_TASK_PARENT_ID
from backend.utils.task_crud.create import TaskCreator
from backend.utils.task_crud.constants import (
    TASKS_TABLE_NAME,
    ASSIGNEE_REMOVAL_ROLES,
    PRIVILEGED_TEAMS,
    PARENT_ID_FIELD,
    IS_ARCHIVED_FIELD,
    TASK_ID_FIELD,
    TITLE_FIELD,
    DESCRIPTION_FIELD,
    DUE_DATE_FIELD,
    STATUS_FIELD,
    PRIORITY_FIELD,
    ASSIGNEE_IDS_FIELD,
    FILE_URL_FIELD,
    TASK_ASSIGNEE_REQUIRED_ERROR,
    SUBTASK_ASSIGNEE_REQUIRED_ERROR,
    MAIN_TASK_RESPONSE_KEY,
    UPDATED_SUBTASKS_RESPONSE_KEY,
    OWNER_USER_ID_FIELD,
    DEFAULT_IS_ARCHIVED,
)


class TaskUpdater:
    """Task update utilities"""

    def __init__(self):
        self.crud = SupabaseCRUD()
        self.table_name = TASKS_TABLE_NAME

    def can_remove_assignees(self, user_role: str, user_teams: list) -> bool:
        """
        Check if user can remove assignee IDs based on role and teams

        Rules:
        - Role is "manager" or "director"
        - Teams include "sales manager" or "finance managers"
        """
        if user_role in ASSIGNEE_REMOVAL_ROLES:
            return True
        return any(team in PRIVILEGED_TEAMS for team in user_teams)

    def _validate_main_task_archival(self, main_task_id: str, is_archived: bool) -> bool:
        if not is_archived:
            return True

        subtasks = self.crud.select(self.table_name, filters={PARENT_ID_FIELD: main_task_id})
        if not subtasks:
            return True

        for subtask in subtasks:
            if not subtask.get(IS_ARCHIVED_FIELD, False):
                return False
        return True

    def update_tasks(
        self,
        main_task_id: str,
        user_id: str,
        user_role: str,
        user_teams: list,
        main_task: Optional[TaskUpdate] = None,
        subtasks: Optional[Dict[str, TaskUpdate]] = None,
        new_subtasks: Optional[List[SubtaskCreate]] = None,
    ) -> Dict[str, Any]:
        result = {
            MAIN_TASK_RESPONSE_KEY: None,
            UPDATED_SUBTASKS_RESPONSE_KEY: []
        }

        # --- MAIN TASK UPDATE ---
        if main_task:
            main_task_dict = {}

            if main_task.title:
                main_task_dict[TITLE_FIELD] = main_task.title
            if main_task.description:
                main_task_dict[DESCRIPTION_FIELD] = main_task.description
            if main_task.due_date:
                main_task_dict[DUE_DATE_FIELD] = main_task.due_date.isoformat()
            if main_task.status:
                main_task_dict[STATUS_FIELD] = main_task.status.value
            if main_task.priority:
                main_task_dict[PRIORITY_FIELD] = main_task.priority
            if main_task.assignee_ids is not None:
                current_task = self.crud.select(self.table_name, filters={TASK_ID_FIELD: main_task_id})
                if current_task:
                    current_assignees = set(current_task[0].get(ASSIGNEE_IDS_FIELD, []))
                    new_assignees = set(main_task.assignee_ids)
                    is_removal = new_assignees.issubset(current_assignees) and len(new_assignees) < len(current_assignees)

                    if is_removal:
                        if self.can_remove_assignees(user_role, user_teams):
                            if len(main_task.assignee_ids) == 0:
                                raise ValueError(TASK_ASSIGNEE_REQUIRED_ERROR)
                            main_task_dict[ASSIGNEE_IDS_FIELD] = main_task.assignee_ids
                    else:
                        if len(main_task.assignee_ids) == 0:
                            raise ValueError(TASK_ASSIGNEE_REQUIRED_ERROR)
                        main_task_dict[ASSIGNEE_IDS_FIELD] = main_task.assignee_ids

            if main_task.is_archived is not None:
                main_task_dict[IS_ARCHIVED_FIELD] = main_task.is_archived

            if hasattr(main_task, 'file_url') and main_task.file_url is not None:
                main_task_dict[FILE_URL_FIELD] = main_task.file_url

            # ✅ Recurrence fields
            if main_task.recurrence_rule is not None:
                main_task_dict["recurrence_rule"] = main_task.recurrence_rule.value
            if main_task.recurrence_interval is not None:
                main_task_dict["recurrence_interval"] = main_task.recurrence_interval
            if main_task.recurrence_end_date is not None:
                main_task_dict["recurrence_end_date"] = main_task.recurrence_end_date.isoformat()

            if main_task_dict:
                main_task_dict_with_parent = {**main_task_dict, PARENT_ID_FIELD: MAIN_TASK_PARENT_ID}
                results = self.crud.update(
                    self.table_name,
                    main_task_dict_with_parent,
                    {TASK_ID_FIELD: main_task_id}
                )
                if results:
                    result[MAIN_TASK_RESPONSE_KEY] = results[0] if isinstance(results, list) else results
            else:
                result[MAIN_TASK_RESPONSE_KEY] = None

            if (
                main_task.recurrence_rule is not None
                or main_task.recurrence_interval is not None
                or main_task.recurrence_end_date is not None
            ):
                creator = TaskCreator()
                try:
                    self.crud.delete(
                        self.table_name,
                        filters={
                            PARENT_ID_FIELD: main_task_id,
                        }
                    )
                except Exception as e:
                    print(f"[TaskUpdater] Warning: Failed to delete old recurrence instances: {e}")

                current_task_data = self.crud.select(self.table_name, filters={TASK_ID_FIELD: main_task_id})
                if current_task_data:
                    current_task = current_task_data[0]
                    try:
                        recurrence_dates = creator._generate_recurrence_dates(
                            start_date=datetime.fromisoformat(current_task["due_date"]),
                            rule=current_task.get("recurrence_rule"),
                            interval=current_task.get("recurrence_interval", 1),
                            end_date=datetime.fromisoformat(current_task["recurrence_end_date"])
                            if current_task.get("recurrence_end_date")
                            else None
                        )

                        for due_date in recurrence_dates[1:]:
                            instance_dict = {
                                TITLE_FIELD: current_task[TITLE_FIELD],
                                DESCRIPTION_FIELD: current_task[DESCRIPTION_FIELD],
                                DUE_DATE_FIELD: due_date.isoformat(),
                                STATUS_FIELD: current_task[STATUS_FIELD],
                                PRIORITY_FIELD: current_task[PRIORITY_FIELD],
                                OWNER_USER_ID_FIELD: current_task[OWNER_USER_ID_FIELD],
                                ASSIGNEE_IDS_FIELD: current_task.get(ASSIGNEE_IDS_FIELD, []),
                                PARENT_ID_FIELD: main_task_id,
                                IS_ARCHIVED_FIELD: DEFAULT_IS_ARCHIVED,
                                "recurrence_rule": current_task.get("recurrence_rule"),
                                "recurrence_interval": current_task.get("recurrence_interval"),
                                "recurrence_end_date": current_task.get("recurrence_end_date"),
                            }

                            if current_task.get("project_id"):
                                instance_dict["project_id"] = current_task["project_id"]

                            self.crud.insert(self.table_name, instance_dict)

                        print(f"[TaskUpdater] Regenerated {len(recurrence_dates) - 1} recurrence instances for task {main_task_id}")
                    except Exception as e:
                        print(f"[TaskUpdater] Error regenerating recurrence instances: {e}")

        # --- ✅ SUBTASKS UPDATE ---
        if subtasks:
            for subtask_id, subtask_data in subtasks.items():
                subtask_dict = {}

                if subtask_data.title:
                    subtask_dict[TITLE_FIELD] = subtask_data.title
                if subtask_data.description:
                    subtask_dict[DESCRIPTION_FIELD] = subtask_data.description
                if subtask_data.due_date:
                    subtask_dict[DUE_DATE_FIELD] = subtask_data.due_date.isoformat()
                if subtask_data.status:
                    subtask_dict[STATUS_FIELD] = subtask_data.status.value
                if subtask_data.priority:
                    subtask_dict[PRIORITY_FIELD] = subtask_data.priority

                if subtask_data.assignee_ids is not None:
                    current_subtask = self.crud.select(self.table_name, filters={TASK_ID_FIELD: subtask_id})
                    if current_subtask:
                        current_assignees = set(current_subtask[0].get(ASSIGNEE_IDS_FIELD, []))
                        new_assignees = set(subtask_data.assignee_ids)
                        is_removal = new_assignees.issubset(current_assignees) and len(new_assignees) < len(current_assignees)

                        if is_removal:
                            # Managers/directors can remove
                            if self.can_remove_assignees(user_role, user_teams):
                                if len(subtask_data.assignee_ids) == 0:
                                    raise ValueError(SUBTASK_ASSIGNEE_REQUIRED_ERROR)
                                subtask_dict[ASSIGNEE_IDS_FIELD] = subtask_data.assignee_ids
                            else:
                                continue
                        else:
                            if len(subtask_data.assignee_ids) == 0:
                                raise ValueError(SUBTASK_ASSIGNEE_REQUIRED_ERROR)
                            subtask_dict[ASSIGNEE_IDS_FIELD] = subtask_data.assignee_ids

                if subtask_data.is_archived is not None:
                    subtask_dict[IS_ARCHIVED_FIELD] = subtask_data.is_archived
                if hasattr(subtask_data, 'file_url') and subtask_data.file_url is not None:
                    subtask_dict[FILE_URL_FIELD] = subtask_data.file_url
                if subtask_data.recurrence_rule is not None:
                    subtask_dict["recurrence_rule"] = subtask_data.recurrence_rule.value
                if subtask_data.recurrence_interval is not None:
                    subtask_dict["recurrence_interval"] = subtask_data.recurrence_interval
                if subtask_data.recurrence_end_date is not None:
                    subtask_dict["recurrence_end_date"] = subtask_data.recurrence_end_date.isoformat()

                if not subtask_dict:
                    continue

                results = self.crud.update(
                    self.table_name,
                    subtask_dict,
                    {TASK_ID_FIELD: subtask_id, PARENT_ID_FIELD: main_task_id}
                )
                if results:
                    result[UPDATED_SUBTASKS_RESPONSE_KEY].append(results[0] if isinstance(results, list) else results)

        if new_subtasks:
            for new_subtask in new_subtasks:
                subtask_dict = {
                    TITLE_FIELD: new_subtask.title,
                    DESCRIPTION_FIELD: new_subtask.description,
                    DUE_DATE_FIELD: new_subtask.due_date.isoformat(),
                    STATUS_FIELD: new_subtask.status.value,
                    PRIORITY_FIELD: new_subtask.priority,
                    ASSIGNEE_IDS_FIELD: new_subtask.assignee_ids or [],
                    PARENT_ID_FIELD: main_task_id,
                    OWNER_USER_ID_FIELD: user_id,
                    IS_ARCHIVED_FIELD: DEFAULT_IS_ARCHIVED
                }
                if hasattr(new_subtask, 'file_url') and new_subtask.file_url:
                    subtask_dict[FILE_URL_FIELD] = new_subtask.file_url
                results = self.crud.insert(self.table_name, subtask_dict)
                if results:
                    result[UPDATED_SUBTASKS_RESPONSE_KEY].append(results)

        return result
