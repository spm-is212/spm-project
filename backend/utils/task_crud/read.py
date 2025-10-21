from typing import List, Dict, Any, Optional
from backend.wrappers.supabase_wrapper.supabase_crud import SupabaseCRUD
from backend.utils.user_crud.user_manager import UserManager
from backend.utils.task_crud.constants import (
    TASKS_TABLE_NAME,
    ADMIN_ROLE,
    OWNER_USER_ID_FIELD,
    ASSIGNEE_IDS_FIELD,
    PARENT_ID_FIELD,
    IS_ARCHIVED_FIELD,
    TASK_ID_FIELD,
    USER_ID_FIELD,
    SUBTASK_KEY,
    MAIN_TASK_KEY
)


class TaskReader:
    """
    Task reading utilities with role-based access control.

    Provides methods to retrieve tasks based on user permissions and organizational hierarchy.
    Access control follows a hierarchical model where higher roles have broader access.
    """

    def __init__(self):
        self.crud = SupabaseCRUD()
        self.user_manager = UserManager()
        self.table_name = TASKS_TABLE_NAME

    def get_tasks_for_user(self, user_id: str, user_role: str, user_departments: List[str]) -> List[Dict[str, Any]]:
        """
        Retrieve tasks based on hierarchical access control rules.

        Access Control Hierarchy (3-tier):
        - Admin: All tasks across all departments
        - Manager: All tasks they are assigned to (can modify assignees)
        - Staff: Only tasks where they are assigned

        Args:
            user_id: Unique identifier of the requesting user
            user_role: User's organizational role (admin, manager, staff)
            user_departments: List of departments the user belongs to

        Returns:
            List of task dictionaries the user is authorized to access
        """
        return self._apply_access_control(user_id, user_role, user_departments, include_archived=False)

    def get_task_by_id(self, task_id: str, user_id: str, user_role: str, user_departments: List[str]) -> Optional[Dict[str, Any]]:
        """
        Get a specific task by ID if user has access.

        Args:
            task_id: ID of the task to retrieve
            user_id: Current user's ID
            user_role: Current user's role
            user_departments: Current user's departments

        Returns:
            Task data if accessible, None otherwise
        """
        accessible_tasks = self.get_tasks_for_user(user_id, user_role, user_departments)

        for task in accessible_tasks:
            if task[TASK_ID_FIELD] == task_id:
                return task

        return None

    def get_archived_subtasks_for_user(self, user_id: str, user_role: str, user_departments: List[str]) -> List[Dict[str, Any]]:
        """
        Retrieve archived subtasks with their associated main tasks.

        Applies the same access control rules as regular task retrieval,
        then filters for archived subtasks and includes their parent tasks.

        Args:
            user_id: ID of the requesting user
            user_role: User's organizational role
            user_departments: List of departments the user belongs to

        Returns:
            List of dictionaries containing 'subtask' and 'main_task' keys
        """
        accessible_tasks = self._get_all_accessible_tasks(user_id, user_role, user_departments)

        result = []
        main_task_cache = {}

        for task in accessible_tasks:
            if task.get(PARENT_ID_FIELD) is not None and task.get(IS_ARCHIVED_FIELD, False):
                main_task_id = task[PARENT_ID_FIELD]
                if main_task_id not in main_task_cache:
                    main_task = next((t for t in accessible_tasks if t[TASK_ID_FIELD] == main_task_id), None)
                    main_task_cache[main_task_id] = main_task

                result.append({
                    SUBTASK_KEY: task,
                    MAIN_TASK_KEY: main_task_cache[main_task_id]
                })

        return result


    def _apply_access_control(self, user_id: str, user_role: str, user_departments: List[str], include_archived: bool = False) -> List[Dict[str, Any]]:
        """
        Apply hierarchical access control rules to retrieve tasks.

        Centralized access control logic used by both regular and archived task retrieval.

        Access control is now based purely on:
        - Role hierarchy (no more privileged teams check)
        - Project collaboration
        - Task assignment

        Args:
            user_id: ID of the requesting user
            user_role: User's organizational role
            user_departments: List of departments the user belongs to
            include_archived: Whether to include archived tasks

        Returns:
            List of tasks the user is authorized to access
        """
        if user_role.lower() in [ADMIN_ROLE, "managing_director"]:
            return self._get_all_tasks()
        elif user_role.lower() == "director":
            return self._filter_tasks_by_departments(user_departments, include_archived)
        # Manager and staff see only their assigned tasks
        # (Managers have additional privileges for updating, but same read access)
        return self._filter_tasks_by_assignment(user_id, include_archived)

    def _get_all_accessible_tasks(self, user_id: str, user_role: str, user_departments: List[str]) -> List[Dict[str, Any]]:
        """
        Internal method to get all accessible tasks including archived ones.

        Applies the same hierarchical access control as get_tasks_for_user
        but includes archived tasks for specialized operations.

        Args:
            user_id: ID of the requesting user
            user_role: User's organizational role
            user_departments: List of departments the user belongs to

        Returns:
            List of all accessible tasks including archived ones
        """
        return self._apply_access_control(user_id, user_role, user_departments, include_archived=True)


    def _get_all_tasks(self) -> List[Dict[str, Any]]:
        """
        Retrieve all tasks in the system without filtering.

        Used for managing directors who have unrestricted access.
        Includes both active and archived tasks.

        Returns:
            Complete list of all tasks in the system
        """
        return self.crud.select(self.table_name)

    def _get_tasks_by_departments(self, departments: List[str]) -> List[Dict[str, Any]]:
        """
        Retrieve all tasks owned by users within specified departments.

        Used for directors and privileged teams who have department-wide access.
        Tasks are filtered by owner's department membership.

        Args:
            departments: List of department names to include

        Returns:
            List of tasks owned by users in the specified departments
        """
        return self._filter_tasks_by_departments(departments, include_archived=False)

    def _get_all_tasks_by_departments(self, departments: List[str]) -> List[Dict[str, Any]]:
        """
        Retrieve all tasks including archived ones from specified departments.

        Similar to _get_tasks_by_departments but includes archived tasks.
        Used internally for operations that need complete task visibility.

        Args:
            departments: List of department names to include

        Returns:
            List of all tasks (including archived) owned by users in departments
        """
        return self._filter_tasks_by_departments(departments, include_archived=True)

    def _get_tasks_for_regular_user(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve tasks for regular users and managers based on assignment.

        Regular users and managers can only see tasks where they are explicitly assigned.

        Args:
            user_id: ID of the user requesting tasks

        Returns:
            List of tasks where the user is assigned
        """
        return self._filter_tasks_by_assignment(user_id, include_archived=False)

    def _get_all_tasks_for_regular_user(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all tasks including archived ones for regular users.

        Regular users and managers can only access tasks where they are assigned.
        This includes both active and archived assigned tasks.

        Args:
            user_id: ID of the user requesting tasks

        Returns:
            List of all assigned tasks including archived ones
        """
        return self._filter_tasks_by_assignment(user_id, include_archived=True)

    def _get_assigned_tasks(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve tasks where the user is explicitly assigned.

        Filters all tasks to only include those where the user ID appears
        in the assignee_ids array. Includes both active and archived tasks.

        Args:
            user_id: ID of the user to find assignments for

        Returns:
            List of tasks where the user is assigned
        """
        return self._filter_tasks_by_assignment(user_id, include_archived=False)

    def _get_all_assigned_tasks(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all assigned tasks including archived ones.

        Comprehensive version of _get_assigned_tasks that includes
        archived tasks for complete assignment history.

        Args:
            user_id: ID of the user to find assignments for

        Returns:
            List of all tasks (including archived) where user is assigned
        """
        return self._filter_tasks_by_assignment(user_id, include_archived=True)



    def _get_department_user_ids(self, departments: List[str]) -> set:
        """
        Retrieve user IDs for all users within specified departments.

        Args:
            departments: List of department names

        Returns:
            Set of user IDs belonging to the specified departments
        """
        if not departments:
            return set()

        department_user_ids = set()
        for dept in departments:
            dept_users = self.user_manager.get_users_by_department(dept)
            for user in dept_users:
                department_user_ids.add(user[USER_ID_FIELD])

        return department_user_ids


    def _filter_tasks_by_departments(self, departments: List[str], include_archived: bool = False) -> List[Dict[str, Any]]:
        """
        Filter tasks by department ownership.

        Args:
            departments: List of department names to include
            include_archived: Whether to include archived tasks

        Returns:
            List of tasks owned by users in the specified departments
        """
        department_user_ids = self._get_department_user_ids(departments)
        if not department_user_ids:
            return []

        all_tasks = self.crud.select(self.table_name)
        return [task for task in all_tasks if task[OWNER_USER_ID_FIELD] in department_user_ids]

    def _filter_tasks_by_assignment(self, user_id: str, include_archived: bool = False) -> List[Dict[str, Any]]:
        """
        Filter tasks by user assignment.

        Args:
            user_id: ID of the user to find assignments for
            include_archived: Whether to include archived tasks

        Returns:
            List of tasks where the user is assigned (including tasks where user is assigned to subtasks)
        """
        all_tasks = self.crud.select(self.table_name)

        # Build a map of parent task IDs for quick lookup
        parent_task_ids = set()
        for task in all_tasks:
            if user_id in task.get(ASSIGNEE_IDS_FIELD, []):
                # If user is assigned to this task
                if task.get(PARENT_ID_FIELD) is not None:
                    # It's a subtask, include the parent task
                    parent_task_ids.add(task[PARENT_ID_FIELD])

        # Return tasks where user is directly assigned OR user is assigned to any of its subtasks
        return [task for task in all_tasks if
                user_id in task.get(ASSIGNEE_IDS_FIELD, []) or
                task.get(TASK_ID_FIELD) in parent_task_ids]
