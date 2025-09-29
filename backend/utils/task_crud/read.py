from typing import List, Dict, Any, Optional
from backend.wrappers.supabase_wrapper.supabase_crud import SupabaseCRUD
from backend.utils.user_crud.user_manager import UserManager


class TaskReader:
    """
    Task reading utilities with access control
    """

    def __init__(self):
        self.crud = SupabaseCRUD()
        self.user_manager = UserManager()
        self.table_name = "tasks"
        self.privileged_teams = ["sales manager", "finance managers"]  # Define privileged teams

    def get_tasks_for_user(self, user_id: str, user_role: str, user_teams: List[str], user_departments: List[str]) -> List[Dict[str, Any]]:
        """
        Get tasks based on user access control rules

        Access Control Rules:
        - Managing Director: Can view ALL tasks in ALL departments
        - Director: Can view all tasks in SAME department
        - Privileged Teams: Can view all tasks in SAME department
        - Regular Staff: Can only view tasks from their own team OR tasks they're assigned to

        Args:
            user_id: Current user's ID
            user_role: Current user's role (staff, manager, director, managing_director)
            user_teams: Current user's teams
            user_departmepytnts: Current user's departments

        Returns:
            List of tasks the user can access
        """

        # Managing Director: Can view ALL tasks
        if user_role == "managing_director":
            return self._get_all_tasks()

        # Director: Can view all tasks in same department
        if user_role == "director":
            return self._get_tasks_by_departments(user_departments)

        # Check if user is in privileged teams
        if self._is_privileged_team(user_teams):
            return self._get_tasks_by_departments(user_departments)

        # Regular staff: Own team tasks OR assigned tasks
        return self._get_tasks_for_regular_user(user_id, user_teams, user_departments)

    def _get_all_tasks(self) -> List[Dict[str, Any]]:
        """Get all tasks in the system (including archived)"""
        all_tasks = self.crud.select(self.table_name)
        return all_tasks

    def _get_tasks_by_departments(self, departments: List[str]) -> List[Dict[str, Any]]:
        """Get all tasks from users in the specified departments"""
        if not departments:
            return []

        # Get all users from these departments
        department_user_ids = set()
        for dept in departments:
            dept_users = self.user_manager.get_users_by_department(dept)
            for user in dept_users:
                department_user_ids.add(user["id"])

        if not department_user_ids:
            return []

        # Get all tasks owned by users in these departments (including archived)
        all_tasks = self.crud.select(self.table_name)
        return [task for task in all_tasks if task["owner_user_id"] in department_user_ids]

    def _get_tasks_for_regular_user(self, user_id: str, user_teams: List[str], user_departments: List[str]) -> List[Dict[str, Any]]:
        """Get tasks for regular users (own team + assigned tasks)"""
        if not user_teams:
            # If no teams, only get assigned tasks
            return self._get_assigned_tasks(user_id)

        # Get users from same teams
        team_user_ids = set()
        for team in user_teams:
            team_users = self.user_manager.get_users_by_team(team)
            for user in team_users:
                team_user_ids.add(user["id"])

        # Get all tasks (including archived)
        all_tasks = self.crud.select(self.table_name)

        accessible_tasks = []
        for task in all_tasks:
            # Can access if:
            # 1. Task is owned by someone in their team
            # 2. They are assigned to the task
            if (task["owner_user_id"] in team_user_ids or
                user_id in task.get("assignee_ids", [])):
                accessible_tasks.append(task)

        return accessible_tasks

    def _get_assigned_tasks(self, user_id: str) -> List[Dict[str, Any]]:
        """Get tasks assigned to the user (including archived)"""
        all_tasks = self.crud.select(self.table_name)
        return [task for task in all_tasks if user_id in task.get("assignee_ids", [])]

    def _is_privileged_team(self, user_teams: List[str]) -> bool:
        """Check if user is in any privileged teams"""
        return any(team in self.privileged_teams for team in user_teams)

    def get_task_by_id(self, task_id: str, user_id: str, user_role: str, user_teams: List[str], user_departments: List[str]) -> Optional[Dict[str, Any]]:
        """
        Get a specific task by ID if user has access

        Args:
            task_id: ID of the task to retrieve
            user_id: Current user's ID
            user_role: Current user's role
            user_teams: Current user's teams
            user_departments: Current user's departments

        Returns:
            Task data if accessible, None otherwise
        """
        accessible_tasks = self.get_tasks_for_user(user_id, user_role, user_teams, user_departments)

        for task in accessible_tasks:
            if task["id"] == task_id:
                return task

        return None

    def get_archived_subtasks_for_user(self, user_id: str, user_role: str, user_teams: List[str], user_departments: List[str]) -> List[Dict[str, Any]]:
        """
        Get archived subtasks with their main tasks based on user access control rules

        Returns:
            List of archived subtasks with their associated main tasks
        """
        # First get all accessible tasks (including archived ones)
        accessible_tasks = self._get_all_accessible_tasks(user_id, user_role, user_teams, user_departments)

        # Filter for archived subtasks and include their main tasks
        result = []
        main_task_cache = {}

        for task in accessible_tasks:
            # If it's an archived subtask (has parent_id and is_archived=True)
            if task.get("parent_id") is not None and task.get("is_archived", False):
                # Find the main task
                main_task_id = task["parent_id"]
                if main_task_id not in main_task_cache:
                    main_task = next((t for t in accessible_tasks if t["id"] == main_task_id), None)
                    main_task_cache[main_task_id] = main_task

                result.append({
                    "subtask": task,
                    "main_task": main_task_cache[main_task_id]
                })

        return result

    def _get_all_accessible_tasks(self, user_id: str, user_role: str, user_teams: List[str], user_departments: List[str]) -> List[Dict[str, Any]]:
        """Get all accessible tasks including archived ones (for internal use)"""
        # Managing Director: Can view ALL tasks
        if user_role == "managing_director":
            return self.crud.select(self.table_name)

        # Director: Can view all tasks in same department
        if user_role == "director":
            return self._get_all_tasks_by_departments(user_departments)

        # Check if user is in privileged teams
        if self._is_privileged_team(user_teams):
            return self._get_all_tasks_by_departments(user_departments)

        # Regular staff: Own team tasks OR assigned tasks
        return self._get_all_tasks_for_regular_user(user_id, user_teams, user_departments)

    def _get_all_tasks_by_departments(self, departments: List[str]) -> List[Dict[str, Any]]:
        """Get all tasks (including archived) from users in the specified departments"""
        if not departments:
            return []

        # Get all users from these departments
        department_user_ids = set()
        for dept in departments:
            dept_users = self.user_manager.get_users_by_department(dept)
            for user in dept_users:
                department_user_ids.add(user["id"])

        if not department_user_ids:
            return []

        # Get all tasks owned by users in these departments (including archived)
        all_tasks = self.crud.select(self.table_name)
        return [task for task in all_tasks if task["owner_user_id"] in department_user_ids]

    def _get_all_tasks_for_regular_user(self, user_id: str, user_teams: List[str], user_departments: List[str]) -> List[Dict[str, Any]]:
        """Get all tasks (including archived) for regular users (own team + assigned tasks)"""
        if not user_teams:
            # If no teams, only get assigned tasks
            return self._get_all_assigned_tasks(user_id)

        # Get users from same teams
        team_user_ids = set()
        for team in user_teams:
            team_users = self.user_manager.get_users_by_team(team)
            for user in team_users:
                team_user_ids.add(user["id"])

        # Get all tasks (including archived)
        all_tasks = self.crud.select(self.table_name)

        accessible_tasks = []
        for task in all_tasks:
            # Can access if:
            # 1. Task is owned by someone in their team
            # 2. They are assigned to the task
            if (task["owner_user_id"] in team_user_ids or
                user_id in task.get("assignee_ids", [])):
                accessible_tasks.append(task)

        return accessible_tasks

    def _get_all_assigned_tasks(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all tasks (including archived) assigned to the user"""
        all_tasks = self.crud.select(self.table_name)
        return [task for task in all_tasks if user_id in task.get("assignee_ids", [])]
