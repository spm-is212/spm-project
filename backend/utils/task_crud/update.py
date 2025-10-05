from typing import Dict, Any, Optional, List
from backend.wrappers.supabase_wrapper.supabase_crud import SupabaseCRUD
from backend.schemas.task import TaskUpdate, SubtaskCreate, MAIN_TASK_PARENT_ID
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
    TASK_ASSIGNEE_REQUIRED_ERROR,
    SUBTASK_ASSIGNEE_REQUIRED_ERROR,
    MAIN_TASK_RESPONSE_KEY,
    UPDATED_SUBTASKS_RESPONSE_KEY,
    OWNER_USER_ID_FIELD,
    DEFAULT_IS_ARCHIVED,
)


class TaskUpdater:
    """
    Task update utilities
    """

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


    def update_tasks(self, main_task_id: str, user_id: str, user_role: str, user_teams: list, main_task: Optional[TaskUpdate] = None, subtasks: Optional[Dict[str, TaskUpdate]] = None, new_subtasks: Optional[List[SubtaskCreate]] = None) -> Dict[str, Any]:
        """
        Update main task and/or subtasks

        Args:
            main_task_id: ID of the main task
            user_id: ID of the user updating the tasks
            user_role: Role of the user updating the tasks
            user_teams: Teams the user belongs to
            main_task: Optional main task update data
            subtasks: Optional dictionary of {subtask_id: TaskUpdate} for updates

        Returns:
            Dictionary containing updated main task and subtasks
        """
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
                        # else: staff removal → skip (don’t set assignee_ids at all)
                    else:
                        if len(main_task.assignee_ids) == 0:
                            raise ValueError(TASK_ASSIGNEE_REQUIRED_ERROR)
                        main_task_dict[ASSIGNEE_IDS_FIELD] = main_task.assignee_ids

                        
            if main_task.is_archived is not None:
                main_task_dict[IS_ARCHIVED_FIELD] = main_task.is_archived

            # ✅ recurrence for main task
            if main_task.recurrence_rule is not None:
                main_task_dict["recurrence_rule"] = main_task.recurrence_rule.value
            if main_task.recurrence_interval is not None:
                main_task_dict["recurrence_interval"] = main_task.recurrence_interval
            if main_task.recurrence_end_date is not None:
                main_task_dict["recurrence_end_date"] = main_task.recurrence_end_date.isoformat()

            if main_task_dict:
                # Add parent_id alongside other fields
                main_task_dict_with_parent = {**main_task_dict, PARENT_ID_FIELD: MAIN_TASK_PARENT_ID}
                results = self.crud.update(
                    self.table_name,
                    main_task_dict_with_parent,
                    {TASK_ID_FIELD: main_task_id}
                )
                if results:
                    if isinstance(results, list):
                        result[MAIN_TASK_RESPONSE_KEY] = results[0]
                    elif isinstance(results, dict):
                        result[MAIN_TASK_RESPONSE_KEY] = results
            else:
                # No meaningful fields provided → skip update
                result[MAIN_TASK_RESPONSE_KEY] = None
                
     # --- SUBTASKS UPDATE ---
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
                            if self.can_remove_assignees(user_role, user_teams):
                                if len(subtask_data.assignee_ids) == 0:
                                    raise ValueError(SUBTASK_ASSIGNEE_REQUIRED_ERROR)
                                subtask_dict[ASSIGNEE_IDS_FIELD] = subtask_data.assignee_ids
                            # else: staff removal → skip (don’t set assignee_ids at all)
                        else:
                            if len(subtask_data.assignee_ids) == 0:
                                raise ValueError(SUBTASK_ASSIGNEE_REQUIRED_ERROR)
                            subtask_dict[ASSIGNEE_IDS_FIELD] = subtask_data.assignee_ids

                if subtask_data.is_archived is not None:
                    subtask_dict[IS_ARCHIVED_FIELD] = subtask_data.is_archived

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
                        {TASK_ID_FIELD: subtask_id, PARENT_ID_FIELD: main_task_id}
                    )
                    if results:
                        if isinstance(results, list):
                            result[UPDATED_SUBTASKS_RESPONSE_KEY].append(results[0])
                        elif isinstance(results, dict):
                            result[UPDATED_SUBTASKS_RESPONSE_KEY].append(results)

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

                results = self.crud.insert(self.table_name, subtask_dict)
                if results:
                    result[UPDATED_SUBTASKS_RESPONSE_KEY].append(results)

        return result
