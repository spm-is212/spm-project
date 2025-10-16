"""
Role-Based Access Control (RBAC) Helper

This module provides centralized access control logic for the system.
After removing the teams abstraction, RBAC is based on:
- User roles (admin, manager, staff) - 3-tier hierarchy
- Project collaboration (collaborator_ids)
- Task assignment (assignee_ids)
- Department membership
"""

from typing import List, Dict, Any
from backend.wrappers.supabase_wrapper.supabase_crud import SupabaseCRUD

# Role constants - 3-tier role system
ADMIN_ROLE = "admin"
MANAGER_ROLE = "manager"
STAFF_ROLE = "staff"

# Privileged roles that can remove assignees and have broader access
PRIVILEGED_ROLES = [ADMIN_ROLE, MANAGER_ROLE]
ASSIGNEE_REMOVAL_ROLES = [ADMIN_ROLE, MANAGER_ROLE]


class RBACHelper:
    """
    Centralized Role-Based Access Control helper

    Provides methods to check user permissions based on:
    - Role hierarchy (admin > manager > staff)
    - Project collaboration
    - Department membership
    """

    def __init__(self):
        self.crud = SupabaseCRUD()

    def is_admin(self, user_role: str) -> bool:
        """Check if user is an admin (highest access level)"""
        return user_role.lower() == ADMIN_ROLE

    def is_manager(self, user_role: str) -> bool:
        """Check if user is a manager"""
        return user_role.lower() == MANAGER_ROLE

    def is_staff(self, user_role: str) -> bool:
        """Check if user is regular staff"""
        return user_role.lower() == STAFF_ROLE

    def has_privileged_role(self, user_role: str) -> bool:
        """
        Check if user has a privileged role (admin or manager).
        Privileged users can:
        - Remove task assignees
        - See broader scope of tasks
        - Update more fields
        """
        return user_role.lower() in PRIVILEGED_ROLES

    def can_remove_assignees(self, user_role: str) -> bool:
        """
        Check if user can remove assignees from tasks.

        Now purely role-based: admin or manager.

        Args:
            user_role: User's role

        Returns:
            True if user can remove assignees
        """
        return user_role.lower() in ASSIGNEE_REMOVAL_ROLES

    def get_user_project_ids(self, user_id: str) -> List[str]:
        """
        Get all project IDs where user is a collaborator.

        Args:
            user_id: User's UUID

        Returns:
            List of project IDs where user is a collaborator
        """
        try:
            projects = self.crud.client.table("projects").select("id, collaborator_ids").execute()

            user_project_ids = []
            for project in projects.data:
                if user_id in project.get("collaborator_ids", []):
                    user_project_ids.append(project["id"])

            return user_project_ids
        except Exception as e:
            print(f"Error getting user projects: {e}")
            return []

    def get_user_projects(self, user_id: str, user_role: str) -> List[Dict[str, Any]]:
        """
        Get all projects accessible to the user based on role and collaboration.

        Args:
            user_id: User's UUID
            user_role: User's role

        Returns:
            List of project dictionaries
        """
        try:
            projects = self.crud.client.table("projects").select("*").execute()

            # Admins see all projects
            if self.is_admin(user_role):
                return projects.data

            # Managers and staff: only projects where they are collaborators
            return [p for p in projects.data if user_id in p.get("collaborator_ids", [])]

        except Exception as e:
            print(f"Error getting user projects: {e}")
            return []

    def can_access_project(self, user_id: str, user_role: str, project_id: str) -> bool:
        """
        Check if user can access a specific project.

        Args:
            user_id: User's UUID
            user_role: User's role
            project_id: Project UUID

        Returns:
            True if user can access the project
        """
        try:
            # Admins can access all projects
            if self.is_admin(user_role):
                return True

            # Get the project
            project = self.crud.client.table("projects").select("*").eq("id", project_id).execute()
            if not project.data:
                return False

            project_data = project.data[0]

            # Check if user is a collaborator (applies to managers and staff)
            if user_id in project_data.get("collaborator_ids", []):
                return True

            return False

        except Exception as e:
            print(f"Error checking project access: {e}")
            return False

    def _get_department_user_ids(self, departments: List[str]) -> set:
        """
        Get all user IDs for users in the specified departments.

        Args:
            departments: List of department names

        Returns:
            Set of user UUIDs
        """
        if not departments:
            return set()

        try:
            users = self.crud.client.table("users").select("uuid, departments").execute()
            dept_user_ids = set()

            for user in users.data:
                user_depts = user.get("departments", [])
                if any(dept in departments for dept in user_depts):
                    dept_user_ids.add(user["uuid"])

            return dept_user_ids
        except Exception as e:
            print(f"Error getting department users: {e}")
            return set()
